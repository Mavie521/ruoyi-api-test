# 性能监控三件套 — 部署指南（InfluxDB + Grafana + Prometheus）

> 配套 `perf/README.md` 的「JMeter 指标大盘」升级版，把原计划的「理论两套监控体系」落成实操。
> 与被测若依栈（根目录 `docker-compose.yml`）**隔离**，独立启停，互不影响。

---

## 0. 架构

```
[Windows 压测机]                              [VM 被测机 192.168.149.100]
  JMeter 5.6                                   若依后端 :8080（被测）
  └─ Backend Listener ──HTTP压测────────────▶ │
  └─ 写指标 ──TCP:8086───────────────────────▶ InfluxDB (8086)
                                                │
  浏览器看大盘 ──http://192.168.149.100:3000─▶ Grafana (3000) ──读──▶ InfluxDB
                                                │                  └─读──▶ Prometheus (9090)
                                                └─ Prometheus ──抓──▶ Node Exporter (9100) ──采──▶ 宿主CPU/内存/磁盘
```

---

## 1. 端口清单（全部避开若依已占用端口）

| 组件 | 端口 | 用途 |
|------|------|------|
| InfluxDB | 8086 | JMeter 写压测指标 |
| Grafana | 3000 | 大盘 Web 界面（admin / admin） |
| Prometheus | 9090 | Prometheus Web UI（学习用） |
| Node Exporter | 9100 | 暴露宿主资源指标给 Prometheus |

> 若依已占用：80 / 8080 / 8088 / 3307 / 6379（Jenkins 8081 在 VM 上但不在本 compose 内），无冲突。

---

## 2. 部署步骤（在 VM 上）

前置：VM 内存已从 2GB 升到 4GB（VMware 编辑虚拟机设置 → 内存 → 4096MB → 开机）。

```bash
# ① Windows 端提交并推送（本目录 3 个文件）
git add perf/monitoring && git commit -m "perf: 监控三件套 InfluxDB+Grafana+Prometheus compose" && git push

# ② VM 拉取
ssh yy@192.168.149.100
cd ~/ruoyi-api-test && git pull

# ③ 启动监控栈（首次会拉镜像，国内慢的话先配镜像加速源）
cd ~/ruoyi-api-test/perf/monitoring
docker compose up -d

# ④ 验证四个容器都 Up
docker compose ps
```

> 镜像国内拉不动时：`sudo mkdir -p /etc/docker && sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'`
> ```json
> { "registry-mirrors": ["https://docker.m.daocloud.io", "https://dockerproxy.com"] }
> ```
> EOF
> 然后 `sudo systemctl restart docker` 再 `docker compose up -d`。

---

## 3. JMeter 接 InfluxDB（压测机 Windows 上配置）

给压测线程组加 **Backend Listener**（右键线程组 → Add → Listener → Backend Listener），
「Backend Listener implementation」选 **`InfluxDBBackendListenerClient`**，参数填：

| 参数 | 值 |
|------|-----|
| `influxdbUrl` | `http://192.168.149.100:8086/write?db=jmeter` |
| `application` | `ruoyi` |
| `measurement` | `jmeter` |
| `summaryOnly` | `false` |
| `samplersRegex` | `.*` |
| `percentiles` | `90;95;99` |
| `testTitle` | `ruoyi-perf` |

然后正常跑压测，指标就实时写进 InfluxDB 了。

---

## 4. Grafana 配置（浏览器打开 http://192.168.149.100:3000，admin/admin）

**① 加两个数据源**（Settings → Data sources → Add data source）：

| 数据源类型 | URL | 其它 |
|-----------|-----|------|
| InfluxDB | `http://influxdb:8086` | Database 填 `jmeter`，无账号密码 |
| Prometheus | `http://prometheus:9090` | 默认即可 |

**② 导入现成 dashboard**（Dashboards → New → Import，填 ID）：

| Dashboard ID | 名称 | 对应数据源 |
|--------------|------|-----------|
| `5496` | JMeter Dashboard（Novatec） | InfluxDB |
| `1860` | Node Exporter Full | Prometheus |

> 压测时 JMeter 大盘（5496）实时显示 TPS / 响应时间 / 错误率曲线；Node Exporter 大盘（1860）显示服务端 CPU / 内存 / 磁盘。

---

## 5. 验证与排查

```bash
# 数据源连通性（VM 上）
curl -s http://localhost:8086/query?q=show+databases | head -c 200     # 应看到 jmeter
curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"up"' # 应看到 up
curl -s http://localhost:9100/metrics | head -3                        # 应看到 node_ 指标

# JMeter 跑完后确认数据进库
curl -s 'http://localhost:8086/query?q=SELECT+*+FROM+jmeter+LIMIT+1' | head -c 300
```

| 问题 | 原因 | 解决 |
|------|------|------|
| 镜像拉不动 | 国内网络 | 配 daemon.json 镜像加速源（见第 2 节） |
| 5496 大盘无数据 | 数据源指向错 / db 名错 | 确认 InfluxDB 数据源 URL `http://influxdb:8086`、Database `jmeter` |
| Prometheus target 红色 | node-exporter 没起 | `docker compose ps` 看 monitor-node-exporter 状态 |
| JMeter 写不进 | 8086 端口没放通 / Backend Listener 没加 | VM `ss -lntp \| grep 8086`，确认压测机能 `telnet 192.168.149.100 8086` |

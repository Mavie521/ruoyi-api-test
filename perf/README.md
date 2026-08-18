# 若依系统性能测试 — 实战落地指南（JMeter + PerfMon + ServerAgent）

> 对应文档：`若依系统 - 性能测试计划.docx`
> 交付物：一套可复用 JMeter 脚本 + ServerAgent 资源监控（见第 3 节）+ 本指南

---

## 0. 交付物清单

| 文件 | 作用 |
|------|------|
| `perf/jmeter/ruoyi-perf-test.jmx` | JMeter 主脚本（参数化线程组，一套适配基准/负载/压力三场景） |
| `perf/README.md` | 本指南 |

---

## 1. 环境拓扑（先搞清楚谁压谁）

```
[压测机 = 你的 Windows 本机]                    [被测服务器 = Linux VM]
   JMeter 5.6 + PerfMon 插件  ──HTTP 压测──▶   若依后端 :8080 (ry-api)
        │                                       │
        │                                       └─ ServerAgent :4444（采本机资源）
        └── PerfMon 监听器 ──TCP:4444── 读取 CPU/内存 ──┘
```

- **被测接口**（3 个，全是只读查询，无脏数据）：
  - `POST /login` — 登录拿 token（前置）
  - `GET /system/user/list?pageNum=1&pageSize=10` — 用户列表分页查询
  - `GET /system/role/list?pageNum=1&pageSize=10` — 角色列表查询
- **目标地址**：`http://192.168.149.100:8080`（脚本里已配好，可用 `-JHOST=` 覆盖）
- **账号**：`admin` / `admin123`（脚本 `用户定义的变量` 里，可改）

---

## 2. 安装 JMeter 与插件（压测机，一次性）

### 2.1 装 JMeter

1. 下载 [Apache JMeter 5.6.3](https://jmeter.apache.org/download_jmeter.cgi)（zip 免安装版）
2. 解压到如 `D:\jmeter`
3. 校验 Java：`java -version`（需 JDK 8+，建议 11/17）

### 2.2 装 Plugins Manager + PerfMon 插件

1. 下载 `jmeter-plugins-manager.jar`，放入 `D:\jmeter\lib\ext\`
2. 重启 JMeter（双击 `D:\jmeter\bin\jmeter.bat`）
3. 菜单 `Options → Plugins Manager`
4. **Available Plugins** 里勾选：
   - `PerfMon (Servers Performance Monitoring)` ← 必须
5. 点 `Apply Changes and Restart JMeter`

> 装完 PerfMon 后，右键任意元素 → Add → Listener 里应出现 **`jp@gc - PerfMon Metrics Collector`**。

---

## 3. 部署 ServerAgent（被测服务器 VM）

ServerAgent 是被测服务器上的资源采集代理，必须跑在若依所在的 VM 上（不是压测机）。

**部署**（VM 上需有 Java）：下载 [ServerAgent 2.2.3](https://github.com/undera/perfmon-agent/releases/tag/2.2.3)，解压到 `~/serveragent`，用 systemd 配置为开机自启（推荐）：

```bash
sudo tee /etc/systemd/system/serveragent.service >/dev/null <<'EOF'
[Unit]
Description=JMeter PerfMon ServerAgent
After=network-online.target

[Service]
User=yy
WorkingDirectory=/home/yy/serveragent
ExecStart=/bin/bash /home/yy/serveragent/startAgent.sh --udp-port 0 --tcp-port 4444
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now serveragent
```

> 不想配自启时，手动后台启动：`cd ~/serveragent && nohup ./startAgent.sh --udp-port 0 --tcp-port 4444 >/tmp/serveragent.log 2>&1 &`

**验证：**

```bash
ss -lntp | grep 4444      # 应看到 LISTEN 4444
```

**防火墙**（如果压测机连不上 4444）：

```bash
sudo firewall-cmd --add-port=4444/tcp --permanent && sudo firewall-cmd --reload
```

---

## 4. 打开脚本并做单线程调试（准入标准，必做）

1. JMeter 里 `File → Open` 打开 `perf/jmeter/ruoyi-perf-test.jmx`
2. 先确认脚本结构（从上到下）：
   ```
   Test Plan
   ├── HTTP请求默认值（协议/IP/端口统一，切环境只改这里）
   ├── 压测线程组（真实业务压测）
   │   ├── 鉴权头 Authorization（线程组级，子接口自动继承）
   │   ├── 登录前置（Once Only Controller）
   │   │     └── POST /login → JSON提取器(token) → 断言
   │   ├── 业务接口（Random Controller，随机执行）
   │   │     ├── GET /system/user/list → 断言
   │   │     └── GET /system/role/list → 断言
   │   └── 思考时间（随机1-3s，-JthinkTimeEnable 开关）
   └── 集合点秒杀场景（默认禁用）
   ```
3. **单线程调试**：线程组里把「线程数」临时改成 `1`、勾掉「循环 forever」设循环 `1`
4. 点绿色 ▶ 运行，看「查看结果树」（右键线程组 → Add → Listener → View Results Tree）
5. **通过标准**：登录返回 200 且有 token，两个业务接口都返回 200 且响应体含 `"code":200`

> ⚠️ 这一步是计划的「准入标准」——脚本没单线程跑通之前，绝对不要开并发压测，否则测出来的全是脚本错误。

---

## 5. PerfMon 资源监控（已内置脚本，只需启动 ServerAgent）

PerfMon 监听器已经内置在脚本里（`jp@gc - PerfMon Metrics Collector`），采集 `192.168.149.100:4444` 的 CPU / 内存 / 磁盘IO / 网络。

你只需要：

1. **被测服务器 VM 上**已部署 ServerAgent 并监听 4444（见第 3 节）
2. 打开脚本，展开「jp@gc - PerfMon Metrics Collector」，确认服务器 IP 和端口对得上
3. 压测时它自动实时画资源曲线

> 如果脚本里没显示 PerfMon 监听器，说明 PerfMon 插件没装（回第 2.2 节装插件）。装好插件再重新打开脚本即可。

---

## 6. 三场景执行

### 方式 A：GUI 改参数（最直观，适合刚开始）

每次在「压测线程组」里改两个数，点 ▶：

| 场景 | 线程数 | 循环/时长 | 目的 |
|------|--------|-----------|------|
| 基准测试 | 5 | 循环 1 次 | 建立轻载基线 |
| 负载测试 | 20 | 勾「forever」+ 时长 300s | 验日常负载稳定性 |
| 压力测试 | 20→30→40→50 | 每档 forever + 180s | 探测性能拐点 |

### 方式 B：命令行 `-J` 参数（一套脚本复用，面试加分）

```bash
# 进入 JMeter bin 目录
cd D:\jmeter\bin

# ① 基准测试（5 并发，单循环）
jmeter -n -t ..\..\Code\claude_test01\ruoyi_api_test\perf\jmeter\ruoyi-perf-test.jmx ^
  -Jusers=5 -Jforever=false -Jloops=1 -Jscheduler=false -Jduration=0 ^
  -l reports\perf\baseline.jtl

# ② 负载测试（20 并发，5 分钟，开思考时间=模拟真实用户）
jmeter -n -t ..\..\Code\claude_test01\ruoyi_api_test\perf\jmeter\ruoyi-perf-test.jmx ^
  -Jusers=20 -Jforever=true -Jscheduler=true -Jduration=300 ^
  -JthinkTimeEnable=true ^
  -l reports\perf\load.jtl

# ③ 压力测试（梯度加压：20/30/40/50，每档 3 分钟，关思考时间=压榨极限）
for %u in (20 30 40 50) do jmeter -n -t ..\..\Code\claude_test01\ruoyi_api_test\perf\jmeter\ruoyi-perf-test.jmx ^
  -Jusers=%u -Jforever=true -Jscheduler=true -Jduration=180 ^
  -JthinkTimeEnable=false ^
  -l reports\perf\stress-%u.jtl
```

> 参数含义：`users` 并发数、`ramp` 加压时间、`forever` 是否无限循环、`duration` 持续秒数、`scheduler` 是否启用定时、`thinkTimeEnable` 思考时间开关（true=模拟真实用户 1-3s 停顿，false=压榨系统极限）。命令行 `^` 是 Windows 续行符，Git Bash 下用 `\`。

### 集合点秒杀场景（请求级并发，进阶）

上面三种都是「用户级并发」。这是「请求级并发」——所有线程在**集合点排队，攒齐后同一瞬间打接口**，模拟秒杀/抢购。

**启用步骤：**

1. 找到「集合点秒杀场景（请求级并发，默认禁用）」线程组，**右键 → Enabled**
2. 跑一次：`-Jusers=50 -Jloops=1`
3. 看聚合报告——50 个请求会在同一时间点爆发，而不是分散在 1 秒里

**集合点参数（Synchronizing Timer）：**

| 参数 | 值 | 含义 |
|------|-----|------|
| groupSize | 0 | 攒齐所有线程才放行（秒杀用这个） |
| groupSize | N | 每攒 N 个放一批 |
| timeoutInMs | 5000 | 5 秒超时兜底，凑不齐也放行（防卡死） |

> 面试话术：`ramp-up=0 只是快速创建虚拟用户；真正的请求级同一时刻并发，必须搭配集合点定时器 Synchronizing Timer`。

---

## 7. 结果收集与验收对照

### 7.1 收集三类数据

| 数据 | 来源 | 说明 |
|------|------|------|
| TPS / RT / 错误率 | 聚合报告、汇总报告、`.jtl` 文件 | 客户端压测指标 |
| CPU / 内存曲线 | PerfMon 监听器 + `perf-result-perfmon.csv` | 服务端资源指标 |
| 拐点/瓶颈 | 对比各梯度数据 | 分析结论 |

### 7.2 验收指标对照（计划 6.1）

| 指标 | 验收标准 | 记录 |
|------|---------|------|
| 平均响应时间 | ≤ 300ms | |
| 95% 响应时间 | ≤ 500ms | |
| 单接口稳定 TPS | ≥ 30 | |
| 错误率 | = 0% | |
| CPU 使用率 | ≤ 75% | |
| 内存占用 | ≤ 80% | |

> 跑完三场景后，把每档的 TPS/RT/错误率/CPU/内存填进上表，对比验收标准，找出「性能拐点」和「瓶颈接口」——这就是报告结论。

---

## 8. 面试口述要点（30 秒版）

> 我在若依项目完整落地了性能测试：用 JMeter 写了带动态 token 关联 + 双断言（HTTP 200 + 业务 code 200）的压测脚本，一套脚本适配基准/负载/压力三场景。实战用 jp@gc-PerfMon + ServerAgent 采集服务器 CPU、内存资源；理论掌握企业两套监控体系——InfluxDB+Grafana 收 JMeter 压测指标、Prometheus+Grafana 做服务端 JVM/中间件全栈监控。通过梯度加压定位到系统性能拐点和瓶颈接口。

---

## 9. 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| PerfMon 监听器无曲线 | ServerAgent 没起 / 端口不通 | VM 上 `systemctl status serveragent`，检查 4444 端口和防火墙 |
| 脚本加载报错 | 缺 PerfMon 插件 | 装完插件再打开脚本 |
| 业务接口 401 | token 没提取到 | 单线程看结果树，确认登录返回了 `token` 字段 |
| 全 405 | 地址/端口错 | 确认 `HOST=192.168.149.100`、`PORT=8080` |

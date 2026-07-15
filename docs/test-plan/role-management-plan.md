# RuoYi 角色管理模块 — 测试计划

## 1. 概述

| 项目 | 内容 |
|------|------|
| 被测系统 | RuoYi-Vue v3.9.2 |
| 测试模块 | 角色管理（SysRoleController） |
| 测试类型 | 接口自动化 + 安全测试 |
| 测试环境 | Docker（MySQL 8.0 + Redis 7 + RuoYi Backend） |
| 测试工具 | Pytest / Requests / Allure / Locust |
| CI/CD | Jenkins Pipeline + 钉钉通知 |

## 2. 测试范围

### 2.1 覆盖功能点

| 功能 | 接口 | 优先级 |
|------|------|--------|
| 角色列表查询 | GET /system/role/list | P0 |
| 角色详情查询 | GET /system/role/{id} | P0 |
| 新增角色 | POST /system/role | P0 |
| 编辑角色 | PUT /system/role | P0 |
| 删除角色 | DELETE /system/role/{ids} | P0 |
| 角色状态变更 | PUT /system/role/changeStatus | P1 |
| 角色下拉选项 | GET /system/role/optionselect | P2 |
| 部门树 | GET /system/role/deptTree/{id} | P2 |
| 已分配用户列表 | GET /system/role/authUser/allocatedList | P2 |
| 未分配用户列表 | GET /system/role/authUser/unallocatedList | P2 |
| SQL注入 | POST /login（注入payload） | P1 |
| XSS注入 | POST /system/role(含脚本标签) | P1 |

### 2.2 不覆盖范围

- 前端页面交互（纯接口测试）
- 性能压测（后续迭代补充）

## 3. 测试策略

### 3.1 接口测试策略

| 维度 | 方法 |
|------|------|
| 正向流程 | HTTP 200 + code=200 + 响应结构 + DB落盘 |
| 异常参数 | 缺字段/类型错/超长/空值 |
| 权限验证 | 无Token/伪造Token/越权 |
| 数据状态 | 重复创建/不存在操作/已删除操作 |
| 幂等性 | 重复请求结果一致 |

### 3.2 断言策略

- **维度一：API 响应断言** — status_code、code、msg、success 字段
- **维度二：数据库落盘断言** — assert_value / assert_exists / assert_not_exists

### 3.3 环境策略

| 模式 | 操作 | 耗时 | 场景 |
|------|------|------|------|
| fast | docker compose down + up | ~20s | 日常回归 |
| clean | docker compose down -v + up | ~60s | 怀疑脏数据时 |

## 4. 测试数据

| 数据 | 生成方式 | 清理方式 |
|------|---------|---------|
| 角色名 | `测试角色_` + 时间戳后缀 | fixture finalizer DELETE |
| 角色Key | `test_role_` + 时间戳后缀 | fixture finalizer DELETE |
| 菜单Ids | 空列表 `[]` | — |

## 5. 风险与应对

| 风险 | 概率 | 应对 |
|------|------|------|
| 容器网络延迟导致超时 | 高 | `wait_for_api.sh` POST 验证 token（40次×5s=200s超时） |
| 数据库脏数据 | 中 | fast/clean 双模式；fixture finalizer 自动清理 |
| 国内网络被墙 | 中 | 阿里云镜像 + 本地编译 JAR |
| Docker Compose profile 不匹配 | 低 | 所有 `docker compose run` 显式加 `--profile test` |
| 宿主机空目录覆盖镜像文件 | 低 | volume mount 只挂需要热更新的目录（tests/reports），testcases 直接用镜像内文件 |

## 6. Docker 运维补充

### 6.1 Key 命令

```bash
# 重建镜像（代码变更后）
docker compose build test-runner

# 清理重建环境
docker compose down -v && docker compose up -d

# 进入容器调试
docker compose --profile test run --rm test-runner bash

# 查看所有容器状态
docker compose ps
```

### 6.2 调试技巧

```bash
# 直接在容器内跑 pytest 诊断
docker compose --profile test run --rm test-runner \
  pytest tests/ --collect-only -v

# 验证 API 是否就绪
docker compose --profile test run --rm test-runner \
  curl -s -X POST http://ruoyi-api:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 查看测试日志
tail -f logs/ruoyi_api_*.log
```

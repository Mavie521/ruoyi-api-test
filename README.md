# 若依接口测试框架

基于 `pytest + requests + Allure` 的接口自动化测试框架，覆盖若依管理系统（RuoYi）核心业务接口。

## 技术栈

| 组件 | 用途 |
|:---|:---|
| Python 3.8+ | 编程语言 |
| pytest | 测试框架 |
| requests | HTTP 客户端 |
| Allure | 测试报告 |
| mysql-connector-python | 数据库断言 |
| loguru | 日志 |
| openpyxl + jinja2 | Excel 数据驱动 |

## 项目结构

```
ruoyi_api_test/
├── api/                 # API 封装层（类似 POM 模式）
│   ├── base_api.py      # 基类：Session + Token 管理
│   ├── login_api.py     # 登录模块
│   ├── user_api.py      # 用户管理（测试控制器）
│   ├── system_user_api.py # 用户管理（真实业务）
│   └── role_api.py      # 角色管理
├── tests/               # pytest 脚本测试（33条）
│   ├── conftest.py      # fixtures：登录态/数据库/测试数据
│   ├── test_login.py
│   ├── test_user.py
│   ├── test_system_user.py  # 真实用户管理测试
│   └── test_role.py
├── testcases/           # Excel 数据驱动测试（20条）
│   └── test_excel_driver.py
├── data/                # 测试数据
│   ├── test_cases.xlsx  # Excel 用例模板
│   └── gen_excel.py     # 用例生成脚本
├── config/              # 配置
│   └── config.py
├── utils/               # 工具
│   ├── logger.py        # 日志
│   ├── assertions.py    # 断言器
│   ├── db_utils.py      # 数据库断言工具
│   ├── excel_utils.py   # Excel 读取
│   ├── data_driver.py   # Excel 驱动引擎
│   └── allure_utils.py  # Allure 报告工具
├── reports/             # 测试报告
├── conftest.py          # pytest 全局配置
├── pytest.ini           # pytest 配置
├── requirements.txt     # 依赖
├── run.py               # 运行入口
└── .env                 # 环境变量
```

## 快速开始

### 1. 环境准备

```bash
git clone <项目地址>
cd ruoyi_api_test

# 创建虚拟环境（可选）
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Mac/Linux

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

复制环境变量模板并修改：

```bash
cp .env.example .env
```

修改 `.env` 中的配置：

```ini
BASE_URL=http://localhost:8080        # 若依后端地址
ADMIN_USERNAME=admin                  # 管理员账号
ADMIN_PASSWORD=admin123               # 管理员密码
DB_HOST=127.0.0.1                     # 数据库地址
DB_PORT=3306                          # 数据库端口
DB_NAME=ry-vue                        # 数据库名
DB_USER=root                          # 数据库用户
DB_PASSWORD=123456                    # 数据库密码
```

### 3. 运行测试

```bash
# 运行全部测试（33条脚本 + 20条Excel驱动 = 53条）
python -m pytest tests/ testcases/ -v

# 只跑脚本测试
python -m pytest tests/ -v

# 只跑Excel驱动测试
python -m pytest testcases/ -v

# 只跑冒烟测试
python -m pytest tests/ -m smoke -v

# 并发运行
python -m pytest tests/ -n 4 -v
```

### 4. 查看报告

```bash
# 需要安装 Allure CLI：https://github.com/allure-framework/allure2/releases

# 方式一：命令行生成并打开
allure generate ./reports/allure-results -o ./reports/allure-report --clean
allure open ./reports/allure-report

# 方式二：使用 run.py
python run.py run       # 运行测试 + 生成报告
python run.py report    # 仅生成报告
```

## 核心设计

### API 封装层（类似 POM 模式）

```
tests/test_xxx.py          # 测试用例
    → api/xxx_api.py       # API 对象（封装接口操作）
        → api/base_api.py  # 基类（Session + Token 管理）
            → 若依后端     # HTTP 请求
```

### Token 自动管理

- `login()` 成功后自动保存 token
- 后续所有 API 请求自动携带 `Authorization: Bearer xxx`
- Fixture 机制实现 session 级共享，一次登录跑全部测试

### 数据库双维度断言

```
API 响应验证 → {"code": 200, "msg": "操作成功"}
    +
数据库落盘验证 → assert_value("SELECT status FROM sys_role WHERE id=%s", "0")
```

### 失败自动定位

- 每个请求自动 attach 到 Allure 报告
- 失败时自动 attach 异常堆栈和测试定位信息
- categories.json 对失败原因分类（API异常/DB断言/业务校验）

## 测试覆盖

| 模块 | 脚本测试 | Excel驱动 |
|:---|:---:|:---:|
| 登录认证 | 6条 | 5条 |
| 用户管理（真实） | 9条 | 2条 |
| 用户管理（测试控制器） | 7条 | 1条 |
| 角色管理 | 11条 | 3条 |
| 部门管理 | - | 2条 |
| 字典管理 | - | 2条 |
| 岗位管理 | - | 1条 |
| 系统监控 | - | 3条 |
| 包含断言示例 | - | 1条 |
| **合计** | **33条** | **20条** |

## CI 集成

### GitHub Actions

在项目根目录创建 `.github/workflows/test.yml`：

```yaml
name: API Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --alluredir=./allure-results
      - name: Generate report
        uses: simple-elf/allure-report-action@v1
        if: always()
        with:
          allure_results: ./allure-results
```

## 常见问题

**Q: 测试报 401 怎么办？**
A: 检查 `.env` 中的账号密码是否正确，或后端是否已启动。

**Q: 数据库断言失败？**
A: 确认数据库连接信息正确，且表结构匹配。

**Q: 如何添加新用例？**
A: 简单接口直接在 Excel 中加行；复杂业务在 `tests/` 下新建 `test_xxx.py`。

# =============================================
# RuoYi API Test Framework — Makefile
# 工程化统一命令入口
# =============================================

.PHONY: setup install install-dev lint test test-p0 test-all coverage \
        report clean clean-pyc clean-cache format help

# ── 环境搭建 ──────────────────────────────────

setup: venv install install-dev precommit   ## 一键搭环境（venv + 依赖 + pre-commit）

venv:                                       ## 创建虚拟环境
	python -m venv .venv
	@echo "✅ 虚拟环境已创建，执行: source .venv/Scripts/activate (Windows) 或 source .venv/bin/activate (Mac/Linux)"

install:                                    ## 安装运行依赖
	pip install -r requirements.txt

install-dev:                                ## 安装开发工具依赖
	pip install -r requirements-dev.txt

precommit:                                  ## 安装 pre-commit 钩子
	pre-commit install

# ── 测试执行 ──────────────────────────────────

test: test-p0                              ## 默认：跑 P0 冒烟

test-p0:                                    ## 跑 P0 冒烟测试
	python -m pytest tests/ -m p0 -v --tb=short

test-p1:                                    ## 跑 P1 测试
	python -m pytest tests/ -m p1 -v --tb=short

test-all:                                   ## 跑全部测试（含 Excel 数据驱动）
	python -m pytest tests/ testcases/ -v --tb=short

test-security:                              ## 只跑安全测试
	python -m pytest tests/ -m security -v --tb=short

test-keyword:                               ## 按关键字过滤: make test-keyword KW=login
	python -m pytest tests/ -k $(KW) -v --tb=short

# ── 代码质量 ──────────────────────────────────

lint:                                       ## pylint 静态检查
	pylint api/ tests/ utils/ config/

format:                                     ## black 自动格式化
	black api/ tests/ utils/ config/ scripts/

format-check:                               ## 只检查格式不改动
	black --check api/ tests/ utils/ config/ scripts/

coverage:                                   ## 测试覆盖率报告
	python -m pytest tests/ --cov=api --cov=utils --cov-config=.coveragerc \
		--cov-report=html --cov-report=term

# ── 报告 ──────────────────────────────────────

report:                                     ## 生成 Allure 报告
	python run.py report

open-report:                                ## 打开 Allure 报告
	python run.py open

# ── 清理 ──────────────────────────────────────

clean: clean-pyc clean-cache               ## 清理所有临时文件

clean-pyc:                                  ## 清理 Python 缓存文件
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-cache:                                ## 清理 pytest / allure 缓存
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf reports/allure-results 2>/dev/null || true
	rm -rf reports/allure-report 2>/dev/null || true

# ── Docker ────────────────────────────────────

docker-up:                                  ## 启动 Docker 后端服务
	docker compose up -d

docker-down:                                ## 关闭 Docker 所有服务
	docker compose down

docker-test:                                ## Docker 环境跑 P0 测试
	docker compose --profile test run --rm test-runner \
		sh -c "pytest tests/ -m p0 --alluredir=reports/allure-results -v"

docker-test-all:                            ## Docker 环境跑全量测试
	docker compose --profile test run --rm test-runner \
		sh -c "pytest tests/ testcases/test_excel_driver.py --alluredir=reports/allure-results -v"

docker-report:                              ## Docker 生成 Allure 报告
	docker compose --profile report run --rm allure-reporter

docker-clean:                               ## Docker 重建环境
	docker compose down -v
	docker compose up -d

# ── 帮助 ──────────────────────────────────────

help:                                       ## 显示帮助信息
	@echo "RuoYi API Test Framework — Makefile"
	@echo ""
	@echo "用法: make <target>"
	@echo ""
	@echo "── 环境搭建 ──"
	@grep -E '^[a-zA-Z_-]+:.*## ' Makefile | sort | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  %-20s %s\n", $$1, $$2}'

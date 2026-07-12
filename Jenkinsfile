/*
 * RuoYi API Test Framework — Jenkins Pipeline
 *
 * 两种运行模式：
 *   模式 A（直接执行）: Jenkins 主机直接装 Python + pytest，跑测试
 *   模式 B（Docker）:   通过 docker-compose 启动完整环境（MySQL+Redis+RuoYi+测试）
 *
 * 使用方法：
 *   1. Jenkins 创建流水线任务 → Pipeline script from SCM
 *   2. SCM: Git → https://github.com/Mavie521/ruoyi-api-test.git
 *   3. 脚本路径: Jenkinsfile
 *
 * 参数说明：
 *   - RUN_MODE:    direct / docker（选择运行方式）
 *   - ENV:         dev / staging / prod / docker
 *   - MARKER:      p0 / p1 / p2 / smoke / regression / critical
 *   - WORKERS:     并发进程数
 *   - RERUNS:      失败重试次数
 *   - BRANCH:      分支
 */

pipeline {
    agent any

    // =============================================
    // 构建参数
    // =============================================
    parameters {
        choice(
            name: 'RUN_MODE',
            choices: ['direct', 'docker'],
            description: '运行方式: direct=主机直跑, docker=容器化部署'
        )
        choice(
            name: 'ENV',
            choices: ['dev', 'staging', 'prod', 'docker'],
            description: '测试环境'
        )
        string(
            name: 'MARKER',
            defaultValue: 'p0',
            description: '用例标记: p0/p1/p2/smoke/critical/regression'
        )
        string(
            name: 'WORKERS',
            defaultValue: '2',
            description: '并发进程数'
        )
        string(
            name: 'RERUNS',
            defaultValue: '1',
            description: '失败重试次数'
        )
        gitParameter(
            name: 'BRANCH',
            type: 'PT_BRANCH',
            branchFilter: 'origin/(.*)',
            defaultValue: 'main',
            description: '分支'
        )
    }

    // =============================================
    // 环境变量
    // =============================================
    environment {
        VENV_DIR      = "${WORKSPACE}/venv"
        ALLURE_RESULTS = "${WORKSPACE}/reports/allure-results"
        ALLURE_REPORT  = "${WORKSPACE}/reports/allure-report"
        BUILD_TIMESTAMP = sh(script: 'date "+%Y-%m-%d %H:%M:%S"', returnStdout: true).trim()
    }

    // =============================================
    // 工具
    // =============================================
    tools {
        python 'python3'
    }

    stages {

        // ========================
        // ① 拉取代码
        // ========================
        stage('① 拉取代码') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "${params.BRANCH}"]],
                    userRemoteConfigs: [[url: 'https://github.com/Mavie521/ruoyi-api-test.git']]
                ])
                script {
                    echo "✅ 分支: ${env.BRANCH_NAME} / 提交: ${env.GIT_COMMIT.take(8)}"
                    echo "   模式: ${params.RUN_MODE} / 环境: ${params.ENV}"
                }
            }
        }

        // ========================
        // ② 环境准备
        // ========================
        stage('② 环境准备') {
            steps {
                script {
                    if (params.RUN_MODE == 'docker') {
                        // Docker 模式：检查 Docker 环境
                        sh 'docker --version'
                        sh 'docker-compose --version || docker compose version'
                        echo "✅ Docker 环境就绪"
                    } else {
                        // Direct 模式：创建虚拟环境 + 安装依赖
                        sh """
                            python3 -m venv "${VENV_DIR}"
                            source "${VENV_DIR}/bin/activate"
                            pip install --upgrade pip -q
                            pip install -r requirements.txt -q
                        """
                        echo "✅ Python 依赖安装完成"
                    }
                }
            }
        }

        // ========================
        // ③ 启动服务（仅 Docker 模式）
        // ========================
        stage('③ 启动服务') {
            when {
                expression { params.RUN_MODE == 'docker' }
            }
            steps {
                script {
                    sh 'docker-compose down -v 2>/dev/null || true'

                    // 检查是否需要下载 SQL
                    sh 'ls docker/mysql/init/ruoyi.sql 2>/dev/null || bash scripts/download_sql.sh'

                    // 启动 MySQL + Redis + RuoYi
                    sh 'docker-compose up -d mysql redis ruoyi-api'

                    echo "等待 RuoYi 后端就绪..."
                    sh """
                        timeout=90
                        elapsed=0
                        while [ \$elapsed -lt \$timeout ]; do
                            if curl -sf http://localhost:8080/actuator/health 2>/dev/null | grep -q UP; then
                                echo '✅ RuoYi 后端已就绪'
                                break
                            fi
                            sleep 3
                            elapsed=\$((elapsed + 3))
                            echo "   ...等待中 (\${elapsed}s)"
                        done
                    """
                }
            }
        }

        // ========================
        // ④ 代码检查
        // ========================
        stage('④ 代码检查') {
            steps {
                script {
                    if (params.RUN_MODE == 'docker') {
                        sh 'docker-compose run --rm test-runner python -m pytest --collect-only tests/ -q'
                    } else {
                        sh """
                            source "${VENV_DIR}/bin/activate && \
                            python -m pytest --collect-only tests/ -q
                        """
                    }
                    echo "✅ 用例收集完成"
                }
            }
        }

        // ========================
        // ⑤ 执行测试
        // ========================
        stage('⑤ 执行测试') {
            steps {
                script {
                    // 清理上次结果
                    sh "rm -rf ${ALLURE_RESULTS}"

                    def marker  = params.MARKER ? "-m ${params.MARKER}" : ""
                    def workers = params.WORKERS.toInteger() > 1 ? "-n ${params.WORKERS}" : ""
                    def reruns  = params.RERUNS.toInteger() > 0 ? "--reruns ${params.RERUNS} --reruns-delay 5" : ""

                    if (params.RUN_MODE == 'docker') {
                        // Docker 模式：用 test-runner 容器执行
                        sh """
                            docker-compose run --rm test-runner \
                                sh -c "pytest tests/ ${marker} ${workers} ${reruns} \
                                    --alluredir=./reports/allure-results \
                                    --clean-alluredir -v"
                        """
                    } else {
                        // Direct 模式：主机直接执行
                        sh """
                            source "${VENV_DIR}/bin/activate && \
                            python run.py run --env=${params.ENV} ${marker} ${workers} ${reruns}
                        """
                    }
                }
            }
        }

        // ========================
        // ⑥ Allure 报告
        // ========================
        stage('⑥ Allure 报告') {
            steps {
                script {
                    allure(
                        includeProperties: true,
                        results: [[path: 'reports/allure-results']],
                        report: 'reports/allure-report',
                        reportBuildPolicy: 'ALWAYS'
                    )
                    echo "✅ Allure 报告已生成"
                }
            }
        }

        // ========================
        // ⑦ 归档产物
        // ========================
        stage('⑦ 归档产物') {
            steps {
                script {
                    archiveArtifacts(
                        artifacts: 'reports/allure-results/**',
                        fingerprint: true,
                        allowEmptyArchive: true
                    )
                    archiveArtifacts(
                        artifacts: 'logs/**',
                        allowEmptyArchive: true
                    )
                    echo "✅ 测试产物已归档"
                }
            }
        }
    }

    // =============================================
    // 构建后处理
    // =============================================
    post {
        always {
            script {
                // 记录构建摘要
                echo "=" * 60
                echo "📋 构建摘要"
                echo "   模式:     ${params.RUN_MODE}"
                echo "   环境:     ${params.ENV}"
                echo "   标记:     ${params.MARKER}"
                echo "   分支:     ${env.BRANCH_NAME}"
                echo "   提交:     ${env.GIT_COMMIT.take(8)}"
                echo "   时间:     ${BUILD_TIMESTAMP}"
                echo "=" * 60
            }
        }

        success {
            script {
                echo "🎉 测试全部通过！"
            }
        }

        failure {
            script {
                echo "❌ 测试有失败，请查看 Allure 报告"
            }
        }

        cleanup {
            script {
                // Docker 模式：关闭服务
                if (params.RUN_MODE == 'docker') {
                    sh 'docker-compose down -v 2>/dev/null || true'
                    echo "🐳 Docker 服务已关闭"
                }
                // 清理工作空间
                cleanWs(cleanWhenNotBuilt: false,
                        deleteDirectories: true,
                        disableDeferredWipeDown: true)
            }
        }
    }
}

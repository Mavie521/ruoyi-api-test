pipeline {
    agent any

    parameters {
        choice(name: 'RUN_MODE', choices: ['direct', 'docker'], description: '运行方式')
        choice(name: 'ENV', choices: ['dev', 'staging', 'prod', 'docker'], description: '测试环境')
        string(name: 'MARKER', defaultValue: 'p0', description: '用例标记')
        string(name: 'WORKERS', defaultValue: '2', description: '并发数')
        string(name: 'RERUNS', defaultValue: '1', description: '重试次数')
        string(name: 'BRANCH', defaultValue: 'main', description: '分支')
    }

    environment {
        ALLURE_RESULTS = "${WORKSPACE}/reports/allure-results"
        ALLURE_REPORT  = "${WORKSPACE}/reports/allure-report"
        BUILD_TIMESTAMP = sh(script: 'date "+%Y-%m-%d %H:%M:%S"', returnStdout: true).trim()
    }

    stages {
        stage('拉取代码') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "${params.BRANCH}"]],
                    userRemoteConfigs: [[url: 'https://github.com/Mavie521/ruoyi-api-test.git']]
                ])
            }
        }

        stage('环境准备') {
            when { expression { params.RUN_MODE == 'docker' } }
            steps {
                sh 'docker compose down -v 2>/dev/null || true'
                sh 'docker compose up -d'
            }
        }

        stage('执行测试') {
            steps {
                sh "rm -rf ${ALLURE_RESULTS}"
                sh """
                    cd /app/ruoyi-api-test && \
                    docker compose run --rm test-runner \
                        sh -c "pytest tests/ -m ${params.MARKER} \
                            --alluredir=./reports/allure-results \
                            --clean-alluredir -v \
                            --reruns ${params.RERUNS} --reruns-delay 5"
                """
            }
        }

        stage('Allure 报告') {
            steps {
                allure includeProperties: true, results: [[path: 'reports/allure-results']]
            }
        }
    }

    post {
        success { echo '测试通过' }
        failure { echo '测试失败，请查看报告' }
        cleanup { cleanWs(deleteDirectories: true) }
    }
}

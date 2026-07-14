pipeline {
    agent any
    parameters {
        choice(name: 'MODE', choices: ['fast', 'clean'], description: '运行模式')
        choice(name: 'MARKER', choices: ['p0', 'p1', 'p2', 'all'], description: '用例级别')
    }
    stages {
        stage('部署') {
            steps {
                sh 'cd /app/ruoyi-api-test && docker compose up -d || true'
                sh 'sleep 20'
            }
        }
        stage('测试') {
            steps {
                sh 'rm -rf /app/ruoyi-api-test/reports/allure-results || true'
                sh "cd /app/ruoyi-api-test && docker compose run -d --name temp-runner test-runner pytest tests/ -m ${params.MARKER} --alluredir=reports/allure-results --clean-alluredir -v || true"
                sh 'docker cp temp-runner:/app/reports/allure-results /app/ruoyi-api-test/reports/allure-results || true'
                sh 'docker rm -f temp-runner || true'
            }
        }
        stage('报告') {
            steps {
                sh 'rm -rf allure-results || true'
                sh 'cp -r /app/ruoyi-api-test/reports/allure-results allure-results || true'
                allure([
                    includeProperties: true,
                    results: [[path: 'allure-results']],
                    reportBuildPolicy: 'ALWAYS'
                ])
            }
        }
    }
    post {
        always {
            script {
                currentBuild.displayName = "#${BUILD_NUMBER}-${params.MARKER}-${params.MODE}"
            }
        }
    }
}

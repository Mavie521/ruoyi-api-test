pipeline {
    agent any
    parameters {
        choice(name: 'MODE', choices: ['fast', 'clean'], description: '运行模式')
        choice(name: 'MARKER', choices: ['p0', 'p1', 'p2', 'all'], description: '用例级别')
        string(name: 'MAX_RETRIES', defaultValue: '40', description: '等待后端就绪的最大重试次数')
        string(name: 'SLEEP', defaultValue: '5', description: '每次重试间隔（秒）')
        string(name: 'RERUNS', defaultValue: '1', description: '失败重跑次数')
    }
    triggers {
        cron('H 8 * * *')
    }
    stages {
        stage('部署') {
            steps {
                sh 'cd /app/ruoyi-api-test && docker compose down 2>/dev/null || true'
                sh 'cd /app/ruoyi-api-test && docker compose up -d || true'
            }
        }
        stage('测试') {
            steps {
                sh "bash /app/ruoyi-api-test/scripts/run_all.sh ${params.MARKER} ${params.MODE} build ${params.MAX_RETRIES} ${params.SLEEP} ${params.RERUNS}"
            }
        }
        stage('报告') {
            steps {
                sh 'rm -rf allure-results allure-report || true'
                sh 'cp -r /app/ruoyi-api-test/reports/allure-results allure-results || true'
                sh 'rm -rf /var/jenkins_home/jobs/ruoyi-api-test/builds/*/archive/allure-report 2>/dev/null || true'
                allure results: [[path: 'allure-results']], reportBuildPolicy: 'ALWAYS'
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

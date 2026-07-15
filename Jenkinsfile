pipeline {
    agent any
    parameters {
        choice(name: 'MODE', choices: ['fast', 'clean'], description: '运行模式')
        choice(name: 'MARKER', choices: ['p0', 'p1', 'p2', 'all'], description: '用例级别')
    }
    triggers {
        cron('H 8 * * *')
    }
    stages {
        stage('全流程') {
            steps {
                sh "bash /home/yy/ruoyi-api-test/scripts/run_all.sh ${params.MARKER} ${params.MODE}"
            }
        }
        stage('报告') {
            steps {
                sh 'rm -rf allure-results allure-report || true'
                sh 'cp -r /home/yy/ruoyi-api-test/reports/allure-results allure-results || true'
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

pipeline {
    agent any

    environment {
        SONARQUBE_SERVER = 'SonarQube-Server'
        SONAR_PROJECT_KEY = 'STB_Automation_Framework'
        SONAR_PROJECT_NAME = 'STB Automation Framework'
        SCANNER_HOME = tool 'SonarQube-Scanner'
    }

    triggers {
        pollSCM('H/5 * * * *')   // Poll Git every 5 minutes (local network)
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 15, unit: 'MINUTES')
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Commit: ${env.GIT_COMMIT?.take(7)}"
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube-Server') {
                    sh """
                        ${SCANNER_HOME}/bin/sonar-scanner \
                        -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                        -Dsonar.projectName="${SONAR_PROJECT_NAME}" \
                        -Dsonar.sources=. \
                        -Dsonar.host.url=${env.SONAR_HOST_URL} \
                        -Dsonar.token=${env.SONAR_AUTH_TOKEN}
                    """
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }

        success {
            emailext (
                subject: "✅ SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: green;">SonarQube Scan Successful</h2>
                    <table border="1" cellpadding="8" style="border-collapse: collapse;">
                        <tr><td><b>Project</b></td><td>${env.JOB_NAME}</td></tr>
                        <tr><td><b>Build #</b></td><td>${env.BUILD_NUMBER}</td></tr>
                        <tr><td><b>Commit</b></td><td>${env.GIT_COMMIT?.take(7)}</td></tr>
                    </table>
                    <p><b>SonarQube Report:</b> <a href="${env.SONAR_HOST_URL}/dashboard?id=${SONAR_PROJECT_KEY}">View Dashboard</a></p>
                    <p><b>Build Console:</b> <a href="${env.BUILD_URL}console">View Logs</a></p>
                </body>
                </html>
                """,
                to: 'ovt.bangalore@gmail.com',
                from: 'sathish.s@vimatch.in',
                mimeType: 'text/html',
                attachLog: true
            )
        }

        failure {
            emailext (
                subject: "❌ FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: red;">Scan Failed</h2>
                    <p><b>Console Output:</b> <a href="${env.BUILD_URL}console">Click here to view logs</a></p>
                </body>
                </html>
                """,
                to: 'ovt.bangalore@gmail.com',
                from: 'sathish.s@vimatch.in',
                mimeType: 'text/html',
                attachLog: true
            )
        }

        unstable {
            emailext (
                subject: "⚠️ QUALITY GATE FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: orange;">SonarQube Quality Gate Failed</h2>
                    <p>Code did not meet quality standards. <a href="${env.SONAR_HOST_URL}/dashboard?id=${SONAR_PROJECT_KEY}">View Issues</a></p>
                </body>
                </html>
                """,
                to: 'ovt.bangalore@gmail.com',
                from: 'sathish.s@vimatch.in',
                mimeType: 'text/html'
            )
        }
    }
}
pipeline {
    agent any

    environment {
        // SonarQube config
        SONARQUBE_SERVER = 'SonarQube-Server'     // Must match name in Jenkins > Configure System
        SONAR_PROJECT_KEY = 'STB_Automation_Framework_Code_Review'       // Your SonarQube project key
        SONAR_PROJECT_NAME = 'STB_Automation_Framework_Code_Review'      // Display name in SonarQube
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
                echo "Branch: ${env.BRANCH_NAME}"
                echo "Commit: ${env.GIT_COMMIT}"
            }
        }

        stage('Build & Compile') {
            steps {
                // For Maven projects
                sh 'mvn clean compile -DskipTests'

                // For Gradle projects, use:
                // sh './gradlew clean compileJava'

                // For Node.js projects, use:
                // sh 'npm install && npm run build'
            }
        }

        stage('Run Unit Tests') {
            steps {
                sh 'mvn test'
                // For Gradle: sh './gradlew test'
            }
            post {
                always {
                    junit testResults: 'target/surefire-reports/*.xml', allowEmptyResults: true
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube-Server') {
                    sh """
                        mvn sonar:sonar \
                        -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                        -Dsonar.projectName="${SONAR_PROJECT_NAME}" \
                        -Dsonar.java.binaries=target/classes
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
                    <h2 style="color: green;">Build Successful</h2>
                    <table border="1" cellpadding="8" style="border-collapse: collapse;">
                        <tr><td><b>Project</b></td><td>${env.JOB_NAME}</td></tr>
                        <tr><td><b>Build #</b></td><td>${env.BUILD_NUMBER}</td></tr>
                        <tr><td><b>Branch</b></td><td>${env.BRANCH_NAME}</td></tr>
                        <tr><td><b>Commit</b></td><td>${env.GIT_COMMIT?.take(7)}</td></tr>
                        <tr><td><b>Duration</b></td><td>${currentBuild.durationString}</td></tr>
                    </table>
                    <p><b>SonarQube Report:</b> <a href="http://192.168.0.193:9000/dashboard?id=${SONAR_PROJECT_KEY}">View Dashboard</a></p>
                    <p><b>Build Console:</b> <a href="${env.BUILD_URL}console">View Logs</a></p>
                </body>
                </html>
                """,
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'ovt.bangalore@gmail.com'}",
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
                    <h2 style="color: red;">Build Failed</h2>
                    <p>The build failed during the pipeline execution.</p>
                    <p><b>Project:</b> ${env.JOB_NAME}</p>
                    <p><b>Build #:</b> ${env.BUILD_NUMBER}</p>
                    <p><b>Failed Stage:</b> ${env.STAGE_NAME}</p>
                    <p><b>Console Output:</b> <a href="${env.BUILD_URL}console">Click here to view logs</a></p>
                </body>
                </html>
                """,
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'your-email@example.com'}",
                from: 'jenkins@local.network',
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
                    <p>The build passed but did not meet the SonarQube quality standards.</p>
                    <p><b>Project:</b> ${env.JOB_NAME}</p>
                    <p><b>Build #:</b> ${env.BUILD_NUMBER}</p>
                    <p><b>SonarQube Dashboard:</b> <a href="http://192.168.1.50:9000/dashboard?id=${SONAR_PROJECT_KEY}">View Issues</a></p>
                </body>
                </html>
                """,
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'your-email@example.com'}",
                from: 'jenkins@local.network',
                mimeType: 'text/html'
            )
        }
    }
}
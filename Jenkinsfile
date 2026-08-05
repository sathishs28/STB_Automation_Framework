pipeline {
    agent any

    environment {
        SONARQUBE_SERVER = 'SonarQube-Server'
        SONAR_PROJECT_KEY = 'STB_Automation_Framework'
        SONAR_PROJECT_NAME = 'STB Automation Framework'
        SCANNER_HOME = tool 'SonarQube-Scanner'
        SONAR_HOST = 'http://192.168.0.5:9000'
    }

    triggers {
        pollSCM('H/5 * * * *')
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

        stage('Fetch SonarQube Metrics') {
            steps {
                script {
                    // Fetch key metrics from SonarQube API
                    def metricsResponse = sh(
                        script: """
                            curl -s -u ${env.SONAR_AUTH_TOKEN}: \
                            "${SONAR_HOST}/api/measures/component?component=${SONAR_PROJECT_KEY}&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,ncloc,alert_status,security_hotspots,reliability_rating,security_rating,sqale_rating"
                        """,
                        returnStdout: true
                    ).trim()

                    // Parse JSON response
                    def json = readJSON text: metricsResponse
                    def measures = json.component.measures

                    // Extract individual metrics
                    env.SONAR_BUGS = measures.find { it.metric == 'bugs' }?.value ?: 'N/A'
                    env.SONAR_VULNERABILITIES = measures.find { it.metric == 'vulnerabilities' }?.value ?: 'N/A'
                    env.SONAR_CODE_SMELLS = measures.find { it.metric == 'code_smells' }?.value ?: 'N/A'
                    env.SONAR_COVERAGE = measures.find { it.metric == 'coverage' }?.value ?: 'N/A'
                    env.SONAR_DUPLICATION = measures.find { it.metric == 'duplicated_lines_density' }?.value ?: 'N/A'
                    env.SONAR_LINES = measures.find { it.metric == 'ncloc' }?.value ?: 'N/A'
                    env.SONAR_STATUS = measures.find { it.metric == 'alert_status' }?.value ?: 'N/A'
                    env.SONAR_HOTSPOTS = measures.find { it.metric == 'security_hotspots' }?.value ?: 'N/A'

                    // Determine status color
                    env.STATUS_COLOR = (env.SONAR_STATUS == 'OK') ? 'green' : 'red'
                    env.STATUS_TEXT = (env.SONAR_STATUS == 'OK') ? 'PASSED' : 'FAILED'
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
                subject: "SonarQube Report: ${env.JOB_NAME} #${env.BUILD_NUMBER} - ${env.STATUS_TEXT}",
                body: """
                <html>
                <head>
                    <style>
                        body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }
                        .container { max-width: 700px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
                        .header { background-color: #${env.STATUS_COLOR}; color: white; padding: 25px; text-align: center; }
                        .header h1 { margin: 0; font-size: 24px; }
                        .header p { margin: 8px 0 0 0; opacity: 0.9; }
                        .content { padding: 25px; }
                        .summary { display: flex; justify-content: space-between; margin-bottom: 25px; }
                        .metric-box { text-align: center; padding: 15px; border-radius: 6px; background: #f8f9fa; flex: 1; margin: 0 5px; }
                        .metric-value { font-size: 28px; font-weight: bold; color: #333; }
                        .metric-label { font-size: 12px; color: #666; margin-top: 5px; text-transform: uppercase; }
                        .bugs { color: #d9534f; }
                        .vulnerabilities { color: #d9534f; }
                        .smells { color: #f0ad4e; }
                        .coverage { color: #5cb85c; }
                        .links { margin-top: 25px; padding-top: 20px; border-top: 1px solid #eee; }
                        .btn { display: inline-block; padding: 10px 20px; margin: 5px; border-radius: 4px; text-decoration: none; color: white; font-size: 14px; }
                        .btn-primary { background: #337ab7; }
                        .btn-success { background: #5cb85c; }
                        .btn-warning { background: #f0ad4e; }
                        .footer { background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #999; }
                        table.info { width: 100%; margin-bottom: 20px; }
                        table.info td { padding: 8px; border-bottom: 1px solid #eee; }
                        table.info td:first-child { font-weight: bold; width: 30%; color: #555; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>SonarQube Analysis Report</h1>
                            <p>Quality Gate: ${env.STATUS_TEXT}</p>
                        </div>
                        
                        <div class="content">
                            <h3 style="margin-top: 0;">Project Information</h3>
                            <table class="info">
                                <tr><td>Project</td><td>${env.JOB_NAME}</td></tr>
                                <tr><td>Build Number</td><td>#${env.BUILD_NUMBER}</td></tr>
                                <tr><td>Commit</td><td>${env.GIT_COMMIT?.take(7)}</td></tr>
                                <tr><td>Branch</td><td>${env.GIT_BRANCH ?: 'main'}</td></tr>
                                <tr><td>Duration</td><td>${currentBuild.durationString}</td></tr>
                            </table>

                            <h3>Code Quality Metrics</h3>
                            <div class="summary">
                                <div class="metric-box">
                                    <div class="metric-value bugs">${env.SONAR_BUGS}</div>
                                    <div class="metric-label">Bugs</div>
                                </div>
                                <div class="metric-box">
                                    <div class="metric-value vulnerabilities">${env.SONAR_VULNERABILITIES}</div>
                                    <div class="metric-label">Vulnerabilities</div>
                                </div>
                                <div class="metric-box">
                                    <div class="metric-value smells">${env.SONAR_CODE_SMELLS}</div>
                                    <div class="metric-label">Code Smells</div>
                                </div>
                                <div class="metric-box">
                                    <div class="metric-value coverage">${env.SONAR_COVERAGE}%</div>
                                    <div class="metric-label">Coverage</div>
                                </div>
                            </div>

                            <div class="summary">
                                <div class="metric-box">
                                    <div class="metric-value">${env.SONAR_HOTSPOTS}</div>
                                    <div class="metric-label">Security Hotspots</div>
                                </div>
                                <div class="metric-box">
                                    <div class="metric-value">${env.SONAR_DUPLICATION}%</div>
                                    <div class="metric-label">Duplication</div>
                                </div>
                                <div class="metric-box">
                                    <div class="metric-value">${env.SONAR_LINES}</div>
                                    <div class="metric-label">Lines of Code</div>
                                </div>
                            </div>

                            <div class="links">
                                <h3>Quick Links</h3>
                                <a href="${SONAR_HOST}/dashboard?id=${SONAR_PROJECT_KEY}" class="btn btn-primary">Open SonarQube Dashboard</a>
                                <a href="${SONAR_HOST}/component_measures?id=${SONAR_PROJECT_KEY}" class="btn btn-success">View Detailed Metrics</a>
                                <a href="${SONAR_HOST}/project/issues?id=${SONAR_PROJECT_KEY}&resolved=false" class="btn btn-warning">View All Issues</a>
                                <br><br>
                                <a href="${env.BUILD_URL}console" class="btn btn-primary">Jenkins Console Output</a>
                            </div>
                        </div>
                        
                        <div class="footer">
                            Generated by Jenkins | ${new Date().format('yyyy-MM-dd HH:mm:ss')}
                        </div>
                    </div>
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
                subject: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: red;">Pipeline Failed</h2>
                    <p>The build or SonarQube scan failed.</p>
                    <p><b>Project:</b> ${env.JOB_NAME}</p>
                    <p><b>Build #:</b> ${env.BUILD_NUMBER}</p>
                    <p><b>Console Output:</b> <a href="${env.BUILD_URL}console">View Logs</a></p>
                </body>
                </html>
                """,
                to: 'ovt.bangalore@gmail.com',
                from: 'sathish.s@vimatch.in',
                mimeType: 'text/html',
                attachLog: true
            )
        }
    }
}
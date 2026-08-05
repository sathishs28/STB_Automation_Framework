pipeline {
    agent any

    environment {
        SONARQUBE_SERVER = 'SonarQube-Server'
        SONAR_PROJECT_KEY = 'STB_Automation_Framework'
        SONAR_PROJECT_NAME = 'STB Automation Framework'
        SCANNER_HOME = tool 'SonarQube-Scanner'
        SONAR_HOST = 'http://192.168.0.5:9000'
        
        // Default values in case metrics fetch fails
        SONAR_BUGS = 'N/A'
        SONAR_VULNERABILITIES = 'N/A'
        SONAR_CODE_SMELLS = 'N/A'
        SONAR_COVERAGE = 'N/A'
        SONAR_DUPLICATION = 'N/A'
        SONAR_LINES = 'N/A'
        SONAR_STATUS = 'UNKNOWN'
        SONAR_HOTSPOTS = 'N/A'
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

        stage('Fetch SonarQube Metrics') {
            steps {
                script {
                    try {
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
                        env.SONAR_BUGS = measures.find { it.metric == 'bugs' }?.value ?: '0'
                        env.SONAR_VULNERABILITIES = measures.find { it.metric == 'vulnerabilities' }?.value ?: '0'
                        env.SONAR_CODE_SMELLS = measures.find { it.metric == 'code_smells' }?.value ?: '0'
                        env.SONAR_COVERAGE = measures.find { it.metric == 'coverage' }?.value ?: '0.0'
                        env.SONAR_DUPLICATION = measures.find { it.metric == 'duplicated_lines_density' }?.value ?: '0.0'
                        env.SONAR_LINES = measures.find { it.metric == 'ncloc' }?.value ?: '0'
                        env.SONAR_STATUS = measures.find { it.metric == 'alert_status' }?.value ?: 'UNKNOWN'
                        env.SONAR_HOTSPOTS = measures.find { it.metric == 'security_hotspots' }?.value ?: '0'

                        echo "Metrics fetched: Bugs=${env.SONAR_BUGS}, Vulnerabilities=${env.SONAR_VULNERABILITIES}, Status=${env.SONAR_STATUS}"
                    } catch (Exception e) {
                        echo "WARNING: Could not fetch metrics from SonarQube API: ${e.message}"
                        // Keep default values
                    }
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
            script {
                // Determine build status and colors
                def buildStatus = currentBuild.currentResult
                def statusColor
                def statusText
                def statusIcon

                if (buildStatus == 'SUCCESS') {
                    statusColor = '28a745'      // Green
                    statusText = 'PASSED'
                    statusIcon = '✅'
                } else if (buildStatus == 'UNSTABLE') {
                    statusColor = 'fd7e14'      // Orange
                    statusText = 'QUALITY GATE FAILED'
                    statusIcon = '⚠️'
                } else {
                    statusColor = 'dc3545'      // Red
                    statusText = 'FAILED'
                    statusIcon = '❌'
                }

                // Send the report email regardless of status
                emailext (
                    subject: "${statusIcon} SonarQube Report: ${env.JOB_NAME} #${env.BUILD_NUMBER} - ${statusText}",
                    body: """
                    <html>
                    <head>
                        <style>
                            body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }
                            .container { max-width: 750px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
                            .header { background-color: #${statusColor}; color: white; padding: 25px; text-align: center; }
                            .header h1 { margin: 0; font-size: 24px; }
                            .header .status-badge { display: inline-block; background: rgba(255,255,255,0.2); padding: 6px 16px; border-radius: 20px; margin-top: 10px; font-size: 14px; font-weight: bold; }
                            .content { padding: 25px; }
                            .alert { background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin-bottom: 20px; color: #856404; }
                            .alert-fail { background: #f8d7da; border-left: 4px solid #dc3545; padding: 12px; margin-bottom: 20px; color: #721c24; }
                            h3 { color: #333; margin-top: 25px; border-bottom: 2px solid #eee; padding-bottom: 8px; }
                            .summary { display: flex; justify-content: space-between; flex-wrap: wrap; margin-bottom: 15px; }
                            .metric-box { text-align: center; padding: 18px 10px; border-radius: 8px; background: #f8f9fa; flex: 1; margin: 5px; min-width: 100px; border-top: 3px solid #ddd; }
                            .metric-value { font-size: 32px; font-weight: bold; }
                            .metric-label { font-size: 11px; color: #666; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
                            .bugs { border-color: #d9534f; color: #d9534f; }
                            .vulns { border-color: #d9534f; color: #d9534f; }
                            .smells { border-color: #f0ad4e; color: #f0ad4e; }
                            .coverage { border-color: #5cb85c; color: #5cb85c; }
                            .neutral { border-color: #337ab7; color: #337ab7; }
                            table.info { width: 100%; margin-bottom: 20px; border-collapse: collapse; }
                            table.info td { padding: 10px; border-bottom: 1px solid #eee; }
                            table.info td:first-child { font-weight: bold; width: 35%; color: #555; }
                            .links { margin-top: 25px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; }
                            .btn { display: inline-block; padding: 10px 20px; margin: 5px; border-radius: 4px; text-decoration: none; color: white; font-size: 13px; }
                            .btn-primary { background: #337ab7; }
                            .btn-success { background: #5cb85c; }
                            .btn-warning { background: #f0ad4e; }
                            .btn-danger { background: #dc3545; }
                            .footer { background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #999; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>SonarQube Analysis Report</h1>
                                <div class="status-badge">${statusIcon} ${statusText}</div>
                            </div>
                            
                            <div class="content">
                                ${buildStatus == 'FAILURE' ? '<div class="alert-fail"><strong>Note:</strong> The pipeline failed. The metrics below reflect the latest available scan data.</div>' : ''}
                                ${buildStatus == 'UNSTABLE' ? '<div class="alert"><strong>Note:</strong> The SonarQube Quality Gate did not pass. Please review the issues below.</div>' : ''}
                                
                                <h3>Build Information</h3>
                                <table class="info">
                                    <tr><td>Project</td><td>${env.JOB_NAME}</td></tr>
                                    <tr><td>Build Number</td><td>#${env.BUILD_NUMBER}</td></tr>
                                    <tr><td>Commit</td><td>${env.GIT_COMMIT?.take(7) ?: 'N/A'}</td></tr>
                                    <tr><td>Branch</td><td>${env.GIT_BRANCH ?: 'main'}</td></tr>
                                    <tr><td>Build Status</td><td><strong style="color: #${statusColor};">${statusText}</strong></td></tr>
                                    <tr><td>Duration</td><td>${currentBuild.durationString}</td></tr>
                                </table>

                                <h3>Code Quality Metrics</h3>
                                <div class="summary">
                                    <div class="metric-box bugs">
                                        <div class="metric-value">${env.SONAR_BUGS}</div>
                                        <div class="metric-label">Bugs</div>
                                    </div>
                                    <div class="metric-box vulns">
                                        <div class="metric-value">${env.SONAR_VULNERABILITIES}</div>
                                        <div class="metric-label">Vulnerabilities</div>
                                    </div>
                                    <div class="metric-box smells">
                                        <div class="metric-value">${env.SONAR_CODE_SMELLS}</div>
                                        <div class="metric-label">Code Smells</div>
                                    </div>
                                    <div class="metric-box coverage">
                                        <div class="metric-value">${env.SONAR_COVERAGE}%</div>
                                        <div class="metric-label">Coverage</div>
                                    </div>
                                </div>

                                <div class="summary">
                                    <div class="metric-box neutral">
                                        <div class="metric-value">${env.SONAR_HOTSPOTS}</div>
                                        <div class="metric-label">Security Hotspots</div>
                                    </div>
                                    <div class="metric-box neutral">
                                        <div class="metric-value">${env.SONAR_DUPLICATION}%</div>
                                        <div class="metric-label">Duplication</div>
                                    </div>
                                    <div class="metric-box neutral">
                                        <div class="metric-value">${env.SONAR_LINES}</div>
                                        <div class="metric-label">Lines of Code</div>
                                    </div>
                                    <div class="metric-box neutral">
                                        <div class="metric-value">${env.SONAR_STATUS}</div>
                                        <div class="metric-label">Quality Gate</div>
                                    </div>
                                </div>

                                <div class="links">
                                    <h3>Quick Links</h3>
                                    <a href="${SONAR_HOST}/dashboard?id=${SONAR_PROJECT_KEY}" class="btn btn-primary">SonarQube Dashboard</a>
                                    <a href="${SONAR_HOST}/component_measures?id=${SONAR_PROJECT_KEY}" class="btn btn-success">Detailed Metrics</a>
                                    <a href="${SONAR_HOST}/project/issues?id=${SONAR_PROJECT_KEY}&resolved=false" class="btn btn-warning">View All Issues</a>
                                    <a href="${SONAR_HOST}/security_hotspots?id=${SONAR_PROJECT_KEY}" class="btn btn-danger">Security Hotspots</a>
                                    <br><br>
                                    <a href="${env.BUILD_URL}console" class="btn btn-primary">Jenkins Console Output</a>
                                </div>
                            </div>
                            
                            <div class="footer">
                                Generated by Jenkins | Build #${env.BUILD_NUMBER} | ${new Date().format('yyyy-MM-dd HH:mm:ss')}
                            </div>
                        </div>
                    </body>
                    </html>
                    """,
                    to: 'ovt.bangalore@gmail.com',
                    from: 'jenkins@local.network',
                    mimeType: 'text/html',
                    attachLog: true
                )
            }
            cleanWs()
        }
    }
}
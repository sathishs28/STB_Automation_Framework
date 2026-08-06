pipeline {
    agent any

    environment {
        SONARQUBE_SERVER = 'SonarQube-Server'
        SONAR_PROJECT_KEY = 'STB_Automation_Framework'
        SONAR_PROJECT_NAME = 'STB Automation Framework'
        SCANNER_HOME = tool 'SonarQube-Scanner'
        SONAR_HOST = 'http://192.168.0.5:9000'

        // Default values (used if fetch fails)
        SONAR_BUGS = '0'
        SONAR_VULNERABILITIES = '0'
        SONAR_CODE_SMELLS = '0'
        SONAR_COVERAGE = '0.0'
        SONAR_DUPLICATION = '0.0'
        SONAR_LINES = '0'
        SONAR_STATUS = 'UNKNOWN'
        SONAR_HOTSPOTS = '0'

        // New issues (since last analysis)
        SONAR_NEW_BUGS = '0'
        SONAR_NEW_VULNERABILITIES = '0'
        SONAR_NEW_CODE_SMELLS = '0'
        SONAR_NEW_HOTSPOTS = '0'
        SONAR_NEW_COVERAGE = '0.0'
        
        // Severity breakdown
        SONAR_BLOCKER = '0'
        SONAR_CRITICAL = '0'
        SONAR_MAJOR = '0'
        SONAR_MINOR = '0'
        SONAR_INFO = '0'
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
                    script {
                        def qg = waitForQualityGate()

                        env.SONAR_STATUS = qg.status

                        if (qg.status != 'OK') {
                            currentBuild.result = 'UNSTABLE'

                            echo "Quality Gate failed: ${qg.status}"
                        } else {
                            echo "Quality Gate passed"
                        }
                    }
                }
            }
        }
        stage('Fetch SonarQube Report Data') {
            steps {
                script {
                    try {
                        withSonarQubeEnv('SonarQube-Server') {
                            def getMetricValue = { measures, metricName, fallback = '0' ->
                                def measure = measures.find { it.metric == metricName }
                                if (!measure) {
                                    return fallback
                                }

                                def rawValue = measure.value
                                if (rawValue == null || rawValue == '') {
                                    if (measure.period?.value != null && measure.period.value != '') {
                                        rawValue = measure.period.value
                                    } else if (measure.periods?.size() > 0) {
                                        def period = measure.periods.find { it.index == 1 } ?: measure.periods.first()
                                        rawValue = period?.value
                                    }
                                }

                                return (rawValue == null || rawValue == '') ? fallback : rawValue.toString()
                            }

                            // 1. Fetch Overall + New Metrics
                            def metricsResponse = sh(
                                script: """
                                    curl --fail --silent --show-error \
                                        -H 'Accept: application/json' \
                                        -u ${env.SONAR_AUTH_TOKEN}: \
                                        "${env.SONAR_HOST}/api/measures/component?component=${env.SONAR_PROJECT_KEY}&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,ncloc,alert_status,security_hotspots,new_bugs,new_vulnerabilities,new_code_smells,new_security_hotspots,new_coverage"
                                """,
                                returnStdout: true
                            ).trim()

                            echo "========== RAW SONAR RESPONSE =========="
                            echo metricsResponse
                            echo "========================================"

                            // Parse JSON
                            def metricsJson = readJSON text: metricsResponse, returnPojo: true
                            def measures = metricsJson.component?.measures ?: []

                            if (measures.isEmpty()) {
                                error("SonarQube API did not return any measures.")
                            }

                            // Build metric map
                            def metricMap = [:]
                            measures.each { measure ->
                                def rawValue = measure.value
                                if (rawValue == null || rawValue == '') {
                                    if (measure.period?.value != null && measure.period.value != '') {
                                        rawValue = measure.period.value
                                    } else if (measure.periods?.size() > 0) {
                                        def period = measure.periods.find { it.index == 1 } ?: measure.periods.first()
                                        rawValue = period?.value
                                    }
                                }
                                metricMap[measure.metric] = (rawValue == null || rawValue == '') ? '0' : rawValue.toString()
                            }

                            // Console Summary
                            echo ""
                            echo "========== SONAR METRICS =========="
                            metricMap.each { key, value ->
                                echo String.format("%-30s : %s", key, value)
                            }
                            echo "==================================="

                            // Overall Metrics
                            def sonarSummary = [:]
                            sonarSummary.bugs            = getMetricValue(measures, 'bugs', '0')
                            sonarSummary.vulnerabilities = getMetricValue(measures, 'vulnerabilities', '0')
                            sonarSummary.codeSmells      = getMetricValue(measures, 'code_smells', '0')
                            sonarSummary.coverage        = getMetricValue(measures, 'coverage', '0.0')
                            sonarSummary.duplication     = getMetricValue(measures, 'duplicated_lines_density', '0.0')
                            sonarSummary.lines           = getMetricValue(measures, 'ncloc', '0')
                            sonarSummary.status          = getMetricValue(measures, 'alert_status', 'UNKNOWN')
                            sonarSummary.hotspots        = getMetricValue(measures, 'security_hotspots', '0')

                            // New Code Metrics
                            sonarSummary.newBugs            = getMetricValue(measures, 'new_bugs', '0')
                            sonarSummary.newVulnerabilities = getMetricValue(measures, 'new_vulnerabilities', '0')
                            sonarSummary.newCodeSmells      = getMetricValue(measures, 'new_code_smells', '0')
                            sonarSummary.newHotspots        = getMetricValue(measures, 'new_security_hotspots', '0')
                            sonarSummary.newCoverage        = getMetricValue(measures, 'new_coverage', '0.0')

                            env.SONAR_BUGS            = sonarSummary.bugs
                            env.SONAR_VULNERABILITIES = sonarSummary.vulnerabilities
                            env.SONAR_CODE_SMELLS     = sonarSummary.codeSmells
                            env.SONAR_COVERAGE        = sonarSummary.coverage
                            env.SONAR_DUPLICATION     = sonarSummary.duplication
                            env.SONAR_LINES           = sonarSummary.lines
                            env.SONAR_STATUS          = sonarSummary.status
                            env.SONAR_HOTSPOTS        = sonarSummary.hotspots
                            env.SONAR_NEW_BUGS            = sonarSummary.newBugs
                            env.SONAR_NEW_VULNERABILITIES = sonarSummary.newVulnerabilities
                            env.SONAR_NEW_CODE_SMELLS     = sonarSummary.newCodeSmells
                            env.SONAR_NEW_HOTSPOTS        = sonarSummary.newHotspots
                            env.SONAR_NEW_COVERAGE        = sonarSummary.newCoverage

                            // Final Summary
                            echo ""
                            echo "========== FINAL SUMMARY =========="
                            echo "Quality Gate     : ${sonarSummary.status}"
                            echo "Coverage         : ${sonarSummary.coverage}%"
                            echo "Code Smells      : ${sonarSummary.codeSmells}"
                            echo "Bugs             : ${sonarSummary.bugs}"
                            echo "Vulnerabilities  : ${sonarSummary.vulnerabilities}"
                            echo "Hotspots         : ${sonarSummary.hotspots}"
                            echo "LOC              : ${sonarSummary.lines}"
                            echo "Duplication      : ${sonarSummary.duplication}%"
                            echo "New Bugs         : ${sonarSummary.newBugs}"
                            echo "New Vulns        : ${sonarSummary.newVulnerabilities}"
                            echo "New Smells       : ${sonarSummary.newCodeSmells}"
                            echo "New Hotspots     : ${sonarSummary.newHotspots}"
                            echo "New Coverage     : ${sonarSummary.newCoverage}%"
                            echo "==================================="

                            // 2. Fetch Severity Breakdown
                            def issueResponse = sh(
                                script: """
                                    curl --fail --silent --show-error \
                                        -H 'Accept: application/json' \
                                        -u ${env.SONAR_AUTH_TOKEN}: \
                                        "${env.SONAR_HOST}/api/issues/search?componentKeys=${env.SONAR_PROJECT_KEY}&facets=severities&ps=100"
                                """,
                                returnStdout: true
                            ).trim()

                            def issueJson = readJSON text: issueResponse, returnPojo: true

                            echo ""
                            echo "========== RAW ISSUE RESPONSE =========="
                            echo issueResponse
                            echo "========================================"

                            echo ""
                            echo "========== DEBUG SEVERITY PARSING =========="
                            echo "Full Response: ${issueJson}"
                            echo "Facets Exists: ${issueJson.facets != null}"
                            echo "Facets Type: ${issueJson.facets?.getClass()}"
                            echo "Facets Size: ${issueJson.facets?.size()}"
                            echo "============================================"

                            def severityMap = ['BLOCKER': '0', 'CRITICAL': '0', 'MAJOR': '0', 'MINOR': '0', 'INFO': '0']

                            // Try to parse from facets if available
                            def facetsParsed = false
                            if (issueJson.facets && issueJson.facets.size() > 0) {
                                echo "Attempting to parse facets..."
                                try {
                                    issueJson.facets.each { facet ->
                                        echo "  Checking facet: ${facet.property}"
                                        if (facet.property == 'severities' && facet.values) {
                                            echo "  Found severities facet with ${facet.values.size()} entries"
                                            facet.values.each { entry ->
                                                def severity = entry.val ?: entry.value
                                                def count = entry.count
                                                echo "    Severity: ${severity} = ${count}"
                                                if (severity && count != null) {
                                                    severityMap[severity] = count.toString()
                                                    facetsParsed = true
                                                }
                                            }
                                        }
                                    }
                                } catch (Exception e) {
                                    echo "  Error parsing facets: ${e.message}"
                                }
                            }

                            echo "Facets parsed successfully: ${facetsParsed}"

                            // Fallback: count from issues array if facets didn't work
                            if (!facetsParsed && issueJson.issues) {
                                echo "Fallback: counting from issues array (${issueJson.issues.size()} issues)..."
                                def issueCounts = [:]
                                issueJson.issues.each { issue ->
                                    def severity = issue.severity
                                    if (severity) {
                                        issueCounts[severity] = (issueCounts[severity] ?: 0) + 1
                                        echo "  Issue severity: ${severity}"
                                    }
                                }
                                echo "Issue counts: ${issueCounts}"
                                issueCounts.each { severity, count ->
                                    severityMap[severity] = count.toString()
                                }
                            }

                            echo "Final severity map: ${severityMap}"

                            // Set environment variables
                            env.SONAR_BLOCKER  = severityMap['BLOCKER'] ?: '0'
                            env.SONAR_CRITICAL = severityMap['CRITICAL'] ?: '0'
                            env.SONAR_MAJOR    = severityMap['MAJOR'] ?: '0'
                            env.SONAR_MINOR    = severityMap['MINOR'] ?: '0'
                            env.SONAR_INFO     = severityMap['INFO'] ?: '0'

                            echo ""
                            echo "========== SEVERITY BREAKDOWN =========="
                            echo "Blocker  : ${env.SONAR_BLOCKER}"
                            echo "Critical : ${env.SONAR_CRITICAL}"
                            echo "Major    : ${env.SONAR_MAJOR}"
                            echo "Minor    : ${env.SONAR_MINOR}"
                            echo "Info     : ${env.SONAR_INFO}"
                            echo "========================================"
                        }

                    } catch (Exception e) {
                        echo "WARNING: Could not fetch SonarQube metrics: ${e.message}"
                        // Defaults remain
                    }
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Determine build status and styling
                def buildStatus = currentBuild.currentResult
                def statusColor, statusText, statusIcon, alertClass, alertMessage

                if (buildStatus == 'SUCCESS') {
                    statusColor = '28a745'
                    statusText = 'PASSED'
                    statusIcon = 'PASSED'
                    alertClass = 'alert-success'
                    alertMessage = 'All quality checks passed. No action required.'
                } else if (buildStatus == 'UNSTABLE') {
                    statusColor = 'fd7e14'
                    statusText = 'QUALITY GATE FAILED'
                    statusIcon = 'WARNING'
                    alertClass = 'alert-warning'
                    alertMessage = 'The SonarQube Quality Gate did not pass. Please review the new issues below.'
                } else {
                    statusColor = 'dc3545'
                    statusText = 'BUILD FAILED'
                    statusIcon = 'FAILED'
                    alertClass = 'alert-fail'
                    alertMessage = 'The pipeline failed. Report shows the latest available scan data.'
                }

                // Calculate total new issues
                def totalNewIssues = 0
                try {
                    totalNewIssues = (env.SONAR_NEW_BUGS.toInteger() + env.SONAR_NEW_VULNERABILITIES.toInteger() + env.SONAR_NEW_CODE_SMELLS.toInteger() + env.SONAR_NEW_HOTSPOTS.toInteger())
                } catch (e) {
                    totalNewIssues = 0
                }

                // Determine new issues alert style
                def newIssuesAlert = ''
                if (totalNewIssues > 0) {
                    newIssuesAlert = "<div class='alert-new-issues'><strong>New Issues Detected:</strong> ${totalNewIssues} new issue(s) found in this commit. Please review before merging.</div>"
                }

                def safeValue = { value, fallback = 'N/A' ->
                    value == null || value == '' ? fallback : value.toString()
                }

                def summaryRowsHtml = [
                    ['Quality Gate', safeValue(env.SONAR_STATUS, 'UNKNOWN')],
                    ['Coverage', "${safeValue(env.SONAR_COVERAGE, '0.0')}%"],
                    ['Code Smells', safeValue(env.SONAR_CODE_SMELLS, '0')],
                    ['Bugs', safeValue(env.SONAR_BUGS, '0')],
                    ['Vulnerabilities', safeValue(env.SONAR_VULNERABILITIES, '0')],
                    ['Hotspots', safeValue(env.SONAR_HOTSPOTS, '0')],
                    ['LOC', safeValue(env.SONAR_LINES, '0')],
                    ['Duplication', "${safeValue(env.SONAR_DUPLICATION, '0.0')}%"],
                    ['New Bugs', safeValue(env.SONAR_NEW_BUGS, '0')],
                    ['New Vulnerabilities', safeValue(env.SONAR_NEW_VULNERABILITIES, '0')],
                    ['New Code Smells', safeValue(env.SONAR_NEW_CODE_SMELLS, '0')],
                    ['New Hotspots', safeValue(env.SONAR_NEW_HOTSPOTS, '0')],
                    ['New Coverage', "${safeValue(env.SONAR_NEW_COVERAGE, '0.0')}%"],
                ].collect { row ->
                    "<tr><td>${row[0]}</td><td><strong>${row[1]}</strong></td></tr>"
                }.join('')

                // Send comprehensive email report
                emailext (
                    subject: "[${statusIcon}] SonarQube Report: ${env.JOB_NAME} #${env.BUILD_NUMBER} - ${statusText}",
                    body: """
                    <html>
                    <head>
                        <style>
                            body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; }
                            .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden; }
                            .header { background-color: #${statusColor}; color: white; padding: 30px; text-align: center; }
                            .header h1 { margin: 0; font-size: 26px; font-weight: 600; }
                            .header .status-badge { display: inline-block; background: rgba(255,255,255,0.25); padding: 8px 20px; border-radius: 25px; margin-top: 12px; font-size: 14px; font-weight: bold; letter-spacing: 0.5px; }
                            .content { padding: 30px; }
                            
                            .alert { padding: 14px 18px; border-radius: 6px; margin-bottom: 22px; font-size: 14px; line-height: 1.5; }
                            .alert-success { background: #d4edda; border-left: 4px solid #28a745; color: #155724; }
                            .alert-warning { background: #fff3cd; border-left: 4px solid #fd7e14; color: #856404; }
                            .alert-fail { background: #f8d7da; border-left: 4px solid #dc3545; color: #721c24; }
                            .alert-new-issues { background: #fff3cd; border: 2px solid #fd7e14; color: #856404; padding: 14px 18px; border-radius: 6px; margin: 20px 0; font-weight: 500; }
                            
                            h3 { color: #2c3e50; margin-top: 28px; margin-bottom: 15px; font-size: 18px; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; }
                            h3:first-of-type { margin-top: 0; }
                            
                            table.info { width: 100%; margin-bottom: 20px; border-collapse: collapse; font-size: 14px; }
                            table.info td { padding: 10px 12px; border-bottom: 1px solid #e9ecef; }
                            table.info td:first-child { font-weight: 600; width: 32%; color: #495057; }
                            
                            .summary { display: flex; justify-content: space-between; flex-wrap: wrap; margin-bottom: 10px; }
                            .metric-box { text-align: center; padding: 20px 10px; border-radius: 8px; background: #f8f9fa; flex: 1; margin: 6px; min-width: 110px; border-top: 4px solid #dee2e6; transition: transform 0.2s; }
                            .metric-value { font-size: 30px; font-weight: 700; }
                            .metric-label { font-size: 11px; color: #6c757d; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
                            
                            .bugs { border-color: #dc3545; color: #dc3545; }
                            .vulns { border-color: #dc3545; color: #dc3545; }
                            .smells { border-color: #fd7e14; color: #fd7e14; }
                            .coverage { border-color: #28a745; color: #28a745; }
                            .neutral { border-color: #6c757d; color: #495057; }
                            .new-highlight { border-color: #fd7e14; background: #fff8e1; }
                            
                            .severity-row { display: flex; justify-content: space-between; margin-top: 10px; }
                            .severity-item { text-align: center; padding: 12px 8px; border-radius: 6px; background: #f8f9fa; flex: 1; margin: 4px; }
                            .severity-count { font-size: 22px; font-weight: 700; }
                            .severity-name { font-size: 11px; color: #6c757d; margin-top: 4px; text-transform: uppercase; }
                            .sev-blocker { color: #dc3545; }
                            .sev-critical { color: #dc3545; }
                            .sev-major { color: #fd7e14; }
                            .sev-minor { color: #6c757d; }
                            .sev-info { color: #17a2b8; }
                            
                            .links { margin-top: 28px; padding-top: 22px; border-top: 2px solid #e9ecef; text-align: center; }
                            .btn { display: inline-block; padding: 10px 22px; margin: 5px; border-radius: 5px; text-decoration: none; color: white; font-size: 13px; font-weight: 500; transition: opacity 0.2s; }
                            .btn:hover { opacity: 0.85; }
                            .btn-primary { background: #337ab7; }
                            .btn-success { background: #28a745; }
                            .btn-warning { background: #fd7e14; }
                            .btn-danger { background: #dc3545; }
                            .btn-dark { background: #495057; }
                            
                            .footer { background: #f8f9fa; padding: 18px; text-align: center; font-size: 12px; color: #adb5bd; border-top: 1px solid #e9ecef; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>SonarQube Analysis Report</h1>
                                <div class="status-badge">${statusIcon} ${statusText}</div>
                            </div>
                            
                            <div class="content">
                                <div class="${alertClass}">
                                    ${alertMessage}
                                </div>
                                
                                ${newIssuesAlert}
                                
                                <h3>Build Information</h3>
                                <table class="info">
                                    <tr><td>Project</td><td>${env.JOB_NAME}</td></tr>
                                    <tr><td>Build Number</td><td>#${env.BUILD_NUMBER}</td></tr>
                                    <tr><td>Commit</td><td>${env.GIT_COMMIT?.take(7) ?: 'N/A'}</td></tr>
                                    <tr><td>Branch</td><td>${env.GIT_BRANCH ?: 'main'}</td></tr>
                                    <tr><td>Build Status</td><td><strong style="color: #${statusColor};">${statusText}</strong></td></tr>
                                    <tr><td>Quality Gate</td><td><strong>${env.SONAR_STATUS}</strong></td></tr>
                                    <tr><td>Duration</td><td>${currentBuild.durationString}</td></tr>
                                </table>

                                <h3>New Issues (Introduced in This Commit)</h3>
                                <div class="summary">
                                    <div class="metric-box new-highlight">
                                        <div class="metric-value">${env.SONAR_NEW_BUGS}</div>
                                        <div class="metric-label">New Bugs</div>
                                    </div>
                                    <div class="metric-box new-highlight">
                                        <div class="metric-value">${env.SONAR_NEW_VULNERABILITIES}</div>
                                        <div class="metric-label">New Vulnerabilities</div>
                                    </div>
                                    <div class="metric-box new-highlight">
                                        <div class="metric-value">${env.SONAR_NEW_CODE_SMELLS}</div>
                                        <div class="metric-label">New Code Smells</div>
                                    </div>
                                    <div class="metric-box new-highlight">
                                        <div class="metric-value">${env.SONAR_NEW_HOTSPOTS}</div>
                                        <div class="metric-label">New Hotspots</div>
                                    </div>
                                </div>

                                <h3>Final Summary</h3>
                                <table class="info">
                                    ${summaryRowsHtml}
                                </table>

                                <h3>Overall Code Quality Metrics</h3>
                                <div class="summary">
                                    <div class="metric-box bugs">
                                        <div class="metric-value">${env.SONAR_BUGS ?: '0'}</div>
                                        <div class="metric-label">Total Bugs</div>
                                    </div>
                                    <div class="metric-box vulns">
                                        <div class="metric-value">${env.SONAR_VULNERABILITIES ?: '0'}</div>
                                        <div class="metric-label">Total Vulnerabilities</div>
                                    </div>
                                    <div class="metric-box smells">
                                        <div class="metric-value">${env.SONAR_CODE_SMELLS ?: '0'}</div>
                                        <div class="metric-label">Total Code Smells</div>
                                    </div>
                                    <div class="metric-box coverage">
                                        <div class="metric-value">${env.SONAR_COVERAGE ?: '0.0'}%</div>
                                        <div class="metric-label">Coverage</div>
                                    </div>
                                </div>

                                <div class="summary">
                                    <div class="metric-box neutral">
                                        <div class="metric-value">${env.SONAR_HOTSPOTS ?: '0'}</div>
                                        <div class="metric-label">Security Hotspots</div>
                                    </div>
                                    <div class="metric-box neutral">
                                        <div class="metric-value">${env.SONAR_DUPLICATION ?: '0.0'}%</div>
                                        <div class="metric-label">Duplication</div>
                                    </div>
                                    <div class="metric-box neutral">
                                        <div class="metric-value">${env.SONAR_LINES ?: '0'}</div>
                                        <div class="metric-label">Lines of Code</div>
                                    </div>
                                </div>

                                <h3>Issue Severity Breakdown</h3>
                                <div class="severity-row">
                                    <div class="severity-item">
                                        <div class="severity-count sev-blocker">${env.SONAR_BLOCKER}</div>
                                        <div class="severity-name">Blocker</div>
                                    </div>
                                    <div class="severity-item">
                                        <div class="severity-count sev-critical">${env.SONAR_CRITICAL}</div>
                                        <div class="severity-name">Critical</div>
                                    </div>
                                    <div class="severity-item">
                                        <div class="severity-count sev-major">${env.SONAR_MAJOR}</div>
                                        <div class="severity-name">Major</div>
                                    </div>
                                    <div class="severity-item">
                                        <div class="severity-count sev-minor">${env.SONAR_MINOR}</div>
                                        <div class="severity-name">Minor</div>
                                    </div>
                                    <div class="severity-item">
                                        <div class="severity-count sev-info">${env.SONAR_INFO}</div>
                                        <div class="severity-name">Info</div>
                                    </div>
                                </div>

                                <div class="links">
                                    <h3>Quick Links</h3>
                                    <a href="${SONAR_HOST}/dashboard?id=${SONAR_PROJECT_KEY}" class="btn btn-primary">Dashboard</a>
                                    <a href="${SONAR_HOST}/component_measures?id=${SONAR_PROJECT_KEY}" class="btn btn-success">Metrics</a>
                                    <a href="${SONAR_HOST}/project/issues?id=${SONAR_PROJECT_KEY}&resolved=false" class="btn btn-warning">All Issues</a>
                                    <a href="${SONAR_HOST}/project/issues?id=${SONAR_PROJECT_KEY}&resolved=false&sinceLeakPeriod=true" class="btn btn-danger">New Issues</a>
                                    <a href="${SONAR_HOST}/security_hotspots?id=${SONAR_PROJECT_KEY}" class="btn btn-dark">Hotspots</a>
                                    <br><br>
                                    <a href="${env.BUILD_URL}console" class="btn btn-primary">Jenkins Console</a>
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
                    from: 'sathish.s@vimatch.in',
                    mimeType: 'text/html',
                    attachLog: true
                )
            }
            cleanWs()
        }
    }
}
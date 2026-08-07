@Library('sonar-pdf-reports') _

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
                    // Declare maps at script scope - they'll persist through withSonarQubeEnv
                    def sonarData = [:]
                    def severityData = [:]
                    
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

                            // Store in outer-scope map that persists after withSonarQubeEnv
                            sonarData.bugs = sonarSummary.bugs
                            sonarData.vulnerabilities = sonarSummary.vulnerabilities
                            sonarData.codeSmells = sonarSummary.codeSmells
                            sonarData.coverage = sonarSummary.coverage
                            sonarData.duplication = sonarSummary.duplication
                            sonarData.lines = sonarSummary.lines
                            sonarData.status = sonarSummary.status
                            sonarData.hotspots = sonarSummary.hotspots
                            sonarData.newBugs = sonarSummary.newBugs
                            sonarData.newVulnerabilities = sonarSummary.newVulnerabilities
                            sonarData.newCodeSmells = sonarSummary.newCodeSmells
                            sonarData.newHotspots = sonarSummary.newHotspots
                            sonarData.newCoverage = sonarSummary.newCoverage

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

                            // Set environment variables and store in outer-scope map
                            env.SONAR_BLOCKER  = severityMap['BLOCKER'] ?: '0'
                            env.SONAR_CRITICAL = severityMap['CRITICAL'] ?: '0'
                            env.SONAR_MAJOR    = severityMap['MAJOR'] ?: '0'
                            env.SONAR_MINOR    = severityMap['MINOR'] ?: '0'
                            env.SONAR_INFO     = severityMap['INFO'] ?: '0'
                            
                            severityData.BLOCKER = severityMap['BLOCKER'] ?: '0'
                            severityData.CRITICAL = severityMap['CRITICAL'] ?: '0'
                            severityData.MAJOR = severityMap['MAJOR'] ?: '0'
                            severityData.MINOR = severityMap['MINOR'] ?: '0'
                            severityData.INFO = severityMap['INFO'] ?: '0'

                            echo ""
                            echo "========== SEVERITY BREAKDOWN =========="
                            echo "Blocker  : ${env.SONAR_BLOCKER}"
                            echo "Critical : ${env.SONAR_CRITICAL}"
                            echo "Major    : ${env.SONAR_MAJOR}"
                            echo "Minor    : ${env.SONAR_MINOR}"
                            echo "Info     : ${env.SONAR_INFO}"
                            echo "========================================"
                        }

                        // ASSIGN ALL ENV VARS OUTSIDE withSonarQubeEnv BLOCK
                        echo ""
                        echo "========== PERSISTING TO ENV VARS ==========="
                        echo "DEBUG: sonarData map = ${sonarData}"
                        echo "DEBUG: sonarData.bugs = ${sonarData.bugs}"
                        echo "DEBUG: sonarData.codeSmells = ${sonarData.codeSmells}"
                        echo "DEBUG: severityData map = ${severityData}"
                        echo "DEBUG: severityData.BLOCKER = ${severityData.BLOCKER}"
                        echo "DEBUG: severityData.MAJOR = ${severityData.MAJOR}"
                        echo ""
                        env.SONAR_BUGS = sonarData.bugs ?: '0'
                        env.SONAR_VULNERABILITIES = sonarData.vulnerabilities ?: '0'
                        env.SONAR_CODE_SMELLS = sonarData.codeSmells ?: '0'
                        env.SONAR_COVERAGE = sonarData.coverage ?: '0.0'
                        env.SONAR_DUPLICATION = sonarData.duplication ?: '0.0'
                        env.SONAR_LINES = sonarData.lines ?: '0'
                        env.SONAR_STATUS = sonarData.status ?: 'UNKNOWN'
                        env.SONAR_HOTSPOTS = sonarData.hotspots ?: '0'
                        env.SONAR_NEW_BUGS = sonarData.newBugs ?: '0'
                        env.SONAR_NEW_VULNERABILITIES = sonarData.newVulnerabilities ?: '0'
                        env.SONAR_NEW_CODE_SMELLS = sonarData.newCodeSmells ?: '0'
                        env.SONAR_NEW_HOTSPOTS = sonarData.newHotspots ?: '0'
                        env.SONAR_NEW_COVERAGE = sonarData.newCoverage ?: '0.0'
                        
                        echo "DEBUG BEFORE severity assignment:"
                        echo "  severityData.BLOCKER type: ${severityData.BLOCKER?.class?.name}"
                        echo "  severityData.BLOCKER value: '${severityData.BLOCKER}'"
                        echo "  Will assign to env.SONAR_BLOCKER: ${severityData.BLOCKER ?: '0'}"
                        
                        env.SONAR_BLOCKER = severityData.BLOCKER ?: '0'
                        env.SONAR_CRITICAL = severityData.CRITICAL ?: '0'
                        env.SONAR_MAJOR = severityData.MAJOR ?: '0'
                        env.SONAR_MINOR = severityData.MINOR ?: '0'
                        env.SONAR_INFO = severityData.INFO ?: '0'
                        
                        echo "DEBUG AFTER severity assignment:"
                        echo "  env.SONAR_BLOCKER = '${env.SONAR_BLOCKER}'"
                        echo "  env.SONAR_MAJOR = '${env.SONAR_MAJOR}'"
                        
                        echo "FINAL VALUES:"
                        echo "  SONAR_BUGS = ${env.SONAR_BUGS}"
                        echo "  SONAR_BLOCKER = ${env.SONAR_BLOCKER}"
                        echo "  SONAR_MAJOR = ${env.SONAR_MAJOR}"
                        echo "============================================"

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
                sonarNativePdfReport(
                    recipientEmail: 'ovt.bangalore@gmail.com',
                    fromEmail: 'sathish.s@vimatch.in'
                )
            }
            cleanWs()
        }
    }
}
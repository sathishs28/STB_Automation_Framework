@Library('sonar-pdf-reports') _

pipeline {
    agent any

    environment {
        // ─── Static config only ───
        SONARQUBE_SERVER  = 'SonarQube-Server'
        SONAR_PROJECT_KEY = 'STB_Automation_Framework'
        SONAR_PROJECT_NAME = 'STB Automation Framework'
        SCANNER_HOME      = tool 'SonarQube-Scanner'
        SONAR_HOST        = 'http://192.168.0.5:9000'
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
                    def sonarData    = [:]
                    def severityData = [:]

                    try {
                        withSonarQubeEnv('SonarQube-Server') {

                            def getMetricValue = { measures, metricName, fallback = '0' ->
                                def measure = measures.find { it.metric == metricName }
                                if (!measure) return fallback

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

                            // ─── 1. Fetch Overall + New Metrics ───
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

                            echo ""
                            echo "========== SONAR METRICS =========="
                            metricMap.each { key, value ->
                                echo String.format("%-30s : %s", key, value)
                            }
                            echo "==================================="

                            // ─── Store in maps ───
                            sonarData.bugs            = getMetricValue(measures, 'bugs', '0')
                            sonarData.vulnerabilities = getMetricValue(measures, 'vulnerabilities', '0')
                            sonarData.codeSmells      = getMetricValue(measures, 'code_smells', '0')
                            sonarData.coverage        = getMetricValue(measures, 'coverage', '0.0')
                            sonarData.duplication     = getMetricValue(measures, 'duplicated_lines_density', '0.0')
                            sonarData.lines           = getMetricValue(measures, 'ncloc', '0')
                            sonarData.status          = getMetricValue(measures, 'alert_status', 'UNKNOWN')
                            sonarData.hotspots        = getMetricValue(measures, 'security_hotspots', '0')

                            sonarData.newBugs            = getMetricValue(measures, 'new_bugs', '0')
                            sonarData.newVulnerabilities = getMetricValue(measures, 'new_vulnerabilities', '0')
                            sonarData.newCodeSmells      = getMetricValue(measures, 'new_code_smells', '0')
                            sonarData.newHotspots        = getMetricValue(measures, 'new_security_hotspots', '0')
                            sonarData.newCoverage        = getMetricValue(measures, 'new_coverage', '0.0')

                            echo ""
                            echo "========== FINAL SUMMARY =========="
                            echo "Quality Gate     : ${sonarData.status}"
                            echo "Coverage         : ${sonarData.coverage}%"
                            echo "Code Smells      : ${sonarData.codeSmells}"
                            echo "Bugs             : ${sonarData.bugs}"
                            echo "Vulnerabilities  : ${sonarData.vulnerabilities}"
                            echo "Hotspots         : ${sonarData.hotspots}"
                            echo "LOC              : ${sonarData.lines}"
                            echo "Duplication      : ${sonarData.duplication}%"
                            echo "New Bugs         : ${sonarData.newBugs}"
                            echo "New Vulns        : ${sonarData.newVulnerabilities}"
                            echo "New Smells       : ${sonarData.newCodeSmells}"
                            echo "New Hotspots     : ${sonarData.newHotspots}"
                            echo "New Coverage     : ${sonarData.newCoverage}%"
                            echo "==================================="

                            // ─── 2. Fetch Severity Breakdown ───
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

                            def severityMap = ['BLOCKER': '0', 'CRITICAL': '0', 'MAJOR': '0', 'MINOR': '0', 'INFO': '0']
                            def facetsParsed = false

                            if (issueJson.facets && issueJson.facets.size() > 0) {
                                issueJson.facets.each { facet ->
                                    if (facet.property == 'severities' && facet.values) {
                                        facet.values.each { entry ->
                                            def severity = entry.val ?: entry.value
                                            def count = entry.count
                                            if (severity && count != null) {
                                                severityMap[severity] = count.toString()
                                                facetsParsed = true
                                            }
                                        }
                                    }
                                }
                            }

                            if (!facetsParsed && issueJson.issues) {
                                def issueCounts = [:]
                                issueJson.issues.each { issue ->
                                    def severity = issue.severity
                                    if (severity) {
                                        issueCounts[severity] = (issueCounts[severity] ?: 0) + 1
                                    }
                                }
                                issueCounts.each { severity, count ->
                                    severityMap[severity] = count.toString()
                                }
                            }

                            echo "Final severity map: ${severityMap}"

                            severityData.BLOCKER  = severityMap['BLOCKER']  ?: '0'
                            severityData.CRITICAL = severityMap['CRITICAL'] ?: '0'
                            severityData.MAJOR    = severityMap['MAJOR']    ?: '0'
                            severityData.MINOR    = severityMap['MINOR']    ?: '0'
                            severityData.INFO     = severityMap['INFO']     ?: '0'

                            echo ""
                            echo "========== SEVERITY BREAKDOWN =========="
                            echo "Blocker  : ${severityData.BLOCKER}"
                            echo "Critical : ${severityData.CRITICAL}"
                            echo "Major    : ${severityData.MAJOR}"
                            echo "Minor    : ${severityData.MINOR}"
                            echo "Info     : ${severityData.INFO}"
                            echo "========================================"
                        }

                        // ─── Assign to env vars OUTSIDE withSonarQubeEnv ───
                        env.SONAR_BUGS              = sonarData.bugs            ?: '0'
                        env.SONAR_VULNERABILITIES   = sonarData.vulnerabilities ?: '0'
                        env.SONAR_CODE_SMELLS       = sonarData.codeSmells      ?: '0'
                        env.SONAR_COVERAGE          = sonarData.coverage        ?: '0.0'
                        env.SONAR_DUPLICATION       = sonarData.duplication     ?: '0.0'
                        env.SONAR_LINES             = sonarData.lines           ?: '0'
                        env.SONAR_STATUS            = sonarData.status          ?: 'UNKNOWN'
                        env.SONAR_HOTSPOTS          = sonarData.hotspots        ?: '0'
                        env.SONAR_NEW_BUGS          = sonarData.newBugs            ?: '0'
                        env.SONAR_NEW_VULNERABILITIES = sonarData.newVulnerabilities ?: '0'
                        env.SONAR_NEW_CODE_SMELLS   = sonarData.newCodeSmells      ?: '0'
                        env.SONAR_NEW_HOTSPOTS      = sonarData.newHotspots        ?: '0'
                        env.SONAR_NEW_COVERAGE      = sonarData.newCoverage        ?: '0.0'

                        env.SONAR_BLOCKER  = severityData.BLOCKER  ?: '0'
                        env.SONAR_CRITICAL = severityData.CRITICAL ?: '0'
                        env.SONAR_MAJOR    = severityData.MAJOR    ?: '0'
                        env.SONAR_MINOR    = severityData.MINOR    ?: '0'
                        env.SONAR_INFO     = severityData.INFO     ?: '0'

                        echo ""
                        echo "========== PERSISTED ENV VARS =========="
                        echo "SONAR_BUGS        = ${env.SONAR_BUGS}"
                        echo "SONAR_BLOCKER     = ${env.SONAR_BLOCKER}"
                        echo "SONAR_CRITICAL    = ${env.SONAR_CRITICAL}"
                        echo "SONAR_MAJOR       = ${env.SONAR_MAJOR}"
                        echo "SONAR_MINOR       = ${env.SONAR_MINOR}"
                        echo "SONAR_INFO        = ${env.SONAR_INFO}"
                        echo "========================================"

                    } catch (Exception e) {
                        echo "WARNING: Could not fetch SonarQube metrics: ${e.message}"
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
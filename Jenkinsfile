@Library('sonar-pdf-reports') _

pipeline {

    agent {
    label 'docker-ci'
    }

    // =========================================================
    // ENVIRONMENT
    // =========================================================

    environment {

        // -----------------------------------------------------
        // SonarQube
        // -----------------------------------------------------
        SONARQUBE_SERVER   = 'SonarQube-Server'
        SONAR_PROJECT_KEY  = 'STB_Automation_Framework'
        SONAR_PROJECT_NAME = 'STB Automation Framework'

        SCANNER_HOME = tool 'SonarQube-Scanner'

        SONAR_HOST = 'http://192.168.0.5:9000'

        // -----------------------------------------------------
        // CI Docker Environment
        // -----------------------------------------------------
        CI_IMAGE = 'stb-automation-ci:1.0'

        // -----------------------------------------------------
        // Test Configuration
        // -----------------------------------------------------
        UNIT_TEST_DIR = 'tests/unit_mock_tests'

        // -----------------------------------------------------
        // CI Installation dependencies - requirements.txt
        // -----------------------------------------------------
        REQUIREMENTS_FILE = 'requirements-ci.txt'
    }

    // =========================================================
    // TRIGGERS
    // =========================================================

    triggers {
        pollSCM('H/5 * * * *')
    }

    // =========================================================
    // OPTIONS
    // =========================================================

    options {

        buildDiscarder(
            logRotator(
                numToKeepStr: '10'
            )
        )

        timeout(
            time: 15,
            unit: 'MINUTES'
        )

        timestamps()

        disableConcurrentBuilds()
    }

    // =========================================================
    // STAGES
    // =========================================================

    stages {

        // =====================================================
        // 1. CHECKOUT
        // =====================================================

        stage('Checkout') {

            steps {

                echo '========================================='
                echo 'Checking out source code'
                echo '========================================='

                checkout scm
            }
        }


        // =====================================================
        // 2. VERIFY CI DOCKER ENVIRONMENT
        // =====================================================

        stage('Verify CI Environment') {

            steps {

                sh """
                    set -e

                    echo "========================================="
                    echo "CI Environment"
                    echo "========================================="

                    echo "Docker:"
                    docker --version

                    echo ""
                    echo "CI Image:"
                    echo "${CI_IMAGE}"

                    echo ""
                    echo "Checking CI image..."

                    docker image inspect ${CI_IMAGE} > /dev/null

                    echo ""
                    echo "Python version:"

                    docker run --rm \
                        ${CI_IMAGE} \
                        python --version

                    echo ""
                    echo "Pytest version:"

                    docker run --rm \
                        ${CI_IMAGE} \
                        pytest --version

                    echo ""
                    echo "CI environment verification completed."
                """
            }
        }


        // =====================================================
        // 3. RUN UNIT TESTS + COVERAGE
        // =====================================================

        stage('Unit Tests and Coverage') {

            steps {

                sh """

                    set -e

                    echo "========================================="
                    echo "Preparing test environment"
                    echo "========================================="

                    rm -f coverage.xml
                    rm -f test-results.xml
                    rm -f .coverage

                    rm -rf htmlcov


                    echo "========================================="
                    echo "Running Unit Tests inside CI Container"
                    echo "========================================="

                    docker run --rm \\
                        -v "\${WORKSPACE}:/workspace" \\
                        -w /workspace \\
                        ${CI_IMAGE} \\
                        bash -c '

                            set -e

                            echo "-----------------------------------------"
                            echo "Python"
                            echo "-----------------------------------------"

                            python --version

                            echo ""
                            echo "-----------------------------------------"
                            echo "Installing Project Dependencies"
                            echo "-----------------------------------------"

                            if [ -f ${REQUIREMENTS_FILE} ]; then

                                python -m pip install \\
                                    --no-cache-dir \\
                                    -r ${REQUIREMENTS_FILE}

                            else

                                echo "WARNING: ${REQUIREMENTS_FILE} not found."

                            fi


                            echo ""
                            echo "-----------------------------------------"
                            echo "Running Unit Tests"
                            echo "-----------------------------------------"

                            python -m pytest \\
                                ${UNIT_TEST_DIR} \\
                                -m unit \\
                                --cov=src \\
                                --cov-branch \\
                                --cov-report=term-missing \\
                                --cov-report=xml:coverage.xml \\
                                --cov-report=html:htmlcov \\
                                --junitxml=test-results.xml \\
                                -v


                            echo ""
                            echo "-----------------------------------------"
                            echo "Generated Reports"
                            echo "-----------------------------------------"

                            ls -lh coverage.xml
                            ls -lh test-results.xml

                        '

                    echo ""
                    echo "========================================="
                    echo "Unit Test Execution Completed"
                    echo "========================================="
                """
            }

            post {

                always {

                    echo 'Publishing unit test results...'

                    junit(
                        allowEmptyResults: true,
                        testResults: 'test-results.xml'
                    )

                    archiveArtifacts(
                        artifacts: 'coverage.xml',
                        allowEmptyArchive: true
                    )

                    archiveArtifacts(
                        artifacts: 'htmlcov/**',
                        allowEmptyArchive: true
                    )
                }
            }
        }


        // =====================================================
        // 4. VERIFY COVERAGE REPORT
        // =====================================================

        stage('Verify Coverage Report') {

            steps {

                sh '''

                    set -e

                    echo "========================================="
                    echo "Verifying Coverage Report"
                    echo "========================================="

                    if [ ! -f coverage.xml ]; then

                        echo "ERROR: coverage.xml was not generated."

                        exit 1

                    fi

                    echo ""
                    echo "Coverage report generated successfully."

                    ls -lh coverage.xml

                    echo ""
                    echo "Coverage report preview:"

                    head -n 10 coverage.xml

                '''
            }
        }


        // =====================================================
        // 5. SONARQUBE ANALYSIS
        // =====================================================

        stage('SonarQube Analysis') {

            steps {

                echo '========================================='
                echo 'Starting SonarQube Analysis'
                echo '========================================='

                withSonarQubeEnv('SonarQube-Server') {

                    sh """

                        set -e

                        ${SCANNER_HOME}/bin/sonar-scanner \\

                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \\

                            -Dsonar.projectName="${SONAR_PROJECT_NAME}" \\

                            -Dsonar.sources=. \\

                            -Dsonar.host.url=${env.SONAR_HOST_URL} \\

                            -Dsonar.token=${env.SONAR_AUTH_TOKEN}

                    """
                }
            }
        }


        // =====================================================
        // 6. SONARQUBE QUALITY GATE
        // =====================================================

        stage('Quality Gate') {

            steps {

                timeout(
                    time: 10,
                    unit: 'MINUTES'
                ) {

                    script {

                        echo '========================================='
                        echo 'Waiting for SonarQube Quality Gate'
                        echo '========================================='

                        def qualityGate = waitForQualityGate()

                        echo ""
                        echo "========================================="
                        echo "SonarQube Quality Gate: ${qualityGate.status}"
                        echo "========================================="

                        if (qualityGate.status != 'OK') {

                            error(
                                "SonarQube Quality Gate failed: " +
                                "${qualityGate.status}"
                            )
                        }

                        echo ""
                        echo "SonarQube Quality Gate PASSED."
                    }
                }
            }
        }


        // =====================================================
        // 7. FETCH SONARQUBE REPORT DATA
        // =====================================================

        stage('Fetch SonarQube Report Data') {

            steps {

                script {

                    def sonarData = [:]
                    def severityData = [:]

                    try {

                        withSonarQubeEnv('SonarQube-Server') {

                            // =================================================
                            // Metric Helper
                            // =================================================

                            def getMetricValue = {
                                measures,
                                metricName,
                                fallback = '0' ->

                                def measure =
                                    measures.find {
                                        it.metric == metricName
                                    }

                                if (!measure) {
                                    return fallback
                                }

                                def rawValue = measure.value

                                if (
                                    rawValue == null ||
                                    rawValue == ''
                                ) {

                                    if (
                                        measure.period?.value != null &&
                                        measure.period.value != ''
                                    ) {

                                        rawValue =
                                            measure.period.value

                                    } else if (
                                        measure.periods?.size() > 0
                                    ) {

                                        def period =
                                            measure.periods.find {
                                                it.index == 1
                                            } ?: measure.periods.first()

                                        rawValue =
                                            period?.value
                                    }
                                }

                                return (
                                    rawValue == null ||
                                    rawValue == ''
                                ) ? fallback :
                                    rawValue.toString()
                            }


                            // =================================================
                            // FETCH PROJECT METRICS
                            // =================================================

                            def metricsResponse = sh(

                                script: """

                                    curl --fail \
                                        --silent \
                                        --show-error \\
                                        -H 'Accept: application/json' \\
                                        -u ${env.SONAR_AUTH_TOKEN}: \\
                                        "${env.SONAR_HOST}/api/measures/component?component=${env.SONAR_PROJECT_KEY}&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,ncloc,alert_status,security_hotspots,new_bugs,new_vulnerabilities,new_code_smells,new_security_hotspots,new_coverage"

                                """,

                                returnStdout: true
                            ).trim()


                            echo ""
                            echo "========== RAW SONAR RESPONSE =========="
                            echo metricsResponse
                            echo "========================================="


                            def metricsJson =
                                readJSON(
                                    text: metricsResponse,
                                    returnPojo: true
                                )

                            def measures =
                                metricsJson.component?.measures ?: []


                            if (measures.isEmpty()) {

                                error(
                                    "SonarQube API did not return any measures."
                                )
                            }


                            // =================================================
                            // BUILD METRIC MAP
                            // =================================================

                            def metricMap = [:]

                            measures.each { measure ->

                                def rawValue =
                                    measure.value

                                if (
                                    rawValue == null ||
                                    rawValue == ''
                                ) {

                                    if (
                                        measure.period?.value != null &&
                                        measure.period.value != ''
                                    ) {

                                        rawValue =
                                            measure.period.value

                                    } else if (
                                        measure.periods?.size() > 0
                                    ) {

                                        def period =
                                            measure.periods.find {
                                                it.index == 1
                                            } ?: measure.periods.first()

                                        rawValue =
                                            period?.value
                                    }
                                }

                                metricMap[measure.metric] =
                                    (
                                        rawValue == null ||
                                        rawValue == ''
                                    ) ? '0' :
                                    rawValue.toString()
                            }


                            echo ""
                            echo "========== SONAR METRICS =========="

                            metricMap.each { key, value ->

                                echo String.format(
                                    "%-30s : %s",
                                    key,
                                    value
                                )
                            }

                            echo "==================================="


                            // =================================================
                            // STORE METRICS
                            // =================================================

                            sonarData.bugs =
                                getMetricValue(
                                    measures,
                                    'bugs',
                                    '0'
                                )

                            sonarData.vulnerabilities =
                                getMetricValue(
                                    measures,
                                    'vulnerabilities',
                                    '0'
                                )

                            sonarData.codeSmells =
                                getMetricValue(
                                    measures,
                                    'code_smells',
                                    '0'
                                )

                            sonarData.coverage =
                                getMetricValue(
                                    measures,
                                    'coverage',
                                    '0.0'
                                )

                            sonarData.duplication =
                                getMetricValue(
                                    measures,
                                    'duplicated_lines_density',
                                    '0.0'
                                )

                            sonarData.lines =
                                getMetricValue(
                                    measures,
                                    'ncloc',
                                    '0'
                                )

                            sonarData.status =
                                getMetricValue(
                                    measures,
                                    'alert_status',
                                    'UNKNOWN'
                                )

                            sonarData.hotspots =
                                getMetricValue(
                                    measures,
                                    'security_hotspots',
                                    '0'
                                )

                            sonarData.newBugs =
                                getMetricValue(
                                    measures,
                                    'new_bugs',
                                    '0'
                                )

                            sonarData.newVulnerabilities =
                                getMetricValue(
                                    measures,
                                    'new_vulnerabilities',
                                    '0'
                                )

                            sonarData.newCodeSmells =
                                getMetricValue(
                                    measures,
                                    'new_code_smells',
                                    '0'
                                )

                            sonarData.newHotspots =
                                getMetricValue(
                                    measures,
                                    'new_security_hotspots',
                                    '0'
                                )

                            sonarData.newCoverage =
                                getMetricValue(
                                    measures,
                                    'new_coverage',
                                    '0.0'
                                )


                            // =================================================
                            // FINAL SUMMARY
                            // =================================================

                            echo ""

                            echo "========== FINAL SUMMARY =========="

                            echo "Quality Gate      : ${sonarData.status}"
                            echo "Coverage          : ${sonarData.coverage}%"
                            echo "Code Smells       : ${sonarData.codeSmells}"
                            echo "Bugs              : ${sonarData.bugs}"
                            echo "Vulnerabilities   : ${sonarData.vulnerabilities}"
                            echo "Hotspots          : ${sonarData.hotspots}"
                            echo "LOC               : ${sonarData.lines}"
                            echo "Duplication       : ${sonarData.duplication}%"
                            echo "New Bugs          : ${sonarData.newBugs}"
                            echo "New Vulns         : ${sonarData.newVulnerabilities}"
                            echo "New Smells        : ${sonarData.newCodeSmells}"
                            echo "New Hotspots      : ${sonarData.newHotspots}"
                            echo "New Coverage      : ${sonarData.newCoverage}%"

                            echo "==================================="


                            // =================================================
                            // FETCH SEVERITY BREAKDOWN
                            // =================================================

                            def issueResponse = sh(

                                script: """

                                    curl --fail \
                                        --silent \
                                        --show-error \\
                                        -H 'Accept: application/json' \\
                                        -u ${env.SONAR_AUTH_TOKEN}: \\
                                        "${env.SONAR_HOST}/api/issues/search?componentKeys=${env.SONAR_PROJECT_KEY}&facets=severities&ps=100"

                                """,

                                returnStdout: true
                            ).trim()


                            def issueJson =
                                readJSON(
                                    text: issueResponse,
                                    returnPojo: true
                                )


                            echo ""
                            echo "========== RAW ISSUE RESPONSE =========="
                            echo issueResponse
                            echo "========================================="


                            def severityMap = [
                                'BLOCKER': '0',
                                'CRITICAL': '0',
                                'MAJOR': '0',
                                'MINOR': '0',
                                'INFO': '0'
                            ]


                            def facetsParsed = false


                            if (
                                issueJson.facets &&
                                issueJson.facets.size() > 0
                            ) {

                                issueJson.facets.each { facet ->

                                    if (
                                        facet.property == 'severities' &&
                                        facet.values
                                    ) {

                                        facet.values.each { entry ->

                                            def severity =
                                                entry.val ?: entry.value

                                            def count =
                                                entry.count

                                            if (
                                                severity &&
                                                count != null
                                            ) {

                                                severityMap[severity] =
                                                    count.toString()

                                                facetsParsed = true
                                            }
                                        }
                                    }
                                }
                            }


                            if (
                                !facetsParsed &&
                                issueJson.issues
                            ) {

                                def issueCounts = [:]

                                issueJson.issues.each { issue ->

                                    def severity =
                                        issue.severity

                                    if (severity) {

                                        issueCounts[severity] =
                                            (
                                                issueCounts[severity] ?: 0
                                            ) + 1
                                    }
                                }


                                issueCounts.each {
                                    severity,
                                    count ->

                                    severityMap[severity] =
                                        count.toString()
                                }
                            }


                            echo ""
                            echo "Final severity map:"
                            echo severityMap


                            severityData.BLOCKER =
                                severityMap['BLOCKER'] ?: '0'

                            severityData.CRITICAL =
                                severityMap['CRITICAL'] ?: '0'

                            severityData.MAJOR =
                                severityMap['MAJOR'] ?: '0'

                            severityData.MINOR =
                                severityMap['MINOR'] ?: '0'

                            severityData.INFO =
                                severityMap['INFO'] ?: '0'


                            echo ""
                            echo "========== SEVERITY BREAKDOWN =========="

                            echo "Blocker  : ${severityData.BLOCKER}"
                            echo "Critical : ${severityData.CRITICAL}"
                            echo "Major    : ${severityData.MAJOR}"
                            echo "Minor    : ${severityData.MINOR}"
                            echo "Info     : ${severityData.INFO}"

                            echo "========================================"
                        }


                        // =====================================================
                        // PERSIST ENVIRONMENT VARIABLES
                        // =====================================================

                        env.SONAR_BUGS =
                            sonarData.bugs ?: '0'

                        env.SONAR_VULNERABILITIES =
                            sonarData.vulnerabilities ?: '0'

                        env.SONAR_CODE_SMELLS =
                            sonarData.codeSmells ?: '0'

                        env.SONAR_COVERAGE =
                            sonarData.coverage ?: '0.0'

                        env.SONAR_DUPLICATION =
                            sonarData.duplication ?: '0.0'

                        env.SONAR_LINES =
                            sonarData.lines ?: '0'

                        env.SONAR_STATUS =
                            sonarData.status ?: 'UNKNOWN'

                        env.SONAR_HOTSPOTS =
                            sonarData.hotspots ?: '0'

                        env.SONAR_NEW_BUGS =
                            sonarData.newBugs ?: '0'

                        env.SONAR_NEW_VULNERABILITIES =
                            sonarData.newVulnerabilities ?: '0'

                        env.SONAR_NEW_CODE_SMELLS =
                            sonarData.newCodeSmells ?: '0'

                        env.SONAR_NEW_HOTSPOTS =
                            sonarData.newHotspots ?: '0'

                        env.SONAR_NEW_COVERAGE =
                            sonarData.newCoverage ?: '0.0'


                        env.SONAR_BLOCKER =
                            severityData.BLOCKER ?: '0'

                        env.SONAR_CRITICAL =
                            severityData.CRITICAL ?: '0'

                        env.SONAR_MAJOR =
                            severityData.MAJOR ?: '0'

                        env.SONAR_MINOR =
                            severityData.MINOR ?: '0'

                        env.SONAR_INFO =
                            severityData.INFO ?: '0'


                        // =====================================================
                        // PRINT PERSISTED VALUES
                        // =====================================================

                        echo ""

                        echo "========== PERSISTED ENV VARS =========="

                        echo "SONAR_BUGS       = ${env.SONAR_BUGS}"
                        echo "SONAR_BLOCKER    = ${env.SONAR_BLOCKER}"
                        echo "SONAR_CRITICAL   = ${env.SONAR_CRITICAL}"
                        echo "SONAR_MAJOR      = ${env.SONAR_MAJOR}"
                        echo "SONAR_MINOR      = ${env.SONAR_MINOR}"
                        echo "SONAR_INFO       = ${env.SONAR_INFO}"
                        echo "SONAR_COVERAGE   = ${env.SONAR_COVERAGE}"

                        echo "========================================"
                    }

                    catch (Exception e) {

                        echo(
                            "WARNING: Could not fetch SonarQube metrics: " +
                            "${e.message}"
                        )
                    }
                }
            }
        }
    }


    // =========================================================
    // POST BUILD ACTIONS
    // =========================================================

    post {

        success {

            echo '========================================='
            echo 'BUILD SUCCESSFUL'
            echo '========================================='

            echo 'All unit tests passed.'
            echo 'Coverage report generated.'
            echo 'SonarQube Quality Gate passed.'
        }


        failure {

            echo '========================================='
            echo 'BUILD FAILED'
            echo '========================================='

            echo 'Please check the failed stage.'
        }


        always {

            script {

                sonarNativePdfReport(
                    recipientEmail: 'sathish.s@vimatch.in',
                    fromEmail: 'camnex.alerts@gmail.com'
                )
            }

            cleanWs()
        }
    }
}
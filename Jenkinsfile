pipeline {
    agent any

    parameters {
        string(name: 'TARGET_REPO_URL', defaultValue: '', description: 'GitHub Repository URL to scan for IaC (e.g., https://github.com/user/repo.git). If left empty, scans the local terraform directory.')
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare Target') {
            steps {
                script {
                    if (params.TARGET_REPO_URL?.trim()) {
                        // Clean up old dir if exists
                        sh "rm -rf target_repo"
                        sh "git clone ${params.TARGET_REPO_URL} target_repo"
                        env.SCAN_DIR = "target_repo/"
                    } else {
                        env.SCAN_DIR = "terraform/"
                    }
                }
            }
        }

        stage('Security Validation Services') {
            parallel {
                stage('Primary Gate (Checkov)') {
                    steps {
                        sh 'checkov -d ${SCAN_DIR} --soft-fail'
                    }
                }
                stage('Async Deep Scan (LLM)') {
                    steps {
                        withCredentials([
                            string(credentialsId: 'GEMINI_API_KEY', variable: 'GEMINI_API_KEY'),
                            string(credentialsId: 'SLACK_WEBHOOK_URL', variable: 'SLACK_WEBHOOK_URL')
                        ]) {
                            sh 'python3.8 scripts/llm_async_client.py ${SCAN_DIR}'
                        }
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t llm-devsecops-app:latest .'
            }
        }

        stage('Verify Image') {
            steps {
                sh 'docker images | grep llm-devsecops-app'
            }
        }
    }
}
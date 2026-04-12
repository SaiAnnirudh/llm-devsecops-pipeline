pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
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

        stage('Security Validation Services') {
            parallel {
                stage('Primary Gate (Checkov)') {
                    steps {
                        sh 'checkov -d terraform/'
                    }
                }
                stage('Async Deep Scan (LLM)') {
                    steps {
                        withCredentials([string(credentialsId: 'OPENAI_API_KEY', variable: 'OPENAI_API_KEY')]) {
                            sh 'python3 scripts/llm_async_client.py terraform/'
                        }
                    }
                }
            }
        }
    }
}
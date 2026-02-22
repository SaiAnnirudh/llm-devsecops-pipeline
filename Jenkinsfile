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
    }
}
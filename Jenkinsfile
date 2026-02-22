pipeline {
    agent any

    options {
        timestamps()
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Cloning repository..."
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo "DevSecOps pipeline running 🚀"
            }
        }

    }

    post {

        success {
            slackSend(
                channel: "#devops",
                color: "good",
                message: "✅ SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                tokenCredentialId: "slack-webhook"
            )
        }

        failure {
            slackSend(
                channel: "#devops",
                color: "danger",
                message: "❌ FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                tokenCredentialId: "slack-webhook"
            )
        }

        unstable {
            slackSend(
                channel: "#devops",
                color: "warning",
                message: "⚠️ UNSTABLE: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                tokenCredentialId: "slack-webhook"
            )
        }

    }
}
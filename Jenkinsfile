pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo "DevSecOps pipeline running 🚀"
            }
        }
    }

    post {
        success {
            slackSend(
                color: 'good',
                message: "✅ SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "❌ FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
    }
}
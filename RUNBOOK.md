# DevSecOps Pipeline Runbook

This guide covers the complete, step-by-step process to run this project from scratch. It assumes you have a Windows machine (or WSL/Linux) with standard DevSecOps tools installed.

## Prerequisites
Ensure you have the following installed on your local machine or build server:
- **AWS CLI**: Configured with your AWS credentials (`aws configure`).
- **Terraform**: For infrastructure provisioning.
- **Ansible**: For configuration management (requires Python).
- **Jenkins**: Running locally or on a server, with Docker installed.
- **Docker & Docker Compose**: For building the app and running monitoring.
- **Python 3**: For running the LLM script locally if needed.

---

## Step 1: Provision Infrastructure (Terraform)
First, we need to create the underlying AWS infrastructure (VPC, EC2 instances) that this project manages.

1. Open your terminal and navigate to the `terraform` directory:
   ```bash
   cd terraform
   ```
2. Initialize Terraform (downloads AWS providers):
   ```bash
   terraform init
   ```
3. Review the infrastructure plan:
   ```bash
   terraform plan
   ```
4. Apply the configuration to create the resources in AWS:
   ```bash
   terraform apply -auto-approve
   ```
5. *Note the output IP addresses*. You will need these to configure Ansible.
6. # 1. Destroy the existing stopped instances so Terraform can recreate them cleanly
cd terraform
terraform destroy -target=aws_instance.jenkins -target=aws_instance.k8_master -target=aws_instance.k8_worker -auto-approve

# 2. Re-apply to create fresh instances with public IPs guaranteed
terraform apply -auto-approve

---

## Step 2: Configure Infrastructure (Ansible)
Once the EC2 instances are running, we use Ansible to configure them.

1. Navigate to the `ansible` directory:
   ```bash
   cd ../ansible
   ```
2. Update the `inventory.ini` file with the public IP addresses of the EC2 instances created by Terraform in Step 1.

wsl
# Inside WSL Ubuntu terminal:
sudo apt update && sudo apt install ansible -y


# Fix permissions (required, otherwise SSH will reject the key)
chmod 400 /mnt/c/Users/tssai/.ssh/llm-devsecops-key.pem

# Navigate to your ansible folder
cd /mnt/c/Users/tssai/llm-devsecops/ansible

# Run the playbook
ansible-playbook -i inventory.ini jenkins.yml \
  --private-key /mnt/c/Users/tssai/.ssh/llm-devsecops-key.pem \
  --ssh-common-args='-o StrictHostKeyChecking=no'


---

## Step 3: Configure Jenkins Credentials
Before running the Jenkins pipeline, Jenkins needs the API keys to communicate with Gemini and Slack.

1. Open your Jenkins Dashboard.

http://13.50.233.232:8080
jenkins ip

in wsl terminal paste this
ssh -i "C:\Users\tssai\.ssh\llm-devsecops-key.pem" ec2-user@13.50.233.232

if permission denied 
IN WINDOWS
# Step 1: Fix permissions
icacls "C:\Users\tssai\.ssh\llm-devsecops-key.pem" /inheritance:r /grant:r "$env:USERNAME:(R)"

# Step 2: SSH in
ssh -i "C:\Users\tssai\.ssh\llm-devsecops-key.pem" ec2-user@13.50.233.232

PERMISSION DENIED
IN WSL
# Step 1: Copy the key to your WSL home directory
cp /mnt/c/Users/tssai/.ssh/llm-devsecops-key.pem ~/llm-devsecops-key.pem

# Step 2: Now chmod WILL work here
chmod 400 ~/llm-devsecops-key.pem

# Step 3: SSH in using the copied key
ssh -i ~/llm-devsecops-key.pem ec2-user@13.50.233.232


ONCE INSIDE SSH
sudo cat /var/lib/jenkins/secrets/initialAdminPassword


IF OTHER PORTS USING THEN USE

# Find what's using port 8080
sudo lsof -i :8080

# OR
sudo netstat -tlnp | grep 8080

# Replace <PID> with the number shown in the output above
sudo kill -9 <PID>

2. Navigate to **Manage Jenkins** > **Credentials** > **System** > **Global credentials (unrestricted)**.
3. Click **Add Credentials** and create two **Secret text** credentials with the following exact IDs:
   - `GEMINI_API_KEY` (Your Google Gemini API Key)
   - `SLACK_WEBHOOK_URL` (Your Slack Webhook URL for alerts)

---

## Step 4: Start Local Monitoring (Prometheus & Grafana)
Start the monitoring stack to track pipeline performance and LLM metrics.

1. Navigate to the `monitoring` directory:
   ```bash
   cd ../monitoring
   ```
2. Start the stack in the background:
   ```bash
   docker compose -f docker-compose-monitoring.yml up -d
   ```
3. You can now access:
   - **Grafana**: `http://localhost:3000` (Default login is `admin` / `admin`)
   - **Prometheus**: `http://localhost:9090`
   - **Pushgateway**: `http://localhost:9091`

---

## Step 5: Run the DevSecOps Pipeline (Jenkins)
Now it's time to run the core pipeline which performs the security scanning and builds the web dashboard.

1. In Jenkins, create a new **Pipeline** project.
2. In the configuration, check **"This project is parameterized"**.
   - Add a **String Parameter**.
   - Name: `TARGET_REPO_URL`
   - Default Value: Leave blank (to scan your local terraform) or paste a GitHub URL to scan an external project.
3. In the Pipeline section, point it to your repository's `Jenkinsfile`.

Definition dropdown → select Pipeline script from SCM
SCM → select Git
Repository URL → paste:
https://github.com/SaiAnnirudh/llm-devsecops-pipeline.git
Branch Specifier → */main
Script Path → Jenkinsfile (already the default, don't change it)
Click Save
Then click "Build with Parameters" on the left sidebar to run it!


4. Click **Build with Parameters**.
5. Watch the stages complete:
   - **Checkout**: Clones the target repo.
   - **Security Validation (Checkov + LLMs)**: Scans the IaC and pushes metrics to your local Pushgateway.
   - **Build Docker Image**: Packages the web app and the JSON results.

---

## Step 6: View the Dashboard
Once Jenkins finishes building the Docker image (`llm-devsecops-app:latest`), run it to view your results!

1. Run the newly built Docker container:
   ```bash
   docker run -d -p 8080:80 llm-devsecops-app:latest
   ```
2. Open your browser and go to `http://localhost:8080`.
3. You will see the **DevSecOps Intelligence** dashboard displaying the side-by-side code diffs and security recommendations!

*(Alternatively, if you deployed the UI to Netlify, click "Upload Scan Results" on your Netlify site and select the `llm_validation_results.json` file generated in your Jenkins workspace).*

# Compliance Document System - Deployment Guide

This guide provides instructions for deploying the Compliance Document System on a Google Cloud Platform (GCP) virtual machine.

## Table of Contents

1. [Overview](#overview)
2. [Local Development](#local-development)
3. [GCP VM Deployment](#gcp-vm-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Troubleshooting](#troubleshooting)

## Overview

The Compliance Document System is a web application that uses Algorand blockchain to track and verify compliance documents. The system consists of:

- **Backend**: Flask API that interfaces with the Algorand blockchain
- **Frontend**: React.js application with Material-UI components
- **Blockchain**: Algorand smart contract for compliance document management

## Local Development

### Prerequisites

- Python 3.9+
- Node.js 16+
- npm or yarn
- Algorand Node or PureStake API access

### Setup

1. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Build the frontend:
   ```bash
   npm run build
   ```

4. Run the Flask development server:
   ```bash
   python app.py
   ```

## GCP VM Deployment

### Prerequisites

- Google Cloud Platform account
- gcloud CLI installed
- Docker installed (optional, for container deployment)

### VM Setup

1. Create a new Compute Engine VM instance:
   ```bash
   gcloud compute instances create compliance-app \
     --image-family=debian-11 \
     --image-project=debian-cloud \
     --machine-type=e2-medium \
     --boot-disk-size=10GB \
     --tags=http-server,https-server
   ```

2. Allow HTTP and HTTPS traffic:
   ```bash
   gcloud compute firewall-rules create allow-http \
     --direction=INGRESS \
     --action=ALLOW \
     --rules=tcp:80 \
     --target-tags=http-server

   gcloud compute firewall-rules create allow-https \
     --direction=INGRESS \
     --action=ALLOW \
     --rules=tcp:443 \
     --target-tags=https-server
   ```

3. SSH into your VM:
   ```bash
   gcloud compute ssh compliance-app
   ```

### Manual Deployment

1. Install dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-venv git nginx
   ```

2. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/compliance-document-system.git
   cd compliance-document-system
   ```

3. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Install Node.js:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

6. Build the frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

7. Set up Gunicorn:
   ```bash
   pip install gunicorn
   ```

8. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/compliance-app.service
   ```
   Add the following content:
   ```
   [Unit]
   Description=Compliance Document System
   After=network.target

   [Service]
   User=your-username
   WorkingDirectory=/path/to/compliance-document-system
   ExecStart=/path/to/compliance-document-system/venv/bin/gunicorn --bind 0.0.0.0:5000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

9. Configure Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/compliance-app
   ```
   Add the following content:
   ```
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

10. Enable the Nginx site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/compliance-app /etc/nginx/sites-enabled
    sudo nginx -t
    sudo systemctl restart nginx
    ```

11. Start the application:
    ```bash
    sudo systemctl start compliance-app
    sudo systemctl enable compliance-app
    ```

## Docker Deployment

### Prerequisites

- Docker and Docker Compose installed on your VM

### Steps

1. SSH into your VM:
   ```bash
   gcloud compute ssh compliance-app
   ```

2. Install Docker:
   ```bash
   sudo apt-get update
   sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
   curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
   sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io
   ```

3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/compliance-document-system.git
   cd compliance-document-system
   ```

4. Create a docker-compose.yml file:
   ```bash
   cat > docker-compose.yml << EOL
   version: '3'

   services:
     compliance-app:
       build: .
       ports:
         - "80:5000"
       environment:
         - ALGORAND_NODE_ADDRESS=your-algorand-node-address
         - ALGORAND_NODE_TOKEN=your-algorand-node-token
       restart: always
   EOL
   ```

5. Build and run the Docker container:
   ```bash
   sudo docker-compose up -d --build
   ```

## Environment Configuration

Configure your environment variables for production deployment:

1. Create a .env file in the project root:
   ```
   ALGORAND_NODE_ADDRESS=https://your-algorand-node-or-purestake
   ALGORAND_NODE_TOKEN=your-algorand-api-key
   FLASK_ENV=production
   FLASK_SECRET_KEY=your-secure-secret-key
   ```

2. Load environment variables in app.py:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

## Troubleshooting

### Common Issues

1. **Connection to Algorand Node Failing**
   - Check if your Algorand node is accessible from the VM
   - Verify API keys are correctly set in environment variables

2. **Application Not Starting**
   - Check systemd logs: `sudo journalctl -u compliance-app`
   - Verify permissions on application files

3. **Frontend Not Loading**
   - Check if frontend build was successful
   - Verify Nginx configuration and logs: `sudo tail -f /var/log/nginx/error.log`

4. **Docker Issues**
   - Check Docker logs: `sudo docker logs <container_id>`
   - Ensure Docker service is running: `sudo systemctl status docker`

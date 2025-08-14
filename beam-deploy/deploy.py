#!/usr/bin/env python3
"""
Beam Cloud deployment script for Document Q&A and Web Search application
"""

import os
import subprocess
import sys
from pathlib import Path
# from beam import Pod 

# pod = Pod(
#     name="Pro-Bab",
#     cpu=4,
#     memory="16Gi",
#     gpu="A10G",  # Choose your required GPU type (e.g., "T4", "A10G", "A100")
#     ports=[8000],
#     entrypoint=["python3", "beam-deploy/deploy.py"],
# )

def run_command(cmd, cwd=None):
    """Run shell command and handle errors"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    
    print(result.stdout)
    return result.stdout

def build_and_push_images():
    """Build and push Docker images to Beam Cloud registry"""
    
    # Set your Beam Cloud registry URL
    registry = os.getenv("BEAM_REGISTRY_URL", "https://8cdcf40b-006d-421a-8791-fe7a26402bdb-8000.app.beam.cloud/")
    
    services = [
        "document-service",
        "llm-service", 
        "web-search-service",
        "api-gateway"
    ]
    
    for service in services:
        print(f"\n=== Building {service} ===")
        
        # Build image
        # build_cmd = f"docker compose build pro-bab-{service}"
        # run_command(build_cmd)
        
        # Push to registry
        tag_cmd = f"docker tag pro-bab-{service}:latest eypsrcnuygr/pro-bab-{service}:latest"
        push_cmd = f"docker push eypsrcnuygr/pro-bab-{service}:latest"
        run_command(tag_cmd)
        run_command(push_cmd)
    
    # Build frontend
    # print(f"\n=== Building frontend ===")
    # build_cmd = f"docker build -t frontend:latest ./frontend"
    # run_command(build_cmd)
    tag_cmd = f"docker tag pro-bab-frontend:latest eypsrcnuygr/pro-bab-frontend:latest"
    push_cmd = f"docker push eypsrcnuygr/pro-bab-frontend:latest"
    run_command(push_cmd)

def deploy_to_beam():
    """Deploy application to Beam Cloud"""
    print("\n=== Deploying to Beam Cloud ===")
    
    # Apply Kubernetes configuration
    deploy_cmd = "kubectl apply -f beam.yaml"
    run_command(deploy_cmd, cwd="beam-deploy")
    
    print("\n=== Deployment completed! ===")
    print("Check the status with: kubectl get pods")
    print("Get service URL with: kubectl get services")

def main():
    """Main deployment function"""
    print("Starting Beam Cloud deployment...")
    
    # Check if required environment variables are set
    # required_vars = ["BEAM_REGISTRY_URL", "BING_API_KEY"]
    # for var in required_vars:
    #     if not os.getenv(var):
    #         print(f"Error: {var} environment variable is required")
    #         sys.exit(1)
    
    # Build and push images
    build_and_push_images()
    
    # Deploy to Beam Cloud
    deploy_to_beam()

if __name__ == "__main__":
    main()
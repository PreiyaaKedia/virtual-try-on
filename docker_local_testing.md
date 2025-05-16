# Testing Docker Image Locally

Before deploying to Azure Container App, it's recommended to test the Docker image locally to ensure everything works properly.

## Prerequisites
- Docker Desktop installed and running
- PowerShell or a terminal

## Steps to Test Locally

1. **Build the Docker image**

```powershell
docker build -t virtual-try-on:latest .
```

2. **Run the Docker container**

```powershell
docker run -p 8501:8501 -v ${PWD}/config.json:/app/config.json virtual-try-on:latest
```

3. **Open the application in your browser**

Navigate to [http://localhost:8501](http://localhost:8501) in your web browser.

4. **Verify the application works**

- Test that you can upload images
- Test that Azure OpenAI integration works
- Verify that you can generate try-on images

## Troubleshooting

If you encounter any issues:

1. **Check Docker logs**

```powershell
docker ps
```

Get the container ID from the output, then:

```powershell
docker logs <container_id>
```

2. **Interactive debugging**

You can also run the container in interactive mode:

```powershell
docker run -it -p 8501:8501 virtual-try-on:local /bin/bash
```

This will give you a shell inside the container where you can run commands and check files.

## Deploying to Azure

Once you've verified that the Docker image works locally, you can deploy it to Azure Container App using the `deploy_container_app.ps1` script:

```powershell
./deploy_container_app.ps1
```

Follow the prompts to complete the deployment.

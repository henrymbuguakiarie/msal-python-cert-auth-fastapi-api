# Deployment Guide

This guide covers deploying the Blog API to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Azure App Service Deployment](#azure-app-service-deployment)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Monitoring Setup](#monitoring-setup)
- [Post-Deployment Checklist](#post-deployment-checklist)

## Prerequisites

### Required Resources

- Microsoft Entra ID tenant
- App registrations (API + Client)
- X.509 certificate uploaded to Azure
- Database (PostgreSQL recommended)
- Azure Key Vault (production)

### Tools

- Azure CLI (`az`)
- Docker (for container deployments)
- kubectl (for Kubernetes deployments)

## Azure App Service Deployment

### Option 1: Deploy from Azure CLI

```bash
# Login to Azure
az login

# Create resource group
az group create \
  --name blog-api-rg \
  --location eastus

# Create App Service Plan
az appservice plan create \
  --name blog-api-plan \
  --resource-group blog-api-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --name blog-api \
  --resource-group blog-api-rg \
  --plan blog-api-plan \
  --runtime "PYTHON:3.10"

# Configure App Settings
az webapp config appsettings set \
  --name blog-api \
  --resource-group blog-api-rg \
  --settings \
    TENANT_ID="your-tenant-id" \
    API_APP_ID_URI="api://your-app-id" \
    DATABASE_URL="postgresql://user:pass@host/db" \
    ENVIRONMENT="production"

# Enable system-assigned managed identity
az webapp identity assign \
  --name blog-api \
  --resource-group blog-api-rg

# Deploy code
cd api
az webapp up \
  --name blog-api \
  --resource-group blog-api-rg
```

### Option 2: Deploy with Docker

```bash
# Build and push Docker image
docker build -t youracr.azurecr.io/blog-api:latest -f api/Dockerfile ./api
docker push youracr.azurecr.io/blog-api:latest

# Create Web App with container
az webapp create \
  --name blog-api \
  --resource-group blog-api-rg \
  --plan blog-api-plan \
  --deployment-container-image-name youracr.azurecr.io/blog-api:latest
```

### Configure Managed Identity for Key Vault

```bash
# Get managed identity principal ID
PRINCIPAL_ID=$(az webapp identity show \
  --name blog-api \
  --resource-group blog-api-rg \
  --query principalId -o tsv)

# Grant Key Vault access
az keyvault set-policy \
  --name your-keyvault \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list \
  --certificate-permissions get list
```

## Docker Deployment

### Build Image

```bash
cd api
docker build -t blog-api:latest -f Dockerfile .
```

### Run Locally

```bash
docker run -d \
  --name blog-api \
  -p 8000:8000 \
  -e TENANT_ID="your-tenant-id" \
  -e API_APP_ID_URI="api://your-app-id" \
  -e DATABASE_URL="postgresql://user:pass@host/db" \
  blog-api:latest
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Kubernetes Deployment

### Create Kubernetes Resources

**1. Create Namespace**

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: blog-api
```

**2. Create Secret**

```bash
kubectl create secret generic blog-api-secrets \
  --namespace blog-api \
  --from-literal=tenant-id="your-tenant-id" \
  --from-literal=api-app-id-uri="api://your-app-id" \
  --from-literal=database-url="postgresql://..."
```

**3. Create Deployment**

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blog-api
  namespace: blog-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: blog-api
  template:
    metadata:
      labels:
        app: blog-api
    spec:
      containers:
      - name: blog-api
        image: youracr.azurecr.io/blog-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: TENANT_ID
          valueFrom:
            secretKeyRef:
              name: blog-api-secrets
              key: tenant-id
        - name: API_APP_ID_URI
          valueFrom:
            secretKeyRef:
              name: blog-api-secrets
              key: api-app-id-uri
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: blog-api-secrets
              key: database-url
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

**4. Create Service**

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: blog-api
  namespace: blog-api
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: blog-api
```

**5. Create Ingress (Optional)**

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: blog-api
  namespace: blog-api
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: blog-api-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: blog-api
            port:
              number: 80
```

**Deploy to Kubernetes**

```bash
kubectl apply -f namespace.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Check status
kubectl get pods -n blog-api
kubectl get svc -n blog-api
kubectl logs -f deployment/blog-api -n blog-api
```

## Environment Configuration

### Production Environment Variables

```bash
# Required
TENANT_ID=your-tenant-id
API_APP_ID_URI=api://your-app-id
DATABASE_URL=postgresql://user:pass@host:5432/blogdb

# Optional
REQUIRED_SCOPE=access_as_user
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Azure Key Vault Integration

```python
# config.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_secret(secret_name: str) -> str:
    """Get secret from Azure Key Vault."""
    credential = DefaultAzureCredential()
    client = SecretClient(
        vault_url="https://your-keyvault.vault.azure.net/",
        credential=credential
    )
    return client.get_secret(secret_name).value

# Usage
DATABASE_URL = get_secret("database-url")
```

## Database Setup

### PostgreSQL (Recommended)

**1. Create Database**

```sql
CREATE DATABASE blogdb;
CREATE USER bloguser WITH ENCRYPTED PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE blogdb TO bloguser;
```

**2. Run Migrations**

```bash
# Using Alembic (if configured)
alembic upgrade head

# Or create tables from code
python -c "from src.database import create_db_and_tables; create_db_and_tables()"
```

**3. Seed Data (Optional)**

```bash
cd api
poetry run python scripts/seed_data.py --users 5 --count 50
```

### Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --name blog-postgres \
  --resource-group blog-api-rg \
  --location eastus \
  --admin-user blogadmin \
  --admin-password "StrongPassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32

# Create database
az postgres flexible-server db create \
  --server-name blog-postgres \
  --resource-group blog-api-rg \
  --database-name blogdb

# Configure firewall (allow Azure services)
az postgres flexible-server firewall-rule create \
  --name blog-postgres \
  --resource-group blog-api-rg \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

## Monitoring Setup

### Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app blog-api-insights \
  --location eastus \
  --resource-group blog-api-rg \
  --application-type web

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app blog-api-insights \
  --resource-group blog-api-rg \
  --query instrumentationKey -o tsv)

# Add to app settings
az webapp config appsettings set \
  --name blog-api \
  --resource-group blog-api-rg \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

### Log Analytics

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group blog-api-rg \
  --workspace-name blog-api-logs

# Link to App Service
az monitor diagnostic-settings create \
  --name blog-api-diagnostics \
  --resource $(az webapp show --name blog-api --resource-group blog-api-rg --query id -o tsv) \
  --workspace blog-api-logs \
  --logs '[{"category": "AppServiceHTTPLogs", "enabled": true}]'
```

## Post-Deployment Checklist

### Security

- [ ] HTTPS/TLS configured and enforced
- [ ] Certificates stored in Key Vault
- [ ] Managed Identity configured
- [ ] Security headers verified
- [ ] CORS properly restricted
- [ ] Rate limiting enabled
- [ ] Firewall rules configured
- [ ] Network security groups configured

### Performance

- [ ] Database connection pooling configured
- [ ] Caching strategy implemented
- [ ] CDN configured for static assets
- [ ] Auto-scaling rules configured
- [ ] Resource limits set

### Monitoring

- [ ] Application Insights configured
- [ ] Log Analytics workspace setup
- [ ] Alerts configured for:
  - High error rates
  - Certificate expiration
  - Database connectivity issues
  - High response times
  - Resource exhaustion
- [ ] Dashboards created

### Operations

- [ ] Health check endpoints working
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan tested
- [ ] Runbook created for common issues
- [ ] On-call rotation configured

### Testing

- [ ] Smoke tests passed
- [ ] Load testing completed
- [ ] Security scanning performed
- [ ] Penetration testing conducted
- [ ] User acceptance testing completed

## Rollback Procedure

If deployment issues occur:

```bash
# Azure App Service
az webapp deployment slot swap \
  --name blog-api \
  --resource-group blog-api-rg \
  --slot staging \
  --action swap

# Kubernetes
kubectl rollout undo deployment/blog-api -n blog-api

# Docker
docker-compose down
docker-compose up -d --force-recreate
```

## Support

For deployment issues:
- Check Azure Portal diagnostics
- Review Application Insights logs
- Consult runbook documentation
- Contact DevOps team

---

**Last Updated:** 2024-12-24
**Version:** 1.0

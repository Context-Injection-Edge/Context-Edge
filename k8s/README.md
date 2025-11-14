# Kubernetes Deployment for Context Edge

This directory contains Kubernetes manifests for deploying Context Edge in production.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker images built and pushed to registry

## Quick Deploy

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Deploy database and cache
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f redis-deployment.yaml

# Wait for database to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n context-edge --timeout=120s

# Deploy services
kubectl apply -f context-service-deployment.yaml
kubectl apply -f data-ingestion-deployment.yaml

# Verify deployment
kubectl get all -n context-edge
```

## Build and Push Docker Images

```bash
# Context Service
cd context-service
docker build -t your-registry/context-edge/context-service:latest .
docker push your-registry/context-edge/context-service:latest

# Data Ingestion
cd ../data-ingestion
docker build -t your-registry/context-edge/data-ingestion:latest .
docker push your-registry/context-edge/data-ingestion:latest
```

Update image references in deployment YAMLs.

## Configuration

### Database Credentials

Update `postgres-secret` in `postgres-statefulset.yaml`:

```yaml
stringData:
  POSTGRES_PASSWORD: your-secure-password
```

### Resource Limits

Adjust CPU/memory limits in deployment YAMLs based on your workload:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Storage

Adjust storage sizes in PVC specs:

- PostgreSQL: Default 10Gi
- Redis: Default 5Gi
- LDO Storage: Default 100Gi

## Access Services

### Get External IPs

```bash
kubectl get svc -n context-edge
```

### Port Forward (for testing)

```bash
# Context Service
kubectl port-forward svc/context-service 8000:8000 -n context-edge

# Data Ingestion
kubectl port-forward svc/data-ingestion 8001:8001 -n context-edge
```

## Scaling

```bash
# Scale Context Service
kubectl scale deployment context-service --replicas=5 -n context-edge

# Scale Data Ingestion
kubectl scale deployment data-ingestion --replicas=3 -n context-edge
```

## Monitoring

```bash
# Check pod status
kubectl get pods -n context-edge

# View logs
kubectl logs -f deployment/context-service -n context-edge
kubectl logs -f deployment/data-ingestion -n context-edge

# Describe resources
kubectl describe deployment context-service -n context-edge
```

## Cleanup

```bash
kubectl delete namespace context-edge
```

## Production Considerations

1. **TLS/SSL**: Add Ingress with cert-manager for HTTPS
2. **Authentication**: Implement OAuth2/JWT for API access
3. **Monitoring**: Deploy Prometheus + Grafana
4. **Logging**: Set up ELK/Loki stack
5. **Backups**: Configure regular PostgreSQL backups
6. **High Availability**: Use multi-zone deployments
7. **Secrets Management**: Use external secrets (Vault, AWS Secrets Manager)

## Ingress Example

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: context-edge-ingress
  namespace: context-edge
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - api.context-edge.com
      secretName: context-edge-tls
  rules:
    - host: api.context-edge.com
      http:
        paths:
          - path: /context
            pathType: Prefix
            backend:
              service:
                name: context-service
                port:
                  number: 8000
          - path: /ingest
            pathType: Prefix
            backend:
              service:
                name: data-ingestion
                port:
                  number: 8001
```

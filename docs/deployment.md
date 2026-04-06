# Knowledge Compiler Deployment Guide

Guide for deploying Knowledge Compiler in production environments.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Strategies](#deployment-strategies)
4. [Configuration](#configuration)
5. [Monitoring Setup](#monitoring-setup)
6. [Performance Tuning](#performance-tuning)
7. [Security Considerations](#security-considerations)
8. [Maintenance Procedures](#maintenance-procedures)

---

## System Requirements

### Minimum Requirements

- **CPU**: 2 cores
- **RAM**: 2GB
- **Disk**: 500MB
- **Python**: 3.10+
- **OS**: Linux, macOS, or Windows

### Recommended Requirements

- **CPU**: 4+ cores
- **RAM**: 4GB+
- **Disk**: 2GB+ SSD
- **Python**: 3.11+
- **OS**: Linux (Ubuntu 22.04+ recommended)

### External Dependencies

- **LLM API Access**: OpenAI API or compatible service
- **Database**: SQLite (included) or PostgreSQL (optional)
- **Web Server**: Nginx or Apache (for web interface)

---

## Pre-Deployment Checklist

### Environment Setup

- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables configured
- [ ] File permissions set correctly

### Configuration

- [ ] Configuration file created and tested
- [ ] API keys configured (LLM, monitoring, etc.)
- [ ] Directory paths created and accessible
- [ ] Log rotation configured
- [ ] Backup strategy in place

### Testing

- [ ] Unit tests passing (`pytest tests/`)
- [ ] Integration tests passing
- [ ] Quality checks passing
- [ ] Performance benchmarks acceptable
- [ ] Monitoring and alerting configured

### Documentation

- [ ] API documentation reviewed
- [ ] User manual reviewed
- [ ] Deployment runbook created
- [ ] Escalation procedures documented

---

## Deployment Strategies

### Development Deployment

Quick setup for development and testing.

```bash
# Clone repository
git clone https://github.com/your-org/knowledge-compiler.git
cd knowledge-compiler

# Setup environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your settings

# Test deployment
python -m pytest tests/ -v
python -m src.main_cli --config config/config.yaml --test
```

### Production Deployment

#### 1. Systemd Service (Linux)

Create service file `/etc/systemd/system/knowledge-compiler.service`:

```ini
[Unit]
Description=Knowledge Compiler Service
After=network.target

[Service]
Type=simple
User=kc_user
WorkingDirectory=/opt/knowledge-compiler
Environment="PATH=/opt/knowledge-compiler/.venv/bin"
EnvironmentFile=/opt/knowledge-compiler/.env
ExecStart=/opt/knowledge-compiler/.venv/bin/python -m src.main_cli --config /etc/knowledge-compiler/production.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl enable knowledge-compiler
sudo systemctl start knowledge-compiler
sudo systemctl status knowledge-compiler
```

#### 2. Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 kc_user && \
    chown -R kc_user:kc_user /app
USER kc_user

# Expose metrics port
EXPOSE 9090

# Start application
CMD ["python", "-m", "src.main_cli", "--config", "config/production.yaml"]
```

Build and run:

```bash
# Build image
docker build -t knowledge-compiler:latest .

# Run container
docker run -d \
  --name knowledge-compiler \
  -v /path/to/config:/app/config \
  -v /path/to/documents:/app/documents \
  -v /path/to/wiki:/app/wiki \
  -p 9090:9090 \
  --restart unless-stopped \
  knowledge-compiler:latest

# Check logs
docker logs -f knowledge-compiler

# Check metrics
curl http://localhost:9090/metrics
```

#### 3. Kubernetes Deployment

Create `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowledge-compiler
  labels:
    app: knowledge-compiler
spec:
  replicas: 2
  selector:
    matchLabels:
      app: knowledge-compiler
  template:
    metadata:
      labels:
        app: knowledge-compiler
    spec:
      containers:
      - name: knowledge-compiler
        image: knowledge-compiler:latest
        ports:
        - containerPort: 9090
          name: metrics
        env:
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: kc-secrets
              key: llm-api-key
        - name: KNOWLEDGE_COMPILER_CONFIG
          value: "/config/production.yaml"
        volumeMounts:
        - name: config
          mountPath: /config
        - name: documents
          mountPath: /app/documents
        - name: wiki
          mountPath: /app/wiki
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
      volumes:
      - name: config
        configMap:
          name: kc-config
      - name: documents
        persistentVolumeClaim:
          claimName: kc-documents
      - name: wiki
        persistentVolumeClaim:
          claimName: kc-wiki
---
apiVersion: v1
kind: Service
metadata:
  name: knowledge-compiler
spec:
  selector:
    app: knowledge-compiler
  ports:
  - port: 9090
    targetPort: 9090
    name: metrics
  type: ClusterIP
```

Deploy:

```bash
# Create secrets
kubectl create secret generic kc-secrets \
  --from-literal=llm-api-key='your-api-key'

# Create config map
kubectl create configmap kc-config \
  --from-file=config/production.yaml

# Deploy
kubectl apply -f deployment.yaml

# Check status
kubectl get pods -l app=knowledge-compiler
kubectl logs -f deployment/knowledge-compiler
```

---

## Configuration

### Production Configuration

Create `config/production.yaml`:

```yaml
# Production configuration
source_dir: "/var/lib/knowledge-compiler/documents"
target_dir: "/var/lib/knowledge-compiler/wiki"

# Categories
categories:
  - "技术指标"
  - "战法"
  - "形态"

# Extraction settings
extraction:
  min_confidence: 0.7
  max_concepts: 100
  min_relationships: 5

# Insight settings
insights:
  enabled: true
  max_hops: 2
  backfill_batch_size: 20

# Quality settings
quality:
  enabled: true
  max_stale_days: 90
  min_quality_score: 0.8
  check_interval_hours: 24

# Performance settings
performance:
  cache_enabled: true
  cache_ttl: 7200
  max_workers: 8
  l1_cache_size: 2000
  l2_cache_enabled: true

# Monitoring settings
monitoring:
  enabled: true
  log_level: INFO
  log_file: /var/log/knowledge-compiler/compiler.log
  metrics_enabled: true
  metrics_port: 9090
  alert_enabled: true
```

### Environment Variables

Create `.env` file:

```bash
# Application settings
KNOWLEDGE_COMPILER_CONFIG=/etc/knowledge-compiler/production.yaml
KNOWLEDGE_COMPILER_LOG_LEVEL=INFO
KNOWLEDGE_COMPILER_CACHE_DIR=/var/cache/knowledge-compiler

# LLM settings
LLM_API_KEY=your_production_api_key
LLM_MODEL=gpt-4
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3

# Database settings (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost/knowledge_compiler
DATABASE_POOL_SIZE=20

# Monitoring settings
METRICS_ENABLED=true
METRICS_PORT=9090
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.example.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM=alerts@example.com
ALERT_EMAIL_TO=ops@example.com

# Security settings
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=100
API_KEY_HEADER=X-API-Key
```

---

## Monitoring Setup

### Metrics Endpoint

Access metrics at `http://localhost:9090/metrics`:

```bash
# View metrics
curl http://localhost:9090/metrics

# Example metrics output
# HELP documents_processed_total Total documents processed
# TYPE documents_processed_total counter
documents_processed_total{status="success"} 1234
documents_processed_total{status="error"} 5

# HELP processing_duration_seconds Processing duration
# TYPE processing_duration_seconds histogram
processing_duration_seconds_bucket{le="0.1"} 800
processing_duration_seconds_bucket{le="0.5"} 1200
processing_duration_seconds_bucket{le="+Inf"} 1239
```

### Prometheus Integration

Add to Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'knowledge-compiler'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s
    metrics_path: /metrics
```

### Grafana Dashboards

Import dashboard templates from `src/monitoring/dashboard/`:

1. Login to Grafana
2. Go to Dashboards → Import
3. Upload dashboard JSON
4. Configure data source

### Alert Configuration

Set up alert rules in `config/alerts.yaml`:

```yaml
alerts:
  - name: high_error_rate
    description: Error rate exceeds 5%
    metric_name: error_rate
    condition: gt
    threshold: 5.0
    severity: WARNING
    duration_seconds: 300
    cooldown_seconds: 1800

  - name: low_quality_score
    description: Wiki quality score below 0.8
    metric_name: quality_score
    condition: lt
    threshold: 0.8
    severity: ERROR
    duration_seconds: 600
    cooldown_seconds: 3600
```

---

## Performance Tuning

### Memory Optimization

```yaml
# Reduce memory footprint
performance:
  cache_enabled: true
  l1_cache_size: 1000  # Reduce from default
  l2_cache_enabled: false  # Disable L2 cache
  max_workers: 2  # Reduce parallelism
```

### CPU Optimization

```yaml
# Maximize CPU utilization
performance:
  max_workers: 8  # Increase for multi-core systems
  batch_size: 50  # Process more items per batch
  concurrent_queries: true
```

### I/O Optimization

```yaml
# Optimize disk I/O
performance:
  cache_enabled: true
  cache_ttl: 14400  # Longer cache TTL
  batch_writes: true  # Batch disk writes
  async_operations: true  # Enable async I/O
```

### Database Optimization (PostgreSQL)

```sql
-- Create indexes
CREATE INDEX idx_pages_category ON pages(category);
CREATE INDEX idx_concepts_name ON concepts(name);
CREATE INDEX idx_relationships_from ON relationships(from_concept);
CREATE INDEX idx_relationships_to ON relationships(to_concept);

-- Configure connection pool
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

---

## Security Considerations

### API Key Management

```bash
# Use environment variables
export LLM_API_KEY="your-api-key"

# Or use secret management
kubectl create secret generic kc-secrets \
  --from-literal=llm-api-key='your-api-key'
```

### File Permissions

```bash
# Restrict access to sensitive directories
chmod 700 /var/lib/knowledge-compiler
chmod 600 /etc/knowledge-compiler/production.yaml
chmod 640 /var/log/knowledge-compiler/*.log

# Run as non-root user
useradd -r -s /bin/false kc_user
chown -R kc_user:kc_user /opt/knowledge-compiler
```

### Network Security

```yaml
# Firewall rules
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 9090/tcp  # Metrics (restrict to internal)
ufw enable
```

### Rate Limiting

```yaml
# Enable rate limiting
security:
  enable_rate_limiting: true
  max_requests_per_minute: 100
  burst_size: 20
```

---

## Maintenance Procedures

### Log Rotation

Configure logrotate (`/etc/logrotate.d/knowledge-compiler`):

```
/var/log/knowledge-compiler/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 kc_user kc_user
    sharedscripts
    postrotate
        systemctl reload knowledge-compiler > /dev/null 2>&1 || true
    endscript
}
```

### Backup Strategy

```bash
#!/bin/bash
# Daily backup script

# Backup configuration
tar -czf /backup/config-$(date +%Y%m%d).tar.gz /etc/knowledge-compiler/

# Backup wiki data
tar -czf /backup/wiki-$(date +%Y%m%d).tar.gz /var/lib/knowledge-compiler/wiki/

# Backup database (if using PostgreSQL)
pg_dump knowledge_compiler > /backup/db-$(date +%Y%m%d).sql

# Retention: Keep last 30 days
find /backup -name "*.tar.gz" -mtime +30 -delete
find /backup -name "*.sql" -mtime +30 -delete
```

### Health Checks

```bash
#!/bin/bash
# Health check script

# Check service status
if ! systemctl is-active --quiet knowledge-compiler; then
    echo "CRITICAL: Service not running"
    exit 2
fi

# Check metrics endpoint
if ! curl -f http://localhost:9090/metrics > /dev/null 2>&1; then
    echo "WARNING: Metrics endpoint not responding"
    exit 1
fi

# Check disk space
DISK_USAGE=$(df /var/lib/knowledge-compiler | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage at ${DISK_USAGE}%"
    exit 1
fi

echo "OK: All checks passed"
exit 0
```

### Update Procedure

```bash
#!/bin/bash
# Update script

# Backup current version
./scripts/backup.sh

# Pull latest code
git pull origin main

# Update dependencies
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Run tests
pytest tests/ -v

# Restart service
sudo systemctl restart knowledge-compiler

# Verify deployment
./scripts/health_check.sh
```

---

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
sudo journalctl -u knowledge-compiler -n 50

# Check configuration
python -m src.main_cli --config /etc/knowledge-compiler/production.yaml --validate
```

**High memory usage:**
```bash
# Check memory usage
free -h
ps aux | grep knowledge-compiler

# Reduce cache size
# Update config and restart
```

**Slow performance:**
```bash
# Check metrics
curl http://localhost:9090/metrics | grep duration

# Enable performance monitoring
# Update config with monitoring.performance.enabled = true
```

### Emergency Procedures

**Rollback to previous version:**
```bash
# Stop service
sudo systemctl stop knowledge-compiler

# Restore backup
./scripts/restore.sh /backup/wiki-YYYYMMDD.tar.gz

# Restart service
sudo systemctl start knowledge-compiler
```

**Emergency maintenance mode:**
```yaml
# Set maintenance mode
monitoring:
  maintenance_mode: true
  maintenance_message: "Scheduled maintenance in progress"
```

---

## Support

For additional support:
- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/your-org/knowledge-compiler/issues)
- Email: support@example.com

# Knowledge Compiler Troubleshooting Guide

Comprehensive troubleshooting guide for common issues and solutions.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Configuration Issues](#configuration-issues)
4. [Runtime Issues](#runtime-issues)
5. [Performance Issues](#performance-issues)
6. [Quality Issues](#quality-issues)
7. [Monitoring Issues](#monitoring-issues)
8. [Data Issues](#data-issues)
9. [Integration Issues](#integration-issues)
10. [Emergency Procedures](#emergency-procedures)

---

## Quick Diagnostics

### Health Check Script

```bash
#!/bin/bash
# Quick health check

echo "=== Knowledge Compiler Health Check ==="

# Check service status
echo "1. Service Status:"
systemctl status knowledge-compiler --no-pager

# Check disk space
echo "2. Disk Space:"
df -h /var/lib/knowledge-compiler

# Check memory usage
echo "3. Memory Usage:"
free -h

# Check metrics endpoint
echo "4. Metrics Endpoint:"
if curl -f http://localhost:9090/metrics > /dev/null 2>&1; then
    echo "✓ Metrics endpoint responding"
else
    echo "✗ Metrics endpoint not responding"
fi

# Check recent errors
echo "5. Recent Errors:"
journalctl -u knowledge-compiler --since "1 hour ago" | grep -i error || echo "No recent errors"

echo "=== Health Check Complete ==="
```

### Diagnostic Commands

```bash
# Check service logs
sudo journalctl -u knowledge-compiler -n 100 --no-pager

# Check application logs
tail -n 100 /var/log/knowledge-compiler/compiler.log

# Check configuration
python -m src.main_cli --config /etc/knowledge-compiler/production.yaml --validate

# Run diagnostics
python scripts/diagnose.py --verbose

# Check database connections
python scripts/test_db.py --test-connection

# Check cache status
curl http://localhost:9090/metrics | grep cache
```

---

## Installation Issues

### Python Version Incompatible

**Error:** `Python 3.10 or higher required`

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.10+
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.10 python3.10-venv

# Create virtual environment with correct version
python3.10 -m venv .venv
source .venv/bin/activate
```

### Dependencies Installation Failures

**Error:** `Failed to install dependencies`

**Solution:**
```bash
# Update pip
pip install --upgrade pip

# Install system dependencies
sudo apt-get install build-essential python3-dev

# Install with specific versions
pip install -r requirements.txt --no-cache-dir

# If specific package fails
pip install package_name --verbose
```

### Permission Errors

**Error:** `Permission denied when creating directories`

**Solution:**
```bash
# Create directories with correct permissions
sudo mkdir -p /var/lib/knowledge-compiler
sudo mkdir -p /var/log/knowledge-compiler
sudo mkdir -p /etc/knowledge-compiler

# Set ownership
sudo chown -R kc_user:kc_user /var/lib/knowledge-compiler
sudo chown -R kc_user:kc_user /var/log/knowledge-compiler

# Set permissions
chmod 755 /var/lib/knowledge-compiler
chmod 755 /var/log/knowledge-compiler
```

---

## Configuration Issues

### Invalid Configuration Format

**Error:** `Configuration validation failed`

**Solution:**
```bash
# Validate configuration
python -m src.main_cli --config config.yaml --validate

# Common issues:
# 1. Missing required fields
# 2. Invalid data types
# 3. Incorrect file paths
# 4. Invalid enum values

# Example fixes:
# Before:
extraction:
  confidence: "high"  # Wrong type

# After:
extraction:
  min_confidence: 0.7  # Correct type
```

### Environment Variables Not Loading

**Error:** `Environment variable not found`

**Solution:**
```bash
# Check if .env file exists
ls -la .env

# Export variables manually
export LLM_API_KEY="your-key"
export KNOWLEDGE_COMPILER_CONFIG="/path/to/config.yaml"

# Or use dotenv in Python
# Add to config.py:
from dotenv import load_dotenv
load_dotenv()

# Verify variables are set
env | grep LLM
env | grep KNOWLEDGE_COMPILER
```

### File Path Issues

**Error:** `File or directory not found`

**Solution:**
```bash
# Use absolute paths in configuration
source_dir: "/absolute/path/to/documents"
target_dir: "/absolute/path/to/wiki"

# Check if paths exist
ls -la /path/to/documents
ls -la /path/to/wiki

# Create directories if needed
mkdir -p /path/to/documents
mkdir -p /path/to/wiki

# Check permissions
ls -ld /path/to/documents
```

---

## Runtime Issues

### Service Won't Start

**Error:** `Service failed to start`

**Diagnosis:**
```bash
# Check service status
sudo systemctl status knowledge-compiler

# Check service logs
sudo journalctl -u knowledge-compiler -n 50 --no-pager

# Check for port conflicts
sudo netstat -tulpn | grep :9090
```

**Common Causes:**

1. **Port already in use**
```bash
# Find process using port
sudo lsof -i :9090

# Kill process or change port
# In config.yaml:
monitoring:
  metrics_port: 9091  # Use different port
```

2. **Missing dependencies**
```bash
# Reinstall dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Verify installation
python -c "import src.main"
```

3. **Configuration errors**
```bash
# Validate configuration
python -m src.main_cli --config config.yaml --validate

# Fix reported errors
```

### Compilation Failures

**Error:** `Document processing failed`

**Diagnosis:**
```bash
# Check recent compilation logs
tail -f /var/log/knowledge-compiler/compiler.log

# Identify specific error
grep "Error:" /var/log/knowledge-compiler/compiler.log | tail -10
```

**Common Causes:**

1. **Document format issues**
```bash
# Validate document format
file documents/example.md

# Check for encoding issues
file -i documents/example.md

# Convert to UTF-8 if needed
iconv -f ISO-8859-1 -t UTF-8 input.txt > output.md
```

2. **LLM API errors**
```bash
# Check API key
echo $LLM_API_KEY

# Test API connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $LLM_API_KEY"

# Check rate limits
# Reduce concurrent requests in config.yaml
performance:
  max_workers: 2  # Reduce from 4
```

3. **Memory issues**
```bash
# Check available memory
free -h

# Reduce memory usage
# In config.yaml:
performance:
  cache_enabled: false  # Disable cache temporarily
  max_workers: 1        # Reduce parallelism
```

### Extraction Failures

**Error:** `Concept extraction failed`

**Diagnosis:**
```bash
# Check extraction logs
grep "Extraction" /var/log/knowledge-compiler/compiler.log | tail -20

# Test extraction manually
python scripts/test_extraction.py --document documents/test.md
```

**Common Causes:**

1. **LLM timeout**
```bash
# Increase timeout in configuration
# In config.yaml:
extraction:
  timeout: 60  # Increase from 30
```

2. **Low confidence scores**
```bash
# Lower confidence threshold
# In config.yaml:
extraction:
  min_confidence: 0.5  # Lower from 0.7
```

3. **API rate limits**
```bash
# Check rate limit status
curl https://api.openai.com/v1/rate_limits

# Implement retry logic
# In config.yaml:
extraction:
  max_retries: 3
  retry_delay: 5
```

---

## Performance Issues

### Slow Compilation

**Symptoms:** Compilation taking longer than expected

**Diagnosis:**
```bash
# Check performance metrics
curl http://localhost:9090/metrics | grep duration

# Check CPU usage
top -p $(pgrep -f knowledge-compiler)

# Check I/O wait
iostat -x 1 5
```

**Solutions:**

1. **Enable caching**
```yaml
# In config.yaml:
performance:
  cache_enabled: true
  cache_ttl: 7200  # 2 hours
  l1_cache_size: 2000
  l2_cache_enabled: true
```

2. **Increase parallelism**
```yaml
performance:
  max_workers: 8  # Increase from 4
  batch_size: 50  # Increase from 20
```

3. **Optimize database queries**
```python
# Use query optimization
from src.performance.optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer(wiki_core=wiki)
page = await optimizer.optimize_query_get_page("concept:test")
```

### High Memory Usage

**Symptoms:** Process consuming excessive memory

**Diagnosis:**
```bash
# Check memory usage
ps aux | grep knowledge-compiler
free -h

# Check for memory leaks
valgrind --leak-check=full python -m src.main_cli
```

**Solutions:**

1. **Reduce cache size**
```yaml
performance:
  l1_cache_size: 500  # Reduce from 1000
  l2_cache_enabled: false  # Disable L2 cache
```

2. **Reduce batch size**
```yaml
performance:
  batch_size: 10  # Reduce from 50
  max_workers: 2  # Reduce from 8
```

3. **Enable memory monitoring**
```bash
# Set memory limit
ulimit -v 2097152  # 2GB virtual memory

# Or use cgroups
# In systemd service:
MemoryLimit=2G
```

### Low Cache Hit Rate

**Symptoms:** Cache effectiveness below 50%

**Diagnosis:**
```bash
# Check cache metrics
curl http://localhost:9090/metrics | grep cache

# Expected: cache_hit_rate > 0.70
```

**Solutions:**

1. **Increase cache size**
```yaml
performance:
  l1_cache_size: 2000  # Increase from 1000
```

2. **Increase cache TTL**
```yaml
performance:
  cache_ttl: 14400  # 4 hours instead of 2
```

3. **Optimize cache key patterns**
```python
# Use consistent cache keys
cache.set(f"page:{page_id}", page_data)

# Invalidate strategically
cache.invalidate_pattern("page:*")
```

---

## Quality Issues

### Low Quality Scores

**Symptoms:** Wiki quality score below threshold

**Diagnosis:**
```bash
# Run quality check
python -m src.main_cli --config config.yaml --quality-check

# Check specific issues
python scripts/check_quality.py --detailed
```

**Solutions:**

1. **Fix orphan pages**
```python
# Find orphan pages
from src.wiki.quality.monitor import QualityMonitor
monitor = QualityMonitor(wiki_core=wiki)
orphans = await monitor.check_orphan_pages()

# Add appropriate links
for orphan in orphans:
    wiki.add_relationship(orphan.page_id, "related_concept", "related_to")
```

2. **Fix broken links**
```python
# Find broken links
broken_links = await monitor.check_broken_links()

# Update or remove broken links
for link in broken_links:
    if wiki.page_exists(link.target):
        # Update link
        pass
    else:
        # Remove link
        wiki.remove_relationship(link.from_page, link.target)
```

3. **Update stale content**
```python
# Find stale pages
stale_pages = await monitor.check_staleness(max_age_days=90)

# Review and update
for page in stale_pages:
    # Flag for review
    page.metadata["review_required"] = True
    wiki.update_page(page.id, metadata=page.metadata)
```

### Duplicate Content

**Symptoms:** Similar or duplicate pages detected

**Diagnosis:**
```bash
# Check for duplicates
python scripts/find_duplicates.py --threshold 0.9
```

**Solutions:**

1. **Merge duplicate pages**
```python
# Find duplicates
from src.wiki.quality.monitor import QualityMonitor
monitor = QualityMonitor(wiki_core=wiki)
duplicates = await monitor.check_duplicate_content()

# Merge duplicates
for duplicate_set in duplicates:
    primary = duplicate_set[0]
    for duplicate in duplicate_set[1:]:
        # Merge content
        wiki.merge_pages(primary.id, duplicate.id)
        # Delete duplicate
        wiki.delete_page(duplicate.id)
```

2. **Prevent future duplicates**
```yaml
# Enable duplicate detection
quality:
  duplicate_detection_enabled: true
  duplicate_similarity_threshold: 0.85
```

---

## Monitoring Issues

### Metrics Not Available

**Error:** `Metrics endpoint not responding`

**Diagnosis:**
```bash
# Check if metrics server is running
curl http://localhost:9090/metrics

# Check service logs
grep "metrics" /var/log/knowledge-compiler/compiler.log
```

**Solutions:**

1. **Enable metrics**
```yaml
monitoring:
  metrics_enabled: true
  metrics_port: 9090
```

2. **Check port conflicts**
```bash
# Find process using port
sudo lsof -i :9090

# Change port or stop conflicting service
```

### Alerts Not Firing

**Symptoms:** Expected alerts not being triggered

**Diagnosis:**
```bash
# Check alert rules
python scripts/list_alerts.py

# Check alert history
python scripts/alert_history.py --last 24h
```

**Solutions:**

1. **Verify alert configuration**
```python
# Check alert rule is enabled
from src.monitoring.alerts import AlertManager

manager = AlertManager()
rule = manager.rules.get("alert_name")
print(f"Enabled: {rule.enabled}")

# Check if conditions are met
current_value = get_metric_value()
print(f"Current: {current_value}, Threshold: {rule.threshold}")
```

2. **Check cooldown period**
```bash
# Alerts may be in cooldown
# Check last alert time
python scripts/alert_status.py --alert-name "high_error_rate"
```

3. **Verify notification channels**
```python
# Test notification channel
manager.test_notification("email")
manager.test_notification("webhook")
```

---

## Data Issues

### Data Corruption

**Symptoms:** Unexpected data errors, missing content

**Diagnosis:**
```bash
# Verify data integrity
python scripts/verify_data.py --detailed

# Check database consistency
python scripts/check_db.py --consistency-check
```

**Solutions:**

1. **Restore from backup**
```bash
# Stop service
sudo systemctl stop knowledge-compiler

# Restore backup
tar -xzf wiki-backup-YYYYMMDD.tar.gz -C /

# Restart service
sudo systemctl start knowledge-compiler
```

2. **Repair data**
```python
# Attempt data repair
python scripts/repair_data.py --wiki-path /path/to/wiki
```

### Missing Relationships

**Symptoms:** Concepts not linked properly

**Diagnosis:**
```bash
# Check relationship counts
python scripts/stats.py --relationships

# Find isolated concepts
python scripts/find_isolated.py
```

**Solutions:**

1. **Rebuild relationships**
```python
# Force relationship extraction
from src.discovery.relationships.mapper import RelationshipMapper

mapper = RelationshipMapper(wiki_core=wiki)
mapper.rebuild_relationships()
```

2. **Verify relationship types**
```python
# Check valid relationship types
from src.discovery.relationships.models import RelationshipType

for rel_type in RelationshipType:
    print(rel_type.value)
```

---

## Integration Issues

### LLM API Failures

**Error:** `LLM API request failed`

**Diagnosis:**
```bash
# Test API connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $LLM_API_KEY"

# Check rate limits
curl https://api.openai.com/v1/rate_limits \
  -H "Authorization: Bearer $LLM_API_KEY"
```

**Solutions:**

1. **Verify API key**
```bash
# Check API key is set
echo $LLM_API_KEY

# Reset if needed
export LLM_API_KEY="new-key"
```

2. **Handle rate limits**
```yaml
# In config.yaml:
extraction:
  max_retries: 5  # Increase retries
  retry_delay: 10  # Increase delay
  rate_limit_wait: 60  # Wait when rate limited
```

3. **Use fallback models**
```yaml
# Configure fallback
extraction:
  primary_model: gpt-4
  fallback_model: gpt-3.5-turbo
```

### Database Connection Issues

**Error:** `Database connection failed`

**Diagnosis:**
```bash
# Test database connection
psql -h localhost -U user -d knowledge_compiler

# Check database status
sudo systemctl status postgresql
```

**Solutions:**

1. **Verify connection string**
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
python scripts/test_db.py --test-connection
```

2. **Check database is running**
```bash
# PostgreSQL
sudo systemctl start postgresql

# SQLite
# Check file permissions
ls -la /path/to/database.db
```

3. **Configure connection pool**
```yaml
# In config.yaml:
database:
  pool_size: 20
  max_overflow: 10
  pool_timeout: 30
```

---

## Emergency Procedures

### Complete System Failure

**Symptoms:** System completely unresponsive

**Immediate Actions:**

1. **Check service status**
```bash
sudo systemctl status knowledge-compiler
```

2. **Check system resources**
```bash
free -h
df -h
top
```

3. **Review error logs**
```bash
sudo journalctl -u knowledge-compiler -n 100 --no-pager
tail -100 /var/log/knowledge-compiler/compiler.log
```

4. **Restart service**
```bash
sudo systemctl restart knowledge-compiler
```

### Data Loss Recovery

**Symptoms:** Missing or corrupted data

**Recovery Steps:**

1. **Stop service**
```bash
sudo systemctl stop knowledge-compiler
```

2. **Assess damage**
```bash
# Check data integrity
python scripts/verify_data.py --detailed
```

3. **Restore from backup**
```bash
# Find most recent backup
ls -lt /backup/

# Restore backup
tar -xzf /backup/wiki-latest.tar.gz -C /
```

4. **Restart service**
```bash
sudo systemctl start knowledge-compiler
```

5. **Verify recovery**
```bash
python scripts/verify_data.py
```

### Performance Degradation

**Symptoms:** Sudden performance drop

**Immediate Actions:**

1. **Check metrics**
```bash
curl http://localhost:9090/metrics | grep duration
```

2. **Check system load**
```bash
top
iostat -x 1 5
```

3. **Clear cache**
```bash
# Clear L1 cache
python scripts/clear_cache.py --level l1

# Clear L2 cache
python scripts/clear_cache.py --level l2

# Clear all caches
python scripts/clear_cache.py --all
```

4. **Reduce load**
```yaml
# Temporarily reduce workers
performance:
  max_workers: 1  # Reduce to minimum
  cache_enabled: true
```

5. **Restart service**
```bash
sudo systemctl restart knowledge-compiler
```

---

## Getting Help

### Diagnostic Information Collection

When reporting issues, collect:

```bash
#!/bin/bash
# Collect diagnostic info

OUTPUT="diagnostics-$(date +%Y%m%d-%H%M%S).txt"

{
  echo "=== System Information ==="
  uname -a
  cat /etc/os-release

  echo "=== Python Version ==="
  python --version

  echo "=== Package Versions ==="
  pip list | grep knowledge

  echo "=== Service Status ==="
  systemctl status knowledge-compiler --no-pager

  echo "=== Recent Logs ==="
  journalctl -u knowledge-compiler -n 50 --no-pager

  echo "=== Configuration ==="
  cat /etc/knowledge-compiler/production.yaml

  echo "=== Metrics ==="
  curl -s http://localhost:9090/metrics | head -50

} > $OUTPUT

echo "Diagnostics saved to $OUTPUT"
```

### Support Channels

- **Documentation**: [docs/](docs/)
- **GitHub Issues**: [Create issue](https://github.com/your-org/knowledge-compiler/issues)
- **Email**: support@example.com
- **Slack**: #knowledge-compiler-support

### When Reporting Issues

Include:
1. System information (OS, Python version)
2. Error messages and logs
3. Configuration files (sanitized)
4. Steps to reproduce
5. Expected vs actual behavior
6. Diagnostic output

---

## Prevention

### Regular Maintenance

```bash
#!/bin/bash
# Weekly maintenance script

# 1. Clean old logs
find /var/log/knowledge-compiler -name "*.log" -mtime +30 -delete

# 2. Run quality checks
python -m src.main_cli --config /etc/knowledge-compiler/production.yaml --quality-check

# 3. Backup data
./scripts/backup.sh

# 4. Check disk space
df -h | awk '$5 > 80 {print "Warning: " $1 " is " $5 " full"}'

# 5. Check service health
./scripts/health_check.sh
```

### Monitoring Setup

1. **Set up alerts** for critical metrics
2. **Configure log rotation** to prevent disk fill
3. **Schedule regular backups** of important data
4. **Monitor performance metrics** for trends
5. **Review quality reports** regularly

---

## Additional Resources

- [API Reference](api/api_reference.md) - API documentation
- [User Manual](user_manual.md) - Usage guide
- [Deployment Guide](deployment.md) - Deployment procedures
- [Migration Guide](migration.md) - Version migration

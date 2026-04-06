# Knowledge Compiler Migration Guide

Guide for migrating between versions of Knowledge Compiler.

## Table of Contents

1. [Version Overview](#version-overview)
2. [Migration Prerequisites](#migration-prerequisites)
3. [Migration Procedures](#migration-procedures)
4. [Version-Specific Changes](#version-specific-changes)
5. [Rollback Procedures](#rollback-procedures)
6. [Testing After Migration](#testing-after-migration)
7. [Troubleshooting](#troubleshooting)

---

## Version Overview

### Current Version: v1.0.0

**Release Date:** April 2026

**Major Features:**
- Phase 3: Intelligent Knowledge Accumulation System
- Insight management and propagation
- Quality assurance monitoring
- Performance optimization
- Production monitoring and alerting

### Version History

| Version | Date | Status | Major Changes |
|---------|------|--------|---------------|
| v1.0.0 | 2026-04 | Current | Phase 3 implementation |
| v0.3.0 | 2026-03 | Stable | Phase 2 refinement |
| v0.2.0 | 2026-02 | Stable | Phase 1 initial release |
| v0.1.0 | 2026-01 | Legacy | Proof of concept |

---

## Migration Prerequisites

### Pre-Migration Checklist

- [ ] Read release notes for target version
- [ ] Review breaking changes and deprecations
- [ ] Test migration in development environment
- [ ] Create full backup of production system
- [ ] Schedule maintenance window
- [ ] Prepare rollback plan
- [ ] Update dependencies and requirements
- [ ] Review new configuration options

### System Requirements

**From v0.3.0 to v1.0.0:**
- Python 3.10+ (was 3.9+)
- 2GB RAM minimum (was 1GB)
- Additional disk space for monitoring data

**Breaking Changes:**
- Configuration file format changes
- API changes in insight management
- Database schema updates required

---

## Migration Procedures

### From v0.3.0 to v1.0.0

#### Step 1: Backup Current System

```bash
# Backup wiki data
tar -czf wiki-backup-$(date +%Y%m%d).tar.gz /path/to/wiki

# Backup configuration
cp /etc/knowledge-compiler/production.yaml ~/production.yaml.bak

# Backup database (if using PostgreSQL)
pg_dump knowledge_compiler > db-backup-$(date +%Y%m%d).sql
```

#### Step 2: Update Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Update to latest version
git pull origin main
git checkout v1.0.0

# Update dependencies
pip install --upgrade -r requirements.txt

# Verify installation
python -m pytest tests/ -v
```

#### Step 3: Migrate Configuration

Old configuration format (v0.3.0):

```yaml
source_dir: "./documents"
target_dir: "./wiki"
extraction:
  confidence: 0.6
```

New configuration format (v1.0.0):

```yaml
source_dir: "./documents"
target_dir: "./wiki"
extraction:
  min_confidence: 0.6  # Changed from 'confidence'
  max_concepts: 50      # New parameter

# New sections for v1.0.0
insights:
  enabled: true
  max_hops: 2

quality:
  enabled: true
  max_stale_days: 90

performance:
  cache_enabled: true
  max_workers: 4

monitoring:
  enabled: true
  log_level: INFO
```

#### Step 4: Database Migration

If using PostgreSQL, run migration scripts:

```bash
# Run migration script
python scripts/migrate_db.py --from-version 0.3.0 --to-version 1.0.0

# Verify migration
python scripts/verify_migration.py
```

Manual migration steps:

```sql
-- Add new tables for insights
CREATE TABLE insights (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add new tables for quality monitoring
CREATE TABLE quality_issues (
    id SERIAL PRIMARY KEY,
    issue_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    page_id VARCHAR(255),
    description TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Add new columns for performance tracking
ALTER TABLE pages ADD COLUMN last_accessed TIMESTAMP;
ALTER TABLE pages ADD COLUMN access_count INTEGER DEFAULT 0;
```

#### Step 5: Data Migration

Migrate existing wiki data to new format:

```bash
# Run data migration script
python scripts/migrate_data.py \
  --source /path/to/old/wiki \
  --target /path/to/new/wiki \
  --format v1.0.0
```

#### Step 6: Validate Migration

```bash
# Run validation script
python scripts/validate_migration.py \
  --old-data /path/to/old/wiki \
  --new-data /path/to/new/wiki

# Expected output:
# ✓ All pages migrated successfully
# ✓ All concepts migrated successfully
# ✓ All relationships migrated successfully
# ✓ No data loss detected
```

#### Step 7: Restart Services

```bash
# Stop old service
sudo systemctl stop knowledge-compiler

# Start new service
sudo systemctl start knowledge-compiler

# Verify startup
sudo systemctl status knowledge-compiler
tail -f /var/log/knowledge-compiler/compiler.log
```

---

### From v0.2.0 to v0.3.0

#### Configuration Changes

Add new Phase 2 configuration:

```yaml
# Add discovery settings
discovery:
  enabled: true
  relationship_types:
    - is_a
    - related_to
    - depends_on

# Add analytics settings
analytics:
  enabled: true
  tracking_enabled: true
```

#### Data Migration

```bash
# Migrate to new wiki structure
python scripts/migrate_to_v0.3.0.py --wiki-path /path/to/wiki
```

---

### From v0.1.0 to v0.2.0

**Note:** Direct migration from v0.1.0 is not recommended. Migrate to v0.2.0 via v0.3.0 first.

---

## Version-Specific Changes

### v1.0.0 Breaking Changes

#### 1. Configuration File Format

**Before (v0.3.0):**
```yaml
extraction:
  confidence: 0.6
```

**After (v1.0.0):**
```yaml
extraction:
  min_confidence: 0.6  # Parameter renamed
  max_concepts: 50      # New parameter
```

#### 2. Insight Management API

**Before (v0.3.0):**
```python
# Old API (removed)
manager.create_insight(title, description)
```

**After (v1.0.0):**
```python
# New API (required parameters)
manager.create_insight(
    title=title,
    description=description,
    related_concepts=[...],  # Required
    impact_score=0.8,        # Required
    novelty_score=0.7,       # Required
    actionability_score=0.9  # Required
)
```

#### 3. Quality Monitoring

**Before (v0.3.0):**
```python
# Old API (removed)
monitor.check_quality()
```

**After (v1.0.0):**
```python
# New API (async required)
await monitor.run_health_check()
```

### v1.0.0 New Features

#### Insight Management

```python
# New insight propagation
manager.propagate_insight(insight, max_hops=2)

# New insight scheduling
manager.schedule_insight(insight)

# New insight backfill
manager.backfill_insights()
```

#### Quality Assurance

```python
# New quality monitoring
monitor = QualityMonitor(wiki_core=wiki)
result = await monitor.run_health_check()

# New issue classification
classifier = IssueClassifier()
classified = classifier.classify_issue(issue)
```

#### Performance Optimization

```python
# New caching system
cache = CacheManager(l1_max_size=1000, l2_enabled=True)

# New query optimization
optimizer = PerformanceOptimizer(wiki_core=wiki, cache_manager=cache)
page = await optimizer.optimize_query_get_page("concept:test")
```

#### Monitoring and Alerting

```python
# New structured logging
logger = get_logger("my_module", log_file="app.log")

# New metrics collection
registry = get_metrics_registry()
counter = registry.counter("documents_processed", "Total documents")

# New alert management
alert_manager = AlertManager()
alert_manager.add_rule(rule)
```

---

## Rollback Procedures

### Emergency Rollback

If migration fails, rollback to previous version:

```bash
#!/bin/bash
# Rollback script

# Stop current service
sudo systemctl stop knowledge-compiler

# Restore previous version
git checkout v0.3.0

# Restore dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Restore data
tar -xzf wiki-backup-YYYYMMDD.tar.gz -C /

# Restore configuration
cp ~/production.yaml.bak /etc/knowledge-compiler/production.yaml

# Restore database (if using PostgreSQL)
psql knowledge_compiler < db-backup-YYYYMMDD.sql

# Restart service
sudo systemctl start knowledge-compiler

# Verify rollback
./scripts/health_check.sh
```

### Partial Rollback

If only certain components need rollback:

```bash
# Rollback configuration only
cp ~/production.yaml.bak /etc/knowledge-compiler/production.yaml
sudo systemctl reload knowledge-compiler

# Rollback data only
tar -xzf wiki-backup-YYYYMMDD.tar.gz -C /path/to/wiki
sudo systemctl restart knowledge-compiler
```

---

## Testing After Migration

### Pre-Deployment Testing

```bash
# 1. Run unit tests
python -m pytest tests/ -v

# 2. Run integration tests
python -m pytest tests/test_integration.py -v

# 3. Run quality checks
python -m src.main_cli --config config.yaml --quality-check

# 4. Run performance benchmarks
python scripts/benchmark.py --config config.yaml
```

### Post-Deployment Validation

```bash
# 1. Verify service status
sudo systemctl status knowledge-compiler

# 2. Check logs for errors
tail -f /var/log/knowledge-compiler/compiler.log

# 3. Verify metrics endpoint
curl http://localhost:9090/metrics

# 4. Test basic operations
python scripts/test_migration.py --config /etc/knowledge-compiler/production.yaml

# 5. Verify data integrity
python scripts/verify_data.py --wiki-path /path/to/wiki
```

### Performance Validation

Compare performance metrics before and after migration:

```python
import requests
import time

# Query metrics endpoint
response = requests.get('http://localhost:9090/metrics')
metrics = response.text

# Check key metrics
expected_metrics = [
    'documents_processed_total',
    'processing_duration_seconds',
    'cache_hit_rate',
    'error_rate'
]

for metric in expected_metrics:
    if metric in metrics:
        print(f"✓ {metric} is available")
    else:
        print(f"✗ {metric} is missing")
```

---

## Troubleshooting

### Common Migration Issues

#### 1. Configuration Validation Errors

**Error:** `Configuration validation failed`

**Solution:**
```bash
# Validate configuration
python -m src.main_cli --config config.yaml --validate

# Fix reported errors and retry
```

#### 2. Database Migration Failures

**Error:** `Database migration failed`

**Solution:**
```bash
# Check database connection
psql -h localhost -U user -d knowledge_compiler

# Run migration manually
psql knowledge_compiler < scripts/migration.sql

# Verify migration
python scripts/verify_db_migration.py
```

#### 3. Data Migration Errors

**Error:** `Data migration incomplete`

**Solution:**
```bash
# Check migration logs
tail -f /var/log/knowledge-compiler/migration.log

# Re-run migration with verbose output
python scripts/migrate_data.py --verbose

# Verify data integrity
python scripts/verify_data.py --detailed
```

#### 4. Performance Degradation

**Error:** System slower after migration

**Solution:**
```bash
# Check cache configuration
curl http://localhost:9090/metrics | grep cache

# Optimize cache settings
# Update config.yaml with appropriate cache sizes

# Restart service
sudo systemctl restart knowledge-compiler
```

### Getting Help

If you encounter issues during migration:

1. **Check logs:** Review `/var/log/knowledge-compiler/compiler.log`
2. **Validate configuration:** Use `--validate` flag
3. **Run diagnostics:** `python scripts/diagnose.py`
4. **Check documentation:** Review relevant sections
5. **Report issues:** Create GitHub issue with details

Include in your report:
- Version migrating from and to
- Error messages and logs
- Configuration files
- System information
- Steps taken before error

---

## Additional Resources

- [Release Notes](RELEASE_NOTES.md) - Detailed version changes
- [API Reference](api/api_reference.md) - API documentation
- [Deployment Guide](deployment.md) - Deployment procedures
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions

---

## Best Practices

1. **Test First:** Always test migration in development environment
2. **Backup Everything:** Create full backups before migration
3. **Document Changes:** Keep record of all changes made
4. **Monitor Closely:** Watch system metrics after migration
5. **Plan Rollback:** Have rollback plan ready before starting
6. **Schedule Maintenance:** Use low-traffic periods for migration
7. **Validate Thoroughly:** Run comprehensive tests after migration
8. **Monitor Performance:** Compare metrics before and after migration

---

## Support

For migration assistance:
- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/your-org/knowledge-compiler/issues)
- Email: support@example.com
- Slack: #knowledge-compiler-support

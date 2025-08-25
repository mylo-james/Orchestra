# Epic 1: Rollback Procedures

## Overview

This document provides comprehensive rollback procedures for Epic 1's BMad resource infrastructure, ensuring safe recovery from any issues with the resource system deployment.

## Rollback Scenarios

### Scenario 1: Emergency Full Rollback

**When to Use**: Critical system failure, widespread resource loading issues, performance degradation

**Steps**:
1. **Immediate Actions** (< 2 minutes)
   ```bash
   # Disable entire resource system
   export ORCHESTRA_RESOURCE_SYSTEM_ENABLED=false

   # Restart Orchestra services
   sudo systemctl restart orchestra
   # OR for Docker deployment
   docker-compose restart orchestra
   ```

2. **Verification** (< 5 minutes)
   ```bash
   # Verify fallback to v0.1.0 behavior
   orchestra status
   orchestra agent --help  # Should show original 3 personas only
   ```

3. **Monitoring** (Ongoing)
   - Monitor service health endpoints
   - Verify original functionality restored
   - Check logs for fallback success

### Scenario 2: Partial Component Rollback

**When to Use**: Specific component issues (overlay system, namespaces, etc.)

#### 2a. Persona Overlay System Rollback
```bash
# Disable overlay merging, keep base resource system
export ORCHESTRA_OVERLAY_SYSTEM_ENABLED=false
sudo systemctl restart orchestra
```

**Impact**: Base personas only, no team/project customization

#### 2b. Namespaced Storage Rollback
```bash
# Disable project isolation, use single namespace
export ORCHESTRA_NAMESPACED_STORAGE_ENABLED=false
sudo systemctl restart orchestra
```

**Impact**: Single namespace storage, no project isolation

#### 2c. Hot-Reload System Rollback
```bash
# Disable hot-reload, require restart for changes
export ORCHESTRA_HOT_RELOAD_ENABLED=false
sudo systemctl restart orchestra
```

**Impact**: Static resource loading, restart required for updates

### Scenario 3: Graceful Planned Rollback

**When to Use**: Planned maintenance, systematic rollback for fixes

**Steps**:
1. **Pre-rollback Preparation**
   - Notify users of planned maintenance
   - Backup current resource configurations
   - Document current system state

2. **Configuration Update**
   ```bash
   # Update configuration file
   vim /etc/orchestra/config.yaml
   # Set feature_flags.resource_system_enabled: false
   ```

3. **Staged Rollback**
   ```bash
   # Rolling restart (if multiple instances)
   for instance in orchestra-1 orchestra-2 orchestra-3; do
     systemctl restart $instance
     sleep 30  # Allow health checks
   done
   ```

4. **Validation**
   - Run health checks
   - Verify v0.1.0 functionality
   - Monitor performance metrics

## Data Preservation

### Resource System Data
- **BMad Content**: Preserved in `.bmad-core/` directory
- **Team/Project Overlays**: Preserved in `teams/` and `projects/` directories
- **Resource Configurations**: Preserved for future re-enablement

### Storage Rollback
- **Qdrant Collections**: Namespaced collections preserved
- **PostgreSQL Schemas**: Project schemas preserved
- **Logs**: Structured logs with namespace info preserved

## Recovery Procedures

### Re-enabling After Rollback

1. **Verify Issues Resolved**
   - Address root cause of rollback
   - Test fixes in development environment
   - Validate resource configurations

2. **Gradual Re-enablement**
   ```bash
   # Start with base resource system only
   export ORCHESTRA_RESOURCE_SYSTEM_ENABLED=true
   export ORCHESTRA_OVERLAY_SYSTEM_ENABLED=false
   export ORCHESTRA_NAMESPACED_STORAGE_ENABLED=false

   # Restart and verify
   systemctl restart orchestra
   # Monitor for issues
   ```

3. **Progressive Feature Enablement**
   ```bash
   # Enable overlay system if stable
   export ORCHESTRA_OVERLAY_SYSTEM_ENABLED=true
   systemctl restart orchestra

   # Enable namespaced storage if stable
   export ORCHESTRA_NAMESPACED_STORAGE_ENABLED=true
   systemctl restart orchestra
   ```

## Monitoring During Rollback

### Key Metrics to Watch
- **Service Availability**: Health endpoint responses
- **Persona Loading**: Time to load personas (should return to <500ms)
- **Memory Usage**: Should decrease to v0.1.0 baseline (≤4GB)
- **Error Rates**: Should decrease after rollback
- **CLI Responsiveness**: Commands should respond normally

### Alerting Thresholds
- **Service Down**: > 30 seconds unavailability
- **High Error Rate**: > 5% error rate after rollback
- **Memory Usage**: > 4GB sustained usage
- **Response Time**: > 1000ms persona loading

## Communication Templates

### Emergency Rollback Notification
```
URGENT: Orchestra Resource System Rollback

Impact: Orchestra has been rolled back to v0.1.0 functionality
Duration: Immediate, investigating issue
Service Status: Available with reduced functionality

Actions:
- Resource system disabled
- Base personas only (orchestrator, dev, release)
- Team/project customizations temporarily unavailable

Updates: Will provide updates every 15 minutes
```

### Recovery Notification
```
Orchestra Resource System Recovery

Status: Resource system re-enabled successfully
Impact: Full functionality restored
Monitoring: Increased monitoring for 24 hours

Available Features:
- All BMad personas and resources
- Team/project customizations
- Full resource management capabilities
```

## Troubleshooting

### Common Rollback Issues

1. **Services Won't Start After Rollback**
   - Check configuration file syntax
   - Verify environment variables are set correctly
   - Check file permissions on configuration files

2. **Original Personas Not Loading**
   - Verify original YAML files are intact
   - Check PersonaLoader fallback logic
   - Restart with clean cache

3. **Performance Still Degraded**
   - Clear resource cache: `rm -rf /tmp/orchestra-cache/*`
   - Restart database connections
   - Verify no resource loading code paths active

### Emergency Contacts
- **System Administrator**: [Contact Info]
- **Development Team Lead**: [Contact Info]
- **Product Owner**: [Contact Info]

## Testing Rollback Procedures

### Regular Rollback Drills
- **Monthly**: Test emergency rollback procedure
- **Quarterly**: Test partial component rollbacks
- **Annually**: Full disaster recovery simulation

### Test Validation
- [ ] Services start successfully after rollback
- [ ] Original v0.1.0 functionality works
- [ ] Performance returns to baseline
- [ ] No data loss occurs
- [ ] Recovery procedures work as documented

---

## References
- [Epic 1 Feature Flags](./epic-1-feature-flags.md) - Feature flag configuration
- [Epic 1 Stories](./stories/completed/epic-1/) - Implementation details
- [Current Implementation](./current-implementation.md) - v0.1.0 baseline behavior
- [Infrastructure Recovery](./infrastructure-recovery-procedures.md) - General recovery procedures

---
*Epic 1 Documentation Enhancement - January 27, 2025*

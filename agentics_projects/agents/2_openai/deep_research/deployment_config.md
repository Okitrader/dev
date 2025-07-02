# Deep Research System - Production Deployment Configuration

## Environment Variables

### Phase 1: Initial Safe Deployment
```bash
# Architecture Control
export USE_NEW_ARCHITECTURE=false          # Keep old architecture as default
export SHADOW_MODE_PERCENTAGE=0.1          # 10% shadow mode testing
export SHADOW_MODE_ENABLED=true            # Enable shadow comparisons

# Performance Monitoring
export PERFORMANCE_LOG_LEVEL=INFO          # Log performance metrics
export PERFORMANCE_DATA_DIR=/var/log/deep_research/performance
export PERFORMANCE_RETENTION_DAYS=90       # Keep 90 days of data

# Feature Flags
export UI_TOGGLE_ENABLED=false             # Initially disable UI toggle
export BETA_USER_PERCENTAGE=0              # No beta users initially

# Cache Configuration
export CACHE_TTL_HOURS=24                  # Cache for 24 hours
export CACHE_MAX_SIZE_MB=100               # Limit cache to 100MB
export CACHE_ENABLED=true                  # Enable caching

# Error Handling
export ERROR_RETRY_ENABLED=true            # Enable automatic retries
export ERROR_MAX_RETRIES=3                 # Maximum retry attempts
export ERROR_BACKOFF_BASE=1.5              # Exponential backoff base

# API Keys (from secure store)
export OPENAI_API_KEY=${OPENAI_API_KEY}
export SERPER_API_KEY=${SERPER_API_KEY}
export SENDGRID_API_KEY=${SENDGRID_API_KEY}
export LANGSMITH_API_KEY=${LANGSMITH_API_KEY}  # Optional
```

### Phase 2: Beta Release (Day 5-7)
```bash
export UI_TOGGLE_ENABLED=true              # Enable UI toggle
export BETA_USER_PERCENTAGE=5              # 5% initial beta
```

### Phase 3: Expanded Beta (After 24h)
```bash
export BETA_USER_PERCENTAGE=25             # Expand to 25%
```

### Phase 4: Full Rollout (After validation)
```bash
export USE_NEW_ARCHITECTURE=true           # Switch default to new
export UI_TOGGLE_ENABLED=true              # Keep toggle for user choice
export SHADOW_MODE_PERCENTAGE=0            # Disable shadow mode
```

## Monitoring Endpoints

### Health Check
- **Endpoint**: `/health`
- **Expected**: `{"status": "healthy", "architecture": "old|new"}`

### Metrics
- **Endpoint**: `/metrics`
- **Format**: Prometheus-compatible
- **Key Metrics**:
  - `deep_research_query_duration_seconds`
  - `deep_research_quality_score`
  - `deep_research_cache_hit_rate`
  - `deep_research_error_rate`

### Performance Comparison
- **Endpoint**: `/api/performance/shadow`
- **Returns**: Shadow mode comparison data

## Deployment Checklist

### Pre-Deployment
- [ ] All environment variables configured
- [ ] API keys secured in vault
- [ ] Performance data directory created
- [ ] Monitoring infrastructure ready
- [ ] Database migrations complete (if needed)

### Deployment Steps
1. Deploy code with feature flags disabled
2. Verify health check endpoint
3. Enable shadow mode monitoring
4. Monitor for 24-48 hours
5. Review shadow mode data
6. Enable beta for select users
7. Monitor adoption and feedback
8. Gradual rollout to all users

### Rollback Triggers
- Performance degradation >20%
- Error rate increase >5%
- Quality score drop >10%
- Memory usage increase >50%
- User complaints spike

### Rollback Procedure
```bash
# Immediate rollback
export USE_NEW_ARCHITECTURE=false
export UI_TOGGLE_ENABLED=false

# If needed, full rollback
kubectl rollback deployment/deep-research --to-revision=PREVIOUS
```

## Success Criteria

### Day 1-2
- Zero increase in error rates
- Shadow mode executing successfully
- All health checks passing
- Performance data collecting

### Day 3-4
- Shadow mode shows ≥20% speed improvement
- Quality scores equal or better
- No memory leaks detected
- Cache hit rate >30%

### Day 5-7 (Beta)
- >50% voluntary adoption among beta users
- Positive user feedback
- No critical issues reported
- Performance improvements confirmed

### Full Rollout
- ≥30% execution time reduction
- ≥15% quality score improvement
- ≥60% user adoption
- ≥25% API cost reduction
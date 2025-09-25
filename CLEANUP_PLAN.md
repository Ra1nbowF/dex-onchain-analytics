# Project Cleanup Plan

## KEEP - Essential Files

### Core Monitors (Currently Active)
- `main.py` - Moralis monitor (actively used)
- `bsc_pool_monitor.py` - BSC pool monitor (actively used)
- `collector.py` - Orchestrator (actively used)

### Database Testing/Management (Needed)
- `check_railway_data.py` - Check Railway database status
- `check_buy_sell_volume.py` - Volume data verification
- `check_volume.py` - Volume analysis
- `test_monitors_locally.py` - Local testing utility
- `create_all_tables_for_railway.sql` - Database schema
- `create_missing_tables_railway.py` - Table creation utility
- `fix_buy_sell_volume.py` - Data fix utility
- `fix_railway_constraints.py` - Constraint management
- `fix_railway_tables_final.py` - Table structure fixes

### Active Grafana Dashboard
- `grafana/moralis-bsc-dashboard.json` - Main dashboard (currently viewing)
- `grafana/bsc-dashboard-fixed.json` - BSC specific dashboard

### Configuration
- `docker-compose.yml` - Docker setup
- `railway.json` - Railway deployment config
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (if exists)
- `PROJECT_DOCUMENTATION.md` - Comprehensive documentation

---

## REMOVE - Redundant/Backup Files

### Backup Python Files
- `collector_backup.py` - Backup
- `collector_monitors.py` - Old version
- `main_backup.py` - Backup
- `main_monitor.py` - Old version
- `railway_collector.py` - Duplicate
- `railway_monitor.py` - Old version
- `run_monitors.py` - Unused
- `start.py` - Old starter

### Old Moralis Monitor Versions
- `moralis_bsc_monitor.py` - Old version
- `moralis_bsc_monitor_fixed.py` - Old fix
- `moralis_complete_fixed.py` - Old version
- `moralis_complete_monitor.py` - Old version
- `moralis_correct_monitor.py` - Old version
- `moralis_enhanced_monitor.py` - Old version
- `moralis_enhanced_monitor_fixed.py` - Old fix
- `moralis_final_monitor.py` - Merged into main.py
- `moralis_token_analytics_final.py` - Old version
- `moralis_token_analytics_fixed.py` - Old fix
- `moralis_working_monitor.py` - Old version

### One-time Migration/Setup Scripts
- `migrate_to_railway.py` - Already migrated
- `migrate_to_railway_auto.py` - Already migrated
- `create_tables_railway.py` - Old version
- `create_tables_railway_new.py` - Old version
- `add_timeseries_data.py` - Test data, not needed
- `fix_missing_data.py` - One-time fix
- `fix_railway_views.py` - One-time fix
- `verify_railway_db.py` - One-time verification
- `verify_railway_deployment.py` - One-time check

### Test Scripts (No longer needed)
- `test_missing_data.py` - One-time test
- `test_moralis_api.py` - API tested
- `test_moralis_endpoints.py` - Endpoints tested
- `test_railway_connection.py` - Connection works
- `test_token_stats_fix.py` - Fixed already
- `test_top_gainers_fix.py` - Fixed already

### Redundant Grafana Dashboards
- `grafana/bsc-pool-dashboard.json` - Duplicate of bsc-dashboard-fixed
- `grafana/consolidated-dashboard.json` - Old consolidation
- `grafana/dex-analytics-dashboard.json` - Old version
- `grafana/moralis-complete-dashboard.json` - Old version
- `grafana/moralis-corrected-dashboard.json` - Old version
- `grafana/moralis-dashboard-fixed.json` - Old fix
- `grafana/moralis-enhanced-dashboard.json` - Old version
- `grafana/moralis-rich-data-dashboard.json` - Old version
- `grafana/moralis-working-dashboard.json` - Old version

---

## Summary
- **Keep**: 20 files (core functionality + testing utilities)
- **Remove**: 44 files (backups, old versions, one-time scripts)
# Project Structure - DEX On-Chain Analytics

## Clean Project Organization (After Cleanup)

### 📁 Root Directory Files

#### Core Monitoring Services (3 files)
```
├── main.py                    # Moralis Web3 API monitor (10-min intervals)
├── bsc_pool_monitor.py        # BSC direct RPC monitor (60-sec intervals)
└── collector.py               # Orchestrator that runs both monitors
```

#### Database Testing & Management (6 files)
```
├── check_railway_data.py      # Check Railway database status and data
├── check_buy_sell_volume.py   # Verify buy/sell volume data collection
├── check_volume.py            # Analyze volume metrics
├── create_missing_tables_railway.py  # Create missing database tables
├── fix_buy_sell_volume.py     # Fix volume data issues
├── fix_railway_constraints.py # Add missing database constraints
└── fix_railway_tables_final.py # Final table structure fixes
```

#### Local Testing (1 file)
```
└── test_monitors_locally.py   # Test monitors with Railway database locally
```

### 📁 Grafana Dashboards (2 files)
```
grafana/
├── moralis-bsc-dashboard.json # Main combined dashboard (active)
└── bsc-dashboard-fixed.json   # BSC-specific metrics dashboard
```

### 📁 Configuration Files
```
├── docker-compose.yml         # Docker services configuration
├── railway.json              # Railway deployment configuration
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (if exists)
├── .gitignore               # Git ignore rules
└── create_all_tables_for_railway.sql  # Complete database schema
```

### 📁 Documentation
```
├── PROJECT_DOCUMENTATION.md  # Comprehensive project documentation
├── PROJECT_STRUCTURE.md     # This file - project organization
├── CLEANUP_PLAN.md          # Cleanup execution plan
└── database_schema_complete.md # Database schema documentation
```

---

## File Categories and Purposes

### 🚀 Production Files (Essential)
- **main.py**: Fetches data from 9 Moralis endpoints
- **bsc_pool_monitor.py**: Direct blockchain monitoring
- **collector.py**: Manages both monitors with health checks

### 🧪 Testing & Debugging
- **check_*.py files**: Verify specific data aspects
- **test_monitors_locally.py**: Local testing capability

### 🔧 Database Management
- **create_missing_tables_railway.py**: Table creation
- **fix_*.py files**: Data and structure corrections

### 📊 Visualization
- **moralis-bsc-dashboard.json**: All metrics in one dashboard
- **bsc-dashboard-fixed.json**: Pool-specific metrics

---

## Removed Files Summary

### ❌ Removed Categories:
1. **44 redundant files** deleted including:
   - 11 old Moralis monitor versions
   - 9 redundant Grafana dashboards
   - 8 backup files
   - 6 one-time migration scripts
   - 6 completed test scripts
   - 4 old orchestrator versions

### 💾 Space Saved:
- Approximately 2.5 MB of redundant code
- Reduced file count from 55 to 11 Python files
- Reduced dashboards from 11 to 2

---

## Quick Reference

### To Run the System:
```bash
# Production (Railway)
python collector.py

# Local Testing
python test_monitors_locally.py

# Individual Monitors
python main.py              # Moralis monitor
python bsc_pool_monitor.py  # BSC monitor
```

### To Check Data:
```bash
python check_railway_data.py      # Overall status
python check_buy_sell_volume.py   # Volume verification
python check_volume.py             # Volume analysis
```

### To Fix Issues:
```bash
python create_missing_tables_railway.py  # Missing tables
python fix_railway_constraints.py        # Constraints
python fix_buy_sell_volume.py           # Volume data
python fix_railway_tables_final.py      # Table structure
```

---

## Environment Variables Required

```bash
DATABASE_URL=postgresql://user:pass@host:port/database
MORALIS_API_KEY=your_moralis_api_key
MONITOR_INTERVAL_MINUTES=10  # Optional, default 10
ETHERSCAN_API_KEY=your_bscscan_key  # For BSC monitor
```

---

*Project cleaned and organized on: September 2024*
*Files reduced from 55 to 11 essential files*
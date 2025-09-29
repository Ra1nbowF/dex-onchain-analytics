# AWS Free Tier Deployment Guide for DEX Analytics Backend

## AWS Free Tier Suitability Assessment

### ✅ **YES, AWS Free Tier IS SUITABLE** for your backend with some considerations:

## Free Tier Resources Available

### 1. **EC2 (Compute)**
- **750 hours/month** of t2.micro or t3.micro instance (12 months)
- 1 vCPU, 1 GB RAM
- **Suitable for**: Your Python monitors, scripts
- **Limitation**: Low memory, may need optimization

### 2. **RDS (Database)**
- **750 hours/month** of db.t2.micro/db.t3.micro/db.t4g.micro
- 20 GB storage
- **Current Issue**: You use Railway PostgreSQL
- **Solution**: Migrate to AWS RDS PostgreSQL

### 3. **Lambda (Serverless)**
- **1 million requests/month FREE forever**
- 400,000 GB-seconds compute time
- **Perfect for**: Scheduled monitors, API endpoints

### 4. **S3 (Storage)**
- 5 GB standard storage
- **Use for**: Storing logs, backups

## Recommended Architecture for Free Tier

### Option 1: EC2 + RDS (Traditional)
```
┌─────────────────┐
│   EC2 t3.micro  │
│  - BSC Monitor  │
│  - API Server   │
│  - Schedulers   │
└────────┬────────┘
         │
┌────────▼────────┐
│  RDS PostgreSQL │
│   db.t3.micro   │
│    20GB SSD     │
└─────────────────┘
```

### Option 2: Lambda + RDS (Serverless) - RECOMMENDED
```
┌─────────────────┐
│  Lambda Functions│
│  - BSC Monitor  │──► CloudWatch Events
│  - Data Fetcher │    (Scheduled triggers)
│  - API Handler  │
└────────┬────────┘
         │
┌────────▼────────┐
│  RDS PostgreSQL │
│   db.t3.micro   │
└─────────────────┘
```

## Current Backend Analysis

### Your Components:
1. **BSC Pool Monitor** - Fetches blockchain data
2. **Moralis Monitor** - API data collection
3. **PostgreSQL Database** - Currently on Railway
4. **Python Scripts** - Various data processors

### Resource Requirements:
- **CPU**: Low (script-based)
- **Memory**: ~512MB-1GB per monitor
- **Storage**: Growing with historical data
- **Network**: API calls to BSC/Moralis

## Deployment Steps

### Prerequisites
1. AWS Account with free tier
2. AWS CLI installed
3. Docker installed locally

### Step 1: Prepare Application

Create `application.py` for Flask API:
```python
from flask import Flask, jsonify
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/swaps')
def get_swaps():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT * FROM bsc_trades ORDER BY timestamp DESC LIMIT 50")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@app.route('/api/transfers')
def get_transfers():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT * FROM bsc_token_transfers ORDER BY timestamp DESC LIMIT 50")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Step 2: Update Requirements
```txt
# Add to requirements.txt
Flask==3.0.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
boto3==1.28.84
```

### Step 3: Create Dockerfile for AWS
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# For EC2
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "application:app"]

# For Lambda (use different base image)
# CMD ["lambda_handler.handler"]
```

### Step 4: Lambda Function Setup

Create `lambda_handler.py`:
```python
import json
import psycopg2
import os
from datetime import datetime

def handler(event, context):
    """AWS Lambda handler for scheduled monitors"""

    DATABASE_URL = os.environ.get('DATABASE_URL')

    # Determine which monitor to run
    monitor_type = event.get('monitor', 'bsc_trades')

    if monitor_type == 'fetch_transfers':
        # Run transfer fetcher
        from fetch_bscscan_transfers import fetch_transfers_no_api
        fetch_transfers_no_api()

    elif monitor_type == 'populate_trades':
        # Run trade populator
        from populate_bsc_trades import main
        main()

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Monitor {monitor_type} completed',
            'timestamp': datetime.now().isoformat()
        })
    }
```

### Step 5: Deployment Script

Create `deploy_to_aws.sh`:
```bash
#!/bin/bash

# Configuration
AWS_REGION="us-east-1"
ECR_REPO_NAME="dex-analytics"
LAMBDA_FUNCTION="dex-monitor"

# 1. Create ECR repository
aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION

# 2. Get login token
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com

# 3. Build and push Docker image
docker build -t $ECR_REPO_NAME .
docker tag $ECR_REPO_NAME:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

# 4. Deploy to Lambda or EC2
echo "Deploy complete!"
```

### Step 6: Database Migration

Create `migrate_to_rds.py`:
```python
import psycopg2
from psycopg2.extras import RealDictCursor

# Source (Railway)
SOURCE_DB = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

# Target (AWS RDS)
TARGET_DB = "postgresql://username:password@your-rds-endpoint.amazonaws.com:5432/dexanalytics"

def migrate_table(table_name):
    """Migrate a single table"""
    source_conn = psycopg2.connect(SOURCE_DB)
    target_conn = psycopg2.connect(TARGET_DB)

    source_cur = source_conn.cursor(cursor_factory=RealDictCursor)
    target_cur = target_conn.cursor()

    # Get table structure
    source_cur.execute(f"SELECT * FROM {table_name} LIMIT 0")
    columns = [desc[0] for desc in source_cur.description]

    # Copy data
    source_cur.execute(f"SELECT * FROM {table_name}")
    for row in source_cur:
        placeholders = ','.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
        target_cur.execute(insert_query, list(row.values()))

    target_conn.commit()
    print(f"Migrated {table_name}")

# Migrate all tables
tables = ['bsc_trades', 'bsc_token_transfers', 'bsc_liquidity_events']
for table in tables:
    migrate_table(table)
```

## Cost Optimization Tips

### 1. **Use Lambda instead of EC2**
- No idle time charges
- Auto-scaling
- 1M requests free forever

### 2. **Schedule monitors efficiently**
- Run every 5-10 minutes instead of continuously
- Use CloudWatch Events for scheduling

### 3. **Optimize database**
- Use RDS proxy for connection pooling
- Enable auto-pause for development

### 4. **Monitor usage**
- Set up billing alerts at $1, $5
- Use AWS Cost Explorer

## Limitations & Solutions

### Limitations:
1. **Memory**: 1GB on t3.micro
2. **Storage**: 20GB RDS limit
3. **Compute**: Limited CPU credits

### Solutions:
1. **Memory**: Use Lambda (3GB available)
2. **Storage**: Archive old data to S3
3. **Compute**: Optimize code, use async

## Free Tier Timeline

### First 12 months (FREE):
- EC2: 750 hrs/month
- RDS: 750 hrs/month
- S3: 5GB storage

### After 12 months:
- Lambda: Still 1M requests free
- S3: Still 5GB free
- EC2/RDS: ~$10-20/month each

## Estimated Monthly Cost After Free Tier

| Service | Usage | Cost |
|---------|-------|------|
| EC2 t3.micro | 24/7 | $7.50 |
| RDS db.t3.micro | 24/7 | $12.50 |
| Lambda | 100k requests | FREE |
| S3 | 5GB | FREE |
| **Total** | | **$20/month** |

## Alternative: Use Lambda Only (Best for Free Tier)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 1M requests | FREE |
| RDS db.t3.micro | 24/7 | $12.50 |
| S3 | 5GB | FREE |
| **Total after free tier** | | **$12.50/month** |

## Next Steps

1. **Create AWS Account** (if not already)
2. **Set up RDS PostgreSQL** in free tier
3. **Migrate database** from Railway
4. **Deploy Lambda functions** for monitors
5. **Set up CloudWatch** schedules
6. **Configure API Gateway** for REST API

## Commands to Get Started

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier dex-analytics-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username admin \
    --master-user-password YourPassword123! \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxx

# Create Lambda function
aws lambda create-function \
    --function-name dex-monitor \
    --runtime python3.10 \
    --role arn:aws:iam::ACCOUNT:role/lambda-role \
    --handler lambda_handler.handler \
    --zip-file fileb://function.zip
```

## Security Considerations

1. **Use Parameter Store** for secrets
2. **Enable RDS encryption**
3. **Use VPC for internal communication**
4. **Set up IAM roles properly**
5. **Enable CloudWatch logging**

## Monitoring Setup

1. **CloudWatch Dashboards** - Free tier includes 3 dashboards
2. **SNS Alerts** - 1,000 notifications free
3. **X-Ray tracing** - 100,000 traces free

## Support & Resources

- [AWS Free Tier](https://aws.amazon.com/free/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [RDS PostgreSQL Guide](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)

---

**Recommendation**: Start with Lambda + RDS setup for maximum free tier usage and scalability!
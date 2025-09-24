#!/bin/bash

echo "==========================================="
echo "DEX Onchain Analytics - Docker Setup"
echo "==========================================="
echo

echo "Step 1: Stopping any existing containers..."
docker-compose down

echo
echo "Step 2: Building and starting containers..."
docker-compose up -d postgres redis

echo
echo "Step 3: Waiting for database to be ready..."
sleep 10

echo
echo "Step 4: Starting data collector..."
docker-compose up -d dex_collector

echo
echo "==========================================="
echo "Setup Complete!"
echo "==========================================="
echo
echo "PostgreSQL is running on: localhost:5433"
echo "Redis is running on: localhost:6380"
echo
echo "To add the dashboard to Grafana:"
echo "1. Open Grafana at http://localhost:3000"
echo "2. Add PostgreSQL data source:"
echo "   - Host: host.docker.internal:5433"
echo "   - Database: dex_analytics"
echo "   - User: postgres"
echo "   - Password: postgres"
echo "   - SSL Mode: disable"
echo "3. Import dashboard from: grafana/dex-analytics-dashboard.json"
echo
echo "To view logs: docker-compose logs -f dex_collector"
echo "To stop: docker-compose down"
echo
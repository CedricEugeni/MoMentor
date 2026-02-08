#!/bin/bash
# Script to view SQLite database content

echo "🗄️  MoMentor Database Content"
echo "================================"
echo ""

# Check if container is running
if ! docker ps | grep -q momentor-backend; then
    echo "❌ Backend container not running!"
    echo "Start it with: docker-compose up"
    exit 1
fi

echo "📊 Algorithm Runs:"
docker exec momentor-backend sqlite3 /app/database/momentor.db "SELECT id, run_date, trigger_type, status, total_capital_usd FROM algorithm_runs ORDER BY run_date DESC;"
echo ""

echo "📈 Actual Positions:"
docker exec momentor-backend sqlite3 /app/database/momentor.db "SELECT run_id, symbol, actual_shares, actual_avg_price_usd FROM actual_positions;"
echo ""

echo "💰 Actual Cash:"
docker exec momentor-backend sqlite3 /app/database/momentor.db "SELECT run_id, uninvested_cash_usd FROM actual_cash;"
echo ""

echo "💾 Price Cache entries:"
docker exec momentor-backend sqlite3 /app/database/momentor.db "SELECT COUNT(*) as count FROM price_cache;"
echo ""

echo "✅ Done! For interactive access, run:"
echo "   docker exec -it momentor-backend sqlite3 /app/database/momentor.db"

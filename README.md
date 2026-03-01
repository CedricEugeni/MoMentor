# MoMentor - Momentum Portfolio Mentor

> **Version 1.0** - Your automated momentum investing assistant for US stocks

MoMentor is a momentum investing strategy mentor for US stocks. It generates monthly portfolio recommendations using the **MomentumVola algorithm**, tracks performance, and helps you rebalance with clear buy/sell and swap plans.

## Features

- **MomentumVola Algorithm**: Quantitative strategy based on momentum/volatility ratio
  - Scans common stocks between S&P 500 and NASDAQ-100
  - Market filter: SPY above 220-day moving average
  - Stock filter: Individual stocks above their 220-day MA
  - Scoring: Momentum (3-month return avg) / Volatility (8-month Wilder ATR)
  - Portfolio: 30% Vanguard S&P 500 ETF + 70% split across top 4 ranked stocks
- **Monthly Automated Runs**: Scheduled execution on the 1st of each month
- **Two Rebalancing Views**: Cashflow (sell then buy) or swap strategies
- **Global Currency Switch**: Display values in USD or EUR across the application
  - Runs generated with EUR input use a fixed EUR/USD rate saved at run creation time
- **Position Confirmation**: Track actual positions with live Yahoo Finance prices
- **Fractional Shares Support**: Buy/sell/swap suggestions and confirmations support up to 4 decimal places
- **Performance Tracking**: P&L and returns since first validation

## How It Works

1. **Generate a Run**: Create a manual run or wait for the monthly scheduler
2. **Review Recommendations**: See the 5 positions (1 ETF + 4 stocks) with target allocations
3. **Execute Trades**: Use the cashflow or swap view to guide your broker orders
4. **Confirm Positions**: Enter your actual executed positions and uninvested cash
5. **Track Performance**: Monitor your portfolio performance over time

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, shadcn/ui
- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Database**: SQLite (Docker volume)
- **Scheduling**: APScheduler (monthly cron at 11:00 Paris time)
- **Market Data**: Yahoo Finance via yfinance
- **Data Sources**: Wikipedia (S&P 500 and NASDAQ-100 constituents)

## Quick Start

**Prerequisites**: Docker + Docker Compose only

1. **Start the application**

```bash
npm run dev
# or directly
docker compose up
```

2. **Open the app**

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/health

3. **First use**: Generate your first run from the Dashboard with your starting capital (USD or EUR)

4. **Stop the application**

```bash
npm run stop
```

That's it! No other dependencies required.

## Available Scripts

- `npm run dev` - Start the application (Docker Compose)
- `npm run start` - Build and start the application
- `npm run stop` - Stop all containers
- `npm run reset-data` - Remove containers and **delete all data** (⚠️ destructive)
- `npm run setup` - Install dependencies locally (for development only)

## Advanced Configuration

### Environment Variables

Backend (`docker-compose.yml`):

- `DATABASE_URL` - SQLite connection string (default: `sqlite:////app/database/momentor.db`)
- `ENABLE_AUTO_SCHEDULING` - Enable monthly automated runs (default: `true`)
- `TZ` - Scheduler timezone (default: `Europe/Paris`)

Frontend (`docker-compose.yml`):

- `VITE_API_URL` - Backend API URL (default: `http://localhost:8000`)

### Scheduler Configuration

Monthly runs are triggered on the **1st of each month at 11:00** (configurable timezone). You can also trigger manual runs anytime from the Dashboard.

## Project Structure

```
backend/
  app/
    algo/        # MomentumVola strategy implementation
    routes/      # FastAPI API endpoints
    services/    # Business logic (run generation, rebalancing, market data)
    models.py    # Database models (runs, positions, recommendations)
    scheduler.py # APScheduler monthly cron
    main.py      # FastAPI application entry point
frontend/
  src/
    components/  # React components (shadcn/ui)
    pages/       # Dashboard, Portfolio, Runs, Settings
    lib/         # API client and utility functions
```

## Development

If you want to develop locally without Docker:

1. **Install dependencies**

```bash
npm run setup
```

2. **Start backend** (Python 3.11+ required)

```bash
cd backend
uvicorn app.main:app --reload
```

3. **Start frontend** (Node 18+ required)

```bash
cd frontend
npm run dev
```

## Troubleshooting

| Issue                    | Solution                                       |
| ------------------------ | ---------------------------------------------- |
| Frontend not loading     | Check `docker logs momentor-frontend`          |
| Backend errors           | Check `docker logs momentor-backend`           |
| Database issues          | Run `./scripts/view-db.sh` to inspect data     |
| Reset everything         | Run `npm run reset-data` (⚠️ deletes all data) |
| Yahoo Finance rate-limit | Retry confirmation or use "Force Confirm"      |
| Port already in use      | Stop other services on ports 3000/8000         |

## Algorithm Details

The **MomentumVola** algorithm follows these steps:

1. **Universe Selection**: Retrieve common stocks between S&P 500 and NASDAQ-100 (~80-90 stocks)
2. **Market Filter**: Only proceed if SPY is above its 220-day moving average
3. **Stock Filter**: Keep only stocks above their own 220-day moving average
4. **Scoring**: Calculate MomentumVola score = `Momentum / Volatility`
   - Momentum = Average of last 3 monthly returns
   - Volatility = Average of last 8 monthly Wilder ATR values
5. **Portfolio Construction**:
   - 30% → Vanguard S&P 500 UCITS ETF (IE00B5BMR087)
   - 70% → Split equally across top 4 ranked stocks

The algorithm uses the last closed month's data to avoid look-ahead bias.

## Data Sources

- **Market Data**: Yahoo Finance via `yfinance` library
- **Index Constituents**: Wikipedia (S&P 500 and NASDAQ-100 pages)
- **Historical Prices**: 2.5 years of daily data for momentum/volatility calculation

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**MoMentor v1.0** - Built with ❤️ for systematic momentum investing

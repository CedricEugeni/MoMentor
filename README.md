# MoMentor - Momentum Portfolio Mentor

MoMentor is a momentum investing strategy mentor for US stocks. It generates monthly portfolio recommendations, tracks performance, and helps you rebalance with clear buy/sell and swap plans.

## Features

- Monthly momentum-based recommendations
- Two rebalancing strategies: cashflow (sell then buy) and swaps
- Position confirmation workflow with Yahoo Finance fallback
- Live portfolio view with P&L since first validation
- Docker Compose setup with persistent SQLite database

## Tech Stack

- Frontend: React 18, TypeScript, Vite, TailwindCSS, shadcn/ui
- Backend: Python 3.11, FastAPI, SQLAlchemy
- Database: SQLite (Docker volume)
- Scheduling: APScheduler (monthly cron)
- Market data: Yahoo Finance via yfinance (rate-limited at times)

## Quick Start (Docker Compose)

Prerequisites: Docker, Docker Compose, Node 18+

1. Install dependencies (optional if you only use Docker)

```bash
npm run setup
```

2. Start the stack

```bash
npm run dev
```

3. Open the app

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health

4. Stop the stack

```bash
npm run stop
```

## Scripts

- `npm run dev` - Start Docker Compose (frontend + backend)
- `npm run start` - Build and start Docker Compose
- `npm run stop` - Stop containers
- `npm run reset-data` - Remove containers and delete the database volume
- `npm run setup` - Install frontend and backend dependencies locally

## Environment Variables

Backend (docker-compose.yml):

- `DATABASE_URL` - SQLite connection string
- `ENABLE_AUTO_SCHEDULING` - Enable monthly runs
- `TZ` - Scheduler timezone (default: Europe/Paris)

Frontend (docker-compose.yml):

- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

## Project Structure

```
backend/
  app/
    algo/        # Momentum strategy implementations
    routes/      # FastAPI route handlers
    services/    # Business logic layer
    models.py    # SQLAlchemy ORM models
    scheduler.py # APScheduler configuration
    main.py      # FastAPI app entry point
frontend/
  src/
    components/  # UI components (shadcn/ui)
    pages/       # Route pages
    lib/         # API client and helpers
```

## Troubleshooting

1. Frontend issues: check browser console.
2. Backend logs: `docker logs momentor-backend`.
3. Database inspection: `./scripts/view-db.sh`.
4. Reset local data: `npm run reset-data`.
5. Yahoo rate-limit: confirmation can be retried or forced when market data is unavailable.

## License

MIT License. See LICENSE.

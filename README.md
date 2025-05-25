# LIFO Database Project

A PostgreSQL database with TimescaleDB extension for tracking food inventory and waste management. This project includes database schema and synthetic data generation.

## Project Structure

```text
.
├── app/                    # Python package for data generation
│   ├── database/          # Database connection handling
│   ├── models/            # Data models and generators
│   └── utils/             # Utility functions
├── database/              # Database schema
│   └── 01-init.sql       # Main schema file
└── docker-compose.yml     # Docker setup for PostgreSQL
```

## Quick Start

1. Start PostgreSQL:

```powershell
docker-compose up -d
```

2. Generate sample data:

```powershell
python -m app.main
```

## Database Documentation

See [Database Schema](docs/database_erd.md) for the complete schema documentation.

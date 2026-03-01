"""Lightweight schema migrations for backward-compatible startup upgrades."""
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def run_schema_migrations(engine: Engine) -> None:
    """Apply minimal additive migrations required by newer application versions."""
    with engine.begin() as connection:
        inspector = inspect(connection)
        table_names = inspector.get_table_names()

        if "algorithm_runs" not in table_names:
            return

        columns = {column["name"] for column in inspector.get_columns("algorithm_runs")}

        if "input_currency" not in columns:
            connection.execute(text("ALTER TABLE algorithm_runs ADD COLUMN input_currency VARCHAR(3) NOT NULL DEFAULT 'USD'"))

        if "fx_rate_to_usd" not in columns:
            connection.execute(text("ALTER TABLE algorithm_runs ADD COLUMN fx_rate_to_usd NUMERIC(12,6) NOT NULL DEFAULT 1"))

        if "fx_rate_timestamp_utc" not in columns:
            connection.execute(text("ALTER TABLE algorithm_runs ADD COLUMN fx_rate_timestamp_utc DATETIME"))

        if "allocation_residual_cash_usd" not in columns:
            connection.execute(
                text("ALTER TABLE algorithm_runs ADD COLUMN allocation_residual_cash_usd NUMERIC(15,2) NOT NULL DEFAULT 0")
            )

        connection.execute(text("UPDATE algorithm_runs SET input_currency = COALESCE(input_currency, 'USD')"))
        connection.execute(text("UPDATE algorithm_runs SET fx_rate_to_usd = COALESCE(fx_rate_to_usd, 1)"))
        connection.execute(text("UPDATE algorithm_runs SET allocation_residual_cash_usd = COALESCE(allocation_residual_cash_usd, 0)"))
        connection.execute(text("UPDATE algorithm_runs SET fx_rate_timestamp_utc = COALESCE(fx_rate_timestamp_utc, run_date)"))

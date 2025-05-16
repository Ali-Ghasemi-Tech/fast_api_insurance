import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from API.database import Base  # your Base metadata
from API import model          # import models so Alembic detects them

# Alembic config object
config = context.config

# Set up Python logging
fileConfig(config.config_file_name)

# Use DATABASE_URL env var or fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://root:ANbnYn3tRyS4DgOm2nLsZpmF@insurance:5432/insurance")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Target metadata for autogenerate
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations without DB connection (offline mode)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations with a live DB connection (online mode)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

# Run migrations based on mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

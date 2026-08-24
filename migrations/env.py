import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

from storage import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_database_url() -> str:
    """Resolve the same database path used by the application runtime."""
    db_path = os.getenv("HOTEL_CHATBOT_DB") or os.getenv("HOTEL_CHATBOT_TEST_DB")
    if not db_path:
        xdg_data_home = os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        app_data_dir = Path(xdg_data_home) / "hotel-chatbot-v2"
        app_data_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(app_data_dir / "hotel_chatbot_v2.db")
    return f"sqlite:///{db_path}"


config.set_main_option("sqlalchemy.url", get_database_url())
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

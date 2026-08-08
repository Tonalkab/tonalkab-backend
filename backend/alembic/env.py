import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 1. Configuración de logging de Alembic
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 2. Importamos los modelos y la metadata de SQLAlchemy
from app.db import Base, DATABASE_URL
from app.models import (
    user,
    auth_provider,
    tipo_planta,
    maceta,
    lectura,
    conexion,
    catalogos_planta,
    control_riego,
    configuracion_maceta,
    predicciones_ml,
    alerta,
    skin,
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    if DATABASE_URL:
        configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

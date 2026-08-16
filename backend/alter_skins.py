import os
import sys

# Agregar backend al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tonalkab-backend/backend')))

from app.db import engine
from sqlalchemy import text

def run_migration():
    try:
        with engine.connect() as conn:
            # Comprobar si la base de datos es SQLite (como fallback) o MySQL
            # Pero ejecutar el alter en ambos casos
            query = text("ALTER TABLE skins ADD COLUMN categoria VARCHAR(20) DEFAULT 'comun' NOT NULL;")
            conn.execute(query)
            conn.commit()
            print("✅ Migración exitosa: Columna 'categoria' añadida a 'skins'.")
    except Exception as e:
        print(f"⚠️ Error o columna ya existe: {e}")

if __name__ == "__main__":
    run_migration()

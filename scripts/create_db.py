"""
Script para criar o banco de dados e extensões necessárias
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from src.config.config import config

def create_database():
    """Cria o banco de dados se não existir"""
    # Conectar ao banco postgres padrão para criar o banco
    admin_conn_str = f"postgresql://{config.database.user}:{config.database.password}@{config.database.host}:{config.database.port}/postgres"
    
    try:
        admin_engine = create_engine(admin_conn_str, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            # Verificar se o banco existe
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{config.database.database}'"))
            exists = result.fetchone()
            
            if not exists:
                print(f"Criando banco de dados '{config.database.database}'...")
                conn.execute(text(f"CREATE DATABASE {config.database.database}"))
                print(f"Banco '{config.database.database}' criado com sucesso!")
            else:
                print(f"Banco '{config.database.database}' já existe.")
        
        admin_engine.dispose()
        
        # Conectar ao banco criado e criar extensão vector
        db_conn_str = config.database.connection_string
        db_engine = create_engine(db_conn_str)
        with db_engine.connect() as conn:
            print("Criando extensão pgvector...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("Extensão pgvector criada com sucesso!")
        
        db_engine.dispose()
        return True
        
    except Exception as e:
        print(f"Erro ao criar banco: {e}")
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)


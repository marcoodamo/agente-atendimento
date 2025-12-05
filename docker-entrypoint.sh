#!/bin/bash
set -e

echo "🚀 Iniciando Agente IA Multicanal..."

# Função para aguardar PostgreSQL
wait_for_postgres() {
    echo "⏳ Aguardando PostgreSQL..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if pg_isready -h postgres -p 5432 -U ${POSTGRES_USER:-agente} > /dev/null 2>&1; then
            echo "✅ PostgreSQL está pronto!"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "PostgreSQL não está pronto ainda. Tentativa $attempt/$max_attempts..."
        sleep 2
    done
    
    echo "❌ Timeout aguardando PostgreSQL"
    return 1
}

# Função para aguardar Redis
wait_for_redis() {
    echo "⏳ Aguardando Redis..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if redis-cli -h redis -p 6379 ping > /dev/null 2>&1; then
            echo "✅ Redis está pronto!"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "Redis não está pronto ainda. Tentativa $attempt/$max_attempts..."
        sleep 2
    done
    
    echo "❌ Timeout aguardando Redis"
    return 1
}

# Aguardar serviços
wait_for_postgres || exit 1
wait_for_redis || exit 1

# Criar banco de dados se não existir (apenas para API)
if [ "$1" = "python" ] && [[ "$*" == *"src.main"* ]]; then
    echo "📦 Verificando banco de dados..."
    python scripts/create_db.py || echo "⚠️ Banco de dados já existe ou erro ao criar"
    
    echo "📋 Inicializando tabelas..."
    python scripts/init_db.py || echo "⚠️ Tabelas já existem ou erro ao inicializar"
fi

# Executar comando passado
echo "▶️ Executando: $@"
exec "$@"


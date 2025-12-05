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
        if [ $((attempt % 5)) -eq 0 ]; then
            echo "   Aguardando... ($attempt/$max_attempts)"
        fi
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
        if [ $((attempt % 5)) -eq 0 ]; then
            echo "   Aguardando... ($attempt/$max_attempts)"
        fi
        sleep 2
    done
    
    echo "❌ Timeout aguardando Redis"
    return 1
}

# Aguardar serviços
wait_for_postgres || exit 1
wait_for_redis || exit 1

# Nota: 
# - O banco de dados é criado automaticamente pelo docker-compose (POSTGRES_DB)
# - A extensão pgvector já está na imagem pgvector/pgvector
# - As tabelas são criadas automaticamente pelo RAGService quando a API inicia
# Não é necessário fazer nada aqui - tudo é automático!

# Executar comando passado
echo "▶️ Executando: $@"
exec "$@"


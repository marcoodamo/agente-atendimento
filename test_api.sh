#!/bin/bash
# Script de teste da API

API_URL="${API_URL:-http://localhost:30000}"
# API_KEY será lida do .env ou você pode exportar antes de executar
# export API_KEY=sua_chave_aqui
API_KEY="${API_KEY:-}"

echo "=== Testando API do Agente IA ==="
echo ""

# Carregar API_KEY do .env se não estiver definida
if [ -z "$API_KEY" ] && [ -f .env ]; then
    export $(grep "^API_KEY=" .env | xargs)
fi

if [ -z "$API_KEY" ]; then
    echo "⚠️  API_KEY não definida!"
    echo "   Defina com: export API_KEY=sua_chave"
    echo "   Ou configure no arquivo .env"
    echo ""
fi

# Teste 1: Health Check
echo "1. Testando /health..."
curl -s "$API_URL/health" | python3 -m json.tool
echo ""
echo ""

# Teste 2: Informações do serviço
echo "2. Testando / (raiz)..."
curl -s "$API_URL/" | python3 -m json.tool
echo ""
echo ""

# Teste 3: Processar mensagem (apenas se API_KEY estiver definida)
if [ -n "$API_KEY" ]; then
    echo "3. Testando /api/message..."
    curl -s -X POST "$API_URL/api/message" \
      -H "X-API-Key: $API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "message": "Olá, como posso ser ajudado?",
        "user_id": "test_user_123",
        "channel": "api"
      }' | python3 -m json.tool
    echo ""
    echo ""

    # Teste 4: Buscar na base de conhecimento (se RAG estiver configurado)
    echo "4. Testando /api/rag/search..."
    curl -s -X GET "$API_URL/api/rag/search?query=teste&top_k=3" \
      -H "X-API-Key: $API_KEY" | python3 -m json.tool
else
    echo "3. ⏭️  Pulando testes que requerem API_KEY"
    echo "4. ⏭️  Pulando testes que requerem API_KEY"
echo ""
echo ""

echo "=== Testes concluídos ==="


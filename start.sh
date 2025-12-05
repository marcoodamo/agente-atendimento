#!/bin/bash
# Script principal para iniciar o Agente IA Multicanal
# Inicia todos os serviços via Docker Compose

set -e

cd "$(dirname "$0")"

echo "🚀 Agente IA Multicanal - Iniciando Serviços"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar se Docker está instalado
if ! command_exists docker; then
    echo -e "${RED}❌ Docker não está instalado!${NC}"
    echo "   Instale Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Docker não está rodando!${NC}"
    echo ""
    echo "📋 Para iniciar Docker:"
    echo "   1. Abra o aplicativo 'Docker Desktop'"
    echo "   2. Aguarde até o ícone aparecer na barra de menu"
    echo ""
    echo -e "${BLUE}⏳ Aguardando Docker iniciar... (pressione Ctrl+C para cancelar)${NC}"
    
    # Aguardar Docker iniciar (máximo 2 minutos)
    MAX_WAIT=120
    ELAPSED=0
    while [ $ELAPSED -lt $MAX_WAIT ]; do
        if docker info > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Docker iniciado!${NC}"
            break
        fi
        sleep 2
        ELAPSED=$((ELAPSED + 2))
        if [ $((ELAPSED % 10)) -eq 0 ]; then
            echo "   Aguardando... (${ELAPSED}s/${MAX_WAIT}s)"
        fi
    done
    
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker não iniciou no tempo esperado${NC}"
        echo "   Por favor, inicie Docker Desktop manualmente e tente novamente"
        exit 1
    fi
fi

# Verificar se docker-compose está disponível
if command_exists docker-compose; then
    COMPOSE_CMD="docker-compose"
elif docker compose version > /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ docker-compose não está disponível!${NC}"
    exit 1
fi

# Verificar se .env existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado!${NC}"
    if [ -f .env.example ]; then
        echo "📝 Copiando .env.example para .env..."
        cp .env.example .env
        echo -e "${YELLOW}✅ Arquivo .env criado.${NC}"
        echo ""
        echo -e "${RED}⚠️  IMPORTANTE: Configure as credenciais obrigatórias no arquivo .env!${NC}"
        echo ""
        echo -e "${BLUE}Credenciais obrigatórias:${NC}"
        echo "   1. API_KEY - Gere uma chave segura (ex: openssl rand -hex 32)"
        echo "   2. OPENAI_API_KEY - Sua chave da OpenAI"
        echo ""
        echo "Valores padrão que podem funcionar para teste:"
        echo "   POSTGRES_PASSWORD=agente123 (usado pelo Docker)"
        echo ""
        echo -e "${BLUE}Depois de configurar, execute novamente:${NC} ./start.sh"
        echo ""
        exit 1
    else
        echo -e "${RED}❌ Arquivo .env.example não encontrado!${NC}"
        exit 1
    fi
fi

# Verificar se API_KEY está configurada
if ! grep -q "^API_KEY=.*[^[:space:]]" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  API_KEY não está configurada no .env!${NC}"
    echo ""
    echo -e "${BLUE}Para gerar uma API_KEY segura, execute:${NC}"
    echo "   openssl rand -hex 32"
    echo ""
    echo "Depois, adicione ao .env:"
    echo "   API_KEY=chave_gerada_aqui"
    echo ""
    exit 1
fi

# Verificar se OPENAI_API_KEY está configurada
if ! grep -q "^OPENAI_API_KEY=.*[^[:space:]]" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY não está configurada no .env!${NC}"
    echo ""
    echo -e "${BLUE}Configure sua chave da OpenAI no arquivo .env:${NC}"
    echo "   OPENAI_API_KEY=sk-..."
    echo ""
    exit 1
fi

# Iniciar serviços
echo -e "${BLUE}📦 Construindo e iniciando containers...${NC}"
$COMPOSE_CMD up -d --build

# Aguardar serviços estarem prontos
echo ""
echo -e "${BLUE}⏳ Aguardando serviços iniciarem e inicializarem banco de dados...${NC}"
sleep 10

# Verificar status
echo ""
echo -e "${BLUE}📊 Status dos serviços:${NC}"
$COMPOSE_CMD ps

# Verificar se todos os serviços estão rodando
if $COMPOSE_CMD ps | grep -q "Up"; then
    echo ""
    echo -e "${GREEN}✅ Serviços iniciados com sucesso!${NC}"
    echo ""
    echo -e "${BLUE}🌐 Acesse:${NC}"
    echo -e "   ${GREEN}📡 API:${NC}        http://localhost:30000"
    echo -e "   ${GREEN}📚 Docs API:${NC}    http://localhost:30000/docs"
    echo -e "   ${GREEN}🌐 Interface:${NC}   http://localhost:30001"
    echo ""
    echo -e "${BLUE}📋 Comandos úteis:${NC}"
    echo "   Ver logs:      $COMPOSE_CMD logs -f"
    echo "   Ver logs API:  $COMPOSE_CMD logs -f api"
    echo "   Parar tudo:    $COMPOSE_CMD down"
    echo "   Reiniciar:     $COMPOSE_CMD restart"
    echo "   Status:        $COMPOSE_CMD ps"
    echo ""
    echo -e "${BLUE}🧪 Testar API:${NC}"
    echo "   ./test_api.sh"
    echo ""
    echo -e "${GREEN}✨ Sistema pronto para uso!${NC}"
    echo ""
    echo -e "${BLUE}💡 Dica:${NC} O banco de dados e tabelas foram criados automaticamente."
    echo "   Você pode começar a usar a API e fazer upload de documentos na Interface Web."
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠️  Alguns serviços podem não ter iniciado corretamente${NC}"
    echo "   Verifique os logs: $COMPOSE_CMD logs"
    echo "   Ou logs específicos: $COMPOSE_CMD logs api"
    exit 1
fi

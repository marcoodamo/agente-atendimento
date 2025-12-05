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
        echo -e "${RED}⚠️  IMPORTANTE: Edite o arquivo .env e configure suas credenciais!${NC}"
        echo "   Especialmente: API_KEY, OPENAI_API_KEY"
        echo ""
        echo "   Depois, execute novamente: ./start.sh"
        exit 1
    else
        echo -e "${RED}❌ Arquivo .env.example não encontrado!${NC}"
        exit 1
    fi
fi

# Iniciar serviços
echo -e "${BLUE}📦 Construindo e iniciando containers...${NC}"
$COMPOSE_CMD up -d --build

# Aguardar serviços estarem prontos
echo ""
echo -e "${BLUE}⏳ Aguardando serviços iniciarem...${NC}"
sleep 8

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
else
    echo ""
    echo -e "${YELLOW}⚠️  Alguns serviços podem não ter iniciado corretamente${NC}"
    echo "   Verifique os logs: $COMPOSE_CMD logs"
    exit 1
fi

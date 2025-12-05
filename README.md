# Agente de Atendimento IA Multicanal

Sistema de atendimento ao cliente baseado em Inteligência Artificial com suporte a múltiplos canais (WhatsApp, Voz, Web Chat) e funcionalidades de RAG, agendamento automático e follow-up.

## 🚀 Início Rápido

### Opção 1: Docker Compose (Recomendado para Deploy)

```bash
# 1. Configurar ambiente
cp .env.example .env  # Edite com suas credenciais

# 2. Iniciar tudo com Docker
docker-compose up -d

# 3. Verificar status
docker-compose ps

# 4. Ver logs
docker-compose logs -f
```

A API estará disponível em `http://localhost:8000` e a interface em `http://localhost:8501`.

**📖 Veja [Deploy](docs/deploy.md) e [Segurança](docs/seguranca.md) para guias completos.**

### Opção 2: Script Automatizado

```bash
# 1. Configurar ambiente
cp .env.example .env  # Edite com suas credenciais

# 2. Iniciar tudo (Docker Compose)
./start.sh
```

Este script verifica dependências, inicia Docker se necessário, e sobe todos os serviços.

## 📚 Documentação Completa

Toda a documentação detalhada está disponível em [`/docs`](docs/):

- **[Índice](docs/README.md)** - Índice completo da documentação
- **[Arquitetura](docs/arquitetura.md)** - Como o sistema funciona
- **[Instalação](docs/instalacao.md)** - Guia completo de instalação e comandos rápidos
- **[APIs](docs/apis.md)** - Documentação das APIs e endpoints
- **[Integrações](docs/integracoes.md)** - WhatsApp, Calendly, Voz
- **[Interface Web](docs/interface.md)** - Interface gráfica Streamlit
- **[RAG](docs/rag.md)** - Base de conhecimento vetorial
- **[Follow-up](docs/follow-up.md)** - Sistema de follow-up automático
- **[Voz](docs/voz.md)** - Atendimento por voz (ASR/TTS)
- **[Edição](docs/edicao.md)** - Como editar e customizar
- **[Deploy](docs/deploy.md)** - Guia completo de deploy com Docker
- **[Segurança](docs/seguranca.md)** - Medidas de segurança e produção

## 🎯 Funcionalidades

- ✅ **WhatsApp** - Integração via Evolution API
- ✅ **Voz** - Atendimento telefônico com ASR/TTS
- ✅ **RAG** - Base de conhecimento vetorial (PostgreSQL + PGVector com HNSW)
- ✅ **Agendamento** - Integração com Calendly
- ✅ **Follow-up** - Sistema automático de reengajamento
- ✅ **Interface Web** - Interface gráfica para gerenciar e testar
- ✅ **Contexto** - Histórico e personalização por cliente

## 🛠️ Tecnologias

- **LangChain** - Framework para agentes IA
- **OpenAI GPT-4o** - Modelo de linguagem
- **PostgreSQL + PGVector** - Base de conhecimento vetorial (índice HNSW)
- **FastAPI** - API REST e webhooks
- **Redis** - Cache e memória de conversas
- **Streamlit** - Interface web

## 📖 Exemplo de Uso

```bash
# Enviar mensagem via API
curl -X POST http://localhost:8000/api/message \
  -H "X-API-Key: sua_chave_aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá, preciso de ajuda",
    "user_id": "user123",
    "channel": "api"
  }'
```

## 🔧 Requisitos

- Python 3.10+
- Docker Desktop (para PostgreSQL e Redis)
- OpenAI API Key
- Variáveis de ambiente configuradas (ver `.env.example`)

## 📝 Licença

Este projeto é proprietário.

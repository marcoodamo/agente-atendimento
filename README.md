# Agente de Atendimento IA Multicanal

Sistema de atendimento ao cliente baseado em Inteligência Artificial com suporte a múltiplos canais (WhatsApp, Voz, Web Chat) e funcionalidades de RAG, agendamento automático e follow-up.

## 🚀 Início Rápido (Um Único Comando)

### Ambiente Zerado? Siga estes passos:

```bash
# 1. Clone o repositório
git clone https://github.com/marcoodamo/agente-atendimento.git
cd agente-atendimento

# 2. Configure credenciais (OBRIGATÓRIO antes de iniciar)
cp .env.example .env
# Edite o .env e configure:
#   - API_KEY (gere com: openssl rand -hex 32)
#   - OPENAI_API_KEY (sua chave da OpenAI)

# 3. INICIE TUDO COM UM ÚNICO COMANDO
./start.sh
```

**É isso!** O script `start.sh`:
- ✅ Verifica se Docker está instalado e rodando
- ✅ Cria o arquivo .env se não existir
- ✅ Valida credenciais obrigatórias
- ✅ Constrói e inicia todos os containers
- ✅ Cria banco de dados e tabelas automaticamente
- ✅ Inicializa todos os serviços

Após executar `./start.sh`, tudo estará funcionando:
- 📡 **API**: http://localhost:30000
- 📚 **Docs API**: http://localhost:30000/docs
- 🌐 **Interface Web**: http://localhost:30001

**Nenhuma configuração manual adicional é necessária!** O banco de dados, tabelas e conexões são criados automaticamente.

**📖 Veja [Deploy](docs/deploy.md) e [Segurança](docs/seguranca.md) para guias completos.**

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

### ✅ Funcionando e Ativo

- ✅ **API REST Completa** - FastAPI com documentação Swagger
  - Processamento de mensagens (`/api/message`)
  - Busca RAG (`/api/rag/search`)
  - Upload de documentos (`/api/rag/upload`)
  - Listagem de documentos e metadata
  - Autenticação via API Key
  
- ✅ **Interface Web Streamlit** - Interface gráfica completa
  - Conversa com o agente em tempo real
  - Upload e gerenciamento de documentos RAG
  - Teste de busca RAG com filtros de metadata
  - Visualização de documentos e metadata
  
- ✅ **RAG (Base de Conhecimento Vetorial)** - Totalmente funcional
  - Busca semântica com PostgreSQL + PGVector (índice HNSW)
  - Upload de documentos (PDF, TXT, DOCX)
  - Chunking automático e indexação
  - Filtros de metadata personalizáveis
  - Integração com LangChain Agent
  
- ✅ **Processamento de Mensagens com IA**
  - LangChain Agent com GPT-4o
  - Histórico de conversas (Redis)
  - Contexto por usuário/canal
  - Respostas baseadas em RAG + histórico
  
- ✅ **Integração WhatsApp (Envio)**
  - Envio de mensagens via Evolution API
  - Suporte a texto e mídia
  - Ferramentas LangChain para agente usar automaticamente
  
- ✅ **Integração Calendly (Ferramentas)**
  - Busca de horários disponíveis
  - Criação de agendamentos
  - Ferramentas LangChain integradas ao agente
  
- ✅ **Configuração Automática**
  - Setup completo com um único comando (`./start.sh`)
  - Criação automática de banco de dados e tabelas
  - Docker Compose para todos os serviços

### ⚠️ Parcialmente Implementado / Requer Configuração

- ⚠️ **Webhooks WhatsApp** - Código implementado, requer:
  - URL pública configurada na Evolution API
  - Configuração de webhook secret/validação
  - Servidor exposto publicamente (túnel ngrok ou similar)
  
- ⚠️ **Webhooks Calendly** - Código implementado, requer:
  - URL pública configurada no Calendly
  - Webhook secret configurado
  - Servidor exposto publicamente
  
- ⚠️ **Follow-up Automático** - Código implementado, requer:
  - Scheduler (Celery Beat ou cron) para processar tarefas pendentes
  - Integração com fila de tarefas (Redis/Celery recomendado)
  - Atualmente apenas agenda, não processa automaticamente
  
- ⚠️ **Integração de Voz** - Código implementado, requer:
  - Infraestrutura de telefonia (Twilio, AWS Connect, etc.)
  - Configuração de provedor ASR/TTS (Google, AWS, ElevenLabs)
  - Credenciais dos provedores de voz
  - Endpoint de recepção de chamadas

### ❌ Não Implementado / Planejado

- ❌ **Dashboard Analytics** - Métricas e relatórios de atendimento
- ❌ **Integração Email** - Envio/recebimento de emails
- ❌ **Multi-idioma** - Suporte a múltiplos idiomas além de português
- ❌ **Avaliação de Satisfação** - Coleta de feedback automático

## 🛠️ Tecnologias Principais

### Core
- **LangChain** - Framework para agentes IA e ferramentas
- **OpenAI GPT-4o** - Modelo de linguagem para respostas do agente
- **FastAPI** - API REST moderna com documentação automática (Swagger)
- **Streamlit** - Interface web interativa

### Armazenamento
- **PostgreSQL 15** - Banco de dados principal
- **PGVector** - Extensão para busca vetorial (índice HNSW)
- **Redis** - Cache e armazenamento de histórico de conversas

### Infraestrutura
- **Docker & Docker Compose** - Containerização e orquestração
- **Uvicorn** - Servidor ASGI para FastAPI

### Integrações
- **Evolution API** - Integração WhatsApp
- **Calendly API** - Agendamento de eventos
- **Google Cloud / AWS / ElevenLabs** - Serviços de voz (ASR/TTS) - opcional

## 📖 Exemplo de Uso

### Via API REST

```bash
# Enviar mensagem via API
curl -X POST http://localhost:30000/api/message \
  -H "X-API-Key: sua_chave_aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá, preciso de ajuda",
    "user_id": "user123",
    "channel": "api"
  }'

# Buscar na base de conhecimento (RAG)
curl -X GET "http://localhost:30000/api/rag/search?query=Como funciona a devolução?&top_k=5" \
  -H "X-API-Key: sua_chave_aqui"

# Upload de documento
curl -X POST http://localhost:30000/api/rag/upload \
  -H "X-API-Key: sua_chave_aqui" \
  -F "file=@documento.pdf" \
  -F "metadata={\"departamento\": \"TI\"}"
```

### Via Interface Web

1. Acesse http://localhost:30001
2. Use a aba **"Conversar"** para conversar com o agente
3. Use a aba **"Base de Conhecimento"** para:
   - Fazer upload de documentos
   - Testar busca RAG
   - Gerenciar metadata dos documentos

## 🔧 Requisitos

- Python 3.10+
- Docker Desktop (para PostgreSQL e Redis)
- OpenAI API Key
- Variáveis de ambiente configuradas (ver `.env.example`)

## 📝 Licença

Este projeto é proprietário.

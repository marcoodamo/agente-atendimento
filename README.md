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

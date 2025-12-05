# 🚀 Guia de Deploy com Docker

Este guia explica como fazer deploy completo da aplicação usando Docker Compose.

## 📋 Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- Arquivo `.env` configurado

## ⚙️ Configuração

### 1. Criar arquivo `.env`

Copie o arquivo de exemplo e configure:

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
# API e Autenticação
API_KEY=sua_chave_secreta_aqui
ENABLE_API_AUTH=true

# OpenAI
OPENAI_API_KEY=sua_chave_openai_aqui
LLM_MODEL=gpt-4o

# Database (usado apenas para referência, containers usam valores do docker-compose)
POSTGRES_USER=agente
POSTGRES_PASSWORD=agente123
POSTGRES_DB=agente_db

# Portas (opcional, padrões: 8000, 8501, 5433, 6379)
API_PORT=8000
INTERFACE_PORT=8501
POSTGRES_PORT=5433
REDIS_PORT=6379

# Módulos
ENABLE_KNOWLEDGE=true
ENABLE_SCHEDULING=true
ENABLE_FOLLOWUP=true
ENABLE_VOICE=false

# RAG
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.3

# Integrações (opcional)
EVOLUTION_API_URL=https://api.evolutionapi.com
EVOLUTION_API_KEY=sua_chave_evolution
EVOLUTION_INSTANCE_NAME=sua_instancia

CALENDLY_API_KEY=sua_chave_calendly
```

### 2. (Opcional) Criar docker-compose.override.yml

Para personalizações locais sem modificar o `docker-compose.yml`:

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

## 🚀 Iniciar Aplicação

### Iniciar todos os serviços

```bash
docker-compose up -d
```

Isso inicia:
- **PostgreSQL** com pgvector (porta 5433)
- **Redis** (porta 6379)
- **API FastAPI** (porta 8000)
- **Interface Streamlit** (porta 8501)

### Ver logs

```bash
# Todos os serviços
docker-compose logs -f

# Serviço específico
docker-compose logs -f api
docker-compose logs -f interface
docker-compose logs -f postgres
```

### Verificar status

```bash
docker-compose ps
```

## 🛑 Parar Aplicação

```bash
# Parar serviços (mantém volumes)
docker-compose stop

# Parar e remover containers (mantém volumes)
docker-compose down

# Parar e remover tudo, incluindo volumes (⚠️ apaga dados!)
docker-compose down -v
```

## 🔄 Atualizar Aplicação

```bash
# Reconstruir imagens
docker-compose build

# Reiniciar serviços
docker-compose restart

# Ou reconstruir e reiniciar
docker-compose up -d --build
```

## 📊 Acessar Serviços

- **API**: http://localhost:8000
- **Interface Web**: http://localhost:8501
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6379

## 🔧 Comandos Úteis

### Executar comandos no container

```bash
# No container da API
docker-compose exec api python scripts/create_db.py
docker-compose exec api python scripts/init_db.py

# No container do PostgreSQL
docker-compose exec postgres psql -U agente -d agente_db

# Shell no container
docker-compose exec api bash
```

### Backup do banco de dados

```bash
docker-compose exec postgres pg_dump -U agente agente_db > backup.sql
```

### Restaurar banco de dados

```bash
docker-compose exec -T postgres psql -U agente agente_db < backup.sql
```

### Ver volumes

```bash
docker volume ls | grep agente
```

### Limpar volumes (⚠️ apaga dados!)

```bash
docker-compose down -v
```

## 🐛 Troubleshooting

### API não inicia

```bash
# Ver logs
docker-compose logs api

# Verificar se PostgreSQL está pronto
docker-compose exec api pg_isready -h postgres -U agente

# Verificar variáveis de ambiente
docker-compose exec api env | grep POSTGRES
```

### Interface não conecta à API

```bash
# Verificar se API está rodando
curl http://localhost:8000/health

# Verificar variável API_URL no container
docker-compose exec interface env | grep API_URL
```

### Erro de permissão

```bash
# Ajustar permissões dos volumes
sudo chown -R $USER:$USER data/ logs/
```

### Reconstruir do zero

```bash
# Parar tudo
docker-compose down -v

# Remover imagens
docker-compose rm -f

# Reconstruir
docker-compose build --no-cache

# Iniciar
docker-compose up -d
```

## 📦 Produção

### Variáveis de ambiente

Para produção, use variáveis de ambiente do sistema ou um arquivo `.env` seguro:

```bash
# Não commitar .env no git!
echo ".env" >> .gitignore
```

### Healthchecks

Os serviços têm healthchecks configurados. Verifique:

```bash
docker-compose ps
```

### Restart policies

Os serviços estão configurados com `restart: unless-stopped` para reiniciar automaticamente.

### Volumes persistentes

Os dados são armazenados em volumes Docker:
- `postgres_data`: Dados do PostgreSQL
- `redis_data`: Dados do Redis
- `./data`: Uploads e dados da aplicação
- `./logs`: Logs da aplicação

## 🔐 Segurança

1. **Altere senhas padrão** no `.env`
2. **Use API_KEY forte** (gerar com: `openssl rand -hex 32`)
3. **Não exponha portas** desnecessárias em produção
4. **Use HTTPS** com reverse proxy (nginx/traefik)
5. **Backup regular** dos volumes

Veja o [Guia de Segurança](seguranca.md) para mais detalhes.

## 📝 Exemplo de Deploy Completo

```bash
# 1. Clonar repositório
git clone <repo-url>
cd agente-atendimento

# 2. Configurar ambiente
cp .env.example .env
# Editar .env com suas credenciais

# 3. Iniciar serviços
docker-compose up -d

# 4. Verificar status
docker-compose ps

# 5. Ver logs
docker-compose logs -f

# 6. Acessar interface
# http://localhost:8501
```

## 🚀 Próximos Passos

- Configure reverse proxy (nginx/traefik) para HTTPS
- Configure backup automático do banco
- Configure monitoramento (Prometheus/Grafana)
- Configure logs centralizados (ELK/ Loki)


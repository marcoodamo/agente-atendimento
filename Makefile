.PHONY: build up down restart logs ps shell-api shell-interface test clean

# Build das imagens
build:
	docker-compose build

# Iniciar todos os serviços
up:
	docker-compose up -d

# Parar todos os serviços
down:
	docker-compose down

# Parar e remover volumes (⚠️ apaga dados!)
down-volumes:
	docker-compose down -v

# Reiniciar serviços
restart:
	docker-compose restart

# Ver logs
logs:
	docker-compose logs -f

# Logs de serviço específico
logs-api:
	docker-compose logs -f api

logs-interface:
	docker-compose logs -f interface

logs-postgres:
	docker-compose logs -f postgres

# Status dos serviços
ps:
	docker-compose ps

# Shell no container da API
shell-api:
	docker-compose exec api bash

# Shell no container da interface
shell-interface:
	docker-compose exec interface bash

# Executar script no container da API
run-script:
	docker-compose exec api python $(SCRIPT)

# Reconstruir e reiniciar
rebuild:
	docker-compose up -d --build

# Limpar tudo (containers, volumes, imagens)
clean:
	docker-compose down -v
	docker system prune -f

# Backup do banco
backup-db:
	docker-compose exec postgres pg_dump -U agente agente_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Restaurar banco
restore-db:
	docker-compose exec -T postgres psql -U agente agente_db < $(BACKUP_FILE)

# Testar API
test-api:
	curl http://localhost:8000/health

# Iniciar apenas infraestrutura (PostgreSQL + Redis)
up-infra:
	docker-compose up -d postgres redis

# Iniciar aplicação (API + Interface)
up-app:
	docker-compose up -d api interface

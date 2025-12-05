# 🔒 Guia de Segurança

Este documento descreve as medidas de segurança implementadas e recomendações para produção.

## 🛡️ Medidas de Segurança Implementadas

### 1. Portas Não-Padrão

Todas as portas foram configuradas no range **30000-40000** para dificultar varredura automática:

- **API**: `30000`
- **Interface**: `30001`
- **PostgreSQL**: `30002` (opcional, pode ser desabilitado)
- **Redis**: `30003` (opcional, pode ser desabilitado)

### 2. Headers de Segurança

A API adiciona automaticamente os seguintes headers de segurança:

- **X-Content-Type-Options**: `nosniff` - Previne MIME type sniffing
- **X-Frame-Options**: `DENY` - Previne clickjacking
- **X-XSS-Protection**: `1; mode=block` - Proteção XSS
- **Strict-Transport-Security**: Força HTTPS
- **Content-Security-Policy**: Restringe recursos carregados
- **Referrer-Policy**: Controla informações de referrer
- **Permissions-Policy**: Restringe APIs do navegador

### 3. CORS Restritivo

CORS configurado para permitir apenas origens específicas:

```env
ALLOWED_ORIGINS=http://seu-dominio.com,https://seu-dominio.com
```

### 4. Trusted Hosts

Proteção contra Host Header attacks:

```env
TRUSTED_HOSTS=seu-dominio.com,api.seu-dominio.com
```

### 5. API Key Authentication

Todas as rotas da API requerem autenticação via `X-API-Key` header.

### 6. Documentação Desabilitada

Em produção, os endpoints de documentação estão desabilitados:
- `/docs` - Desabilitado
- `/redoc` - Desabilitado
- `/openapi.json` - Desabilitado

## 🔐 Configuração para Produção

### 1. Variáveis de Ambiente

Configure no `.env`:

```env
# Segurança
ALLOWED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
TRUSTED_HOSTS=seu-dominio.com,www.seu-dominio.com,api.seu-dominio.com

# API Key forte (gerar com: openssl rand -hex 32)
API_KEY=gerar_chave_forte_aqui

# Desabilitar portas desnecessárias
POSTGRES_PORT=  # Deixar vazio para não expor
REDIS_PORT=     # Deixar vazio para não expor
```

### 2. Firewall

Configure firewall para permitir apenas portas necessárias:

```bash
# Permitir apenas portas da aplicação
ufw allow 30000/tcp  # API
ufw allow 30001/tcp  # Interface
# Não exponha PostgreSQL e Redis externamente
```

### 3. Reverse Proxy com HTTPS

Use nginx ou traefik como reverse proxy com HTTPS:

**Exemplo nginx.conf:**

```nginx
server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # API
    location /api/ {
        proxy_pass http://localhost:30000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Não expor headers internos
        proxy_hide_header X-Powered-By;
        proxy_hide_header Server;
    }

    # Interface
    location / {
        proxy_pass http://localhost:30001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support para Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Redirecionar HTTP para HTTPS
server {
    listen 80;
    server_name seu-dominio.com;
    return 301 https://$server_name$request_uri;
}
```

### 4. Rate Limiting

Adicione rate limiting no nginx ou use middleware:

```nginx
# Rate limiting no nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    # ...
}
```

### 5. Ocultar Informações

A API já remove headers que expõem informações:
- `Server` - Removido
- `X-Powered-By` - Removido

### 6. Logs e Monitoramento

Configure logs adequados:

```env
LOG_LEVEL=WARNING  # Em produção, use WARNING ou ERROR
```

Monitore:
- Tentativas de acesso não autorizado
- Taxa de requisições
- Erros 4xx e 5xx

## 🚨 Checklist de Segurança

Antes de colocar em produção:

- [ ] API_KEY forte configurada (mínimo 32 caracteres aleatórios)
- [ ] ALLOWED_ORIGINS configurado com domínio real
- [ ] TRUSTED_HOSTS configurado
- [ ] HTTPS configurado via reverse proxy
- [ ] PostgreSQL e Redis não expostos externamente
- [ ] Firewall configurado
- [ ] Rate limiting ativo
- [ ] Logs configurados e monitorados
- [ ] Backup automático do banco de dados
- [ ] Certificados SSL válidos
- [ ] Documentação da API desabilitada
- [ ] Variáveis sensíveis em variáveis de ambiente (não no código)

## 🔍 Testes de Segurança

### Verificar Headers de Segurança

```bash
curl -I https://seu-dominio.com/api/health
```

Deve retornar todos os headers de segurança.

### Testar CORS

```bash
curl -H "Origin: https://atacante.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS https://seu-dominio.com/api/message
```

Deve retornar erro se origem não estiver em ALLOWED_ORIGINS.

### Testar Autenticação

```bash
# Sem API Key - deve falhar
curl https://seu-dominio.com/api/message

# Com API Key - deve funcionar
curl -H "X-API-Key: sua_chave" https://seu-dominio.com/api/message
```

## 📝 Notas Importantes

1. **Localhost vs Domínio**: Em produção, sempre use HTTPS e domínio real. Localhost é apenas para desenvolvimento.

2. **PostgreSQL/Redis**: Não exponha essas portas externamente. Use apenas dentro da rede Docker.

3. **API Key**: Gere uma chave forte e mantenha segura. Não commite no git.

4. **HTTPS**: Sempre use HTTPS em produção. Configure certificado SSL válido.

5. **Backup**: Configure backup automático do banco de dados.

6. **Monitoramento**: Configure alertas para tentativas de acesso não autorizado.

## 🆘 Em Caso de Ataque

1. **Bloquear IP**: Use firewall para bloquear IPs suspeitos
2. **Rotacionar API Key**: Gere nova chave e atualize
3. **Verificar Logs**: Analise logs para identificar padrões
4. **Atualizar Dependências**: Mantenha todas as dependências atualizadas
5. **Notificar**: Se dados foram comprometidos, notifique usuários


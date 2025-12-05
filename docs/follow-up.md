# Sistema de Follow-up

O módulo de follow-up permite agendar e enviar mensagens automáticas de acompanhamento aos clientes.

## Visão Geral

O sistema de follow-up suporta diferentes tipos de mensagens automáticas:
- **Pós-serviço**: Após um atendimento
- **Pós-compra**: Após uma compra
- **Lembretes**: Lembretes agendados
- **Reengajamento**: Reengajamento de clientes inativos

## Configuração

### Habilitar Módulo

No arquivo `.env`:
```env
ENABLE_FOLLOWUP=true
```

Ou via linha de comando:
```bash
python -m src.main --mode api --followup
```

## Tipos de Follow-up

### 1. Pós-Serviço

Enviado automaticamente após um atendimento.

```python
from src.modules.followup.followup_service import FollowUpService, FollowUpType

service = FollowUpService()

# Agendar follow-up padrão (24 horas após atendimento)
await service.schedule_post_service_followup(
    user_id="user123",
    channel="whatsapp",
    delay_hours=24
)
```

### 2. Pós-Compra

Enviado após uma compra ser realizada.

```python
await service.schedule_followup(
    user_id="user123",
    channel="whatsapp",
    followup_type=FollowUpType.POST_PURCHASE,
    delay_hours=48,
    message_template=(
        "Olá! Esperamos que esteja satisfeito com sua compra. "
        "Se precisar de algo, estamos à disposição!"
    )
)
```

### 3. Lembrete

Lembretes agendados para datas específicas.

```python
from datetime import datetime

reminder_time = datetime(2024, 1, 15, 14, 0)  # 15/01/2024 às 14:00

await service.schedule_reminder(
    user_id="user123",
    channel="whatsapp",
    reminder_time=reminder_time,
    message="Lembrete: Sua consulta é hoje às 14h!"
)
```

### 4. Reengajamento

Para reengajar clientes inativos.

```python
await service.schedule_followup(
    user_id="user123",
    channel="whatsapp",
    followup_type=FollowUpType.REENGAGEMENT,
    delay_hours=168,  # 7 dias
    message_template=(
        "Olá! Faz um tempo que não conversamos. "
        "Temos novidades que podem interessar você!"
    )
)
```

## Processamento Automático

O sistema processa follow-ups pendentes automaticamente quando integrado com o orquestrador. Para processar manualmente:

```python
await service.process_pending_followups()
```

**Nota:** Em produção, recomenda-se usar Celery Beat ou similar para processar follow-ups periodicamente.

## Canais Suportados

### WhatsApp

```python
await service.schedule_followup(
    user_id="5511999999999",
    channel="whatsapp",
    followup_type=FollowUpType.POST_SERVICE,
    delay_hours=24,
    message_template="Mensagem de follow-up",
    metadata={"phone_number": "5511999999999"}
)
```

### Email (Em desenvolvimento)

```python
await service.schedule_followup(
    user_id="usuario@exemplo.com",
    channel="email",
    followup_type=FollowUpType.POST_SERVICE,
    delay_hours=24,
    message_template="Mensagem de follow-up"
)
```

## Cancelar Follow-ups

Para cancelar follow-ups pendentes:

```python
# Cancelar todos os follow-ups de um usuário
await service.cancel_followup(user_id="user123")

# Cancelar apenas follow-ups de um tipo específico
await service.cancel_followup(
    user_id="user123",
    followup_type=FollowUpType.POST_SERVICE
)
```

## Consultar Follow-ups Pendentes

```python
# Todos os follow-ups pendentes
todos = service.get_pending_followups()

# Follow-ups de um usuário específico
do_usuario = service.get_pending_followups(user_id="user123")
```

## Integração com o Orquestrador

O follow-up é agendado automaticamente após processar uma mensagem quando o módulo está ativo:

```python
# No webhook_server.py, após processar mensagem:
if orchestrator.active_modules.get("followup"):
    followup_service = get_followup_service()
    await followup_service.schedule_post_service_followup(
        user_id=phone_number,
        channel="whatsapp"
    )
```

## Personalização de Mensagens

Você pode personalizar as mensagens usando templates:

```python
message_template = (
    "Olá {nome}!\n\n"
    "Esperamos que tenha conseguido resolver sua questão sobre {assunto}. "
    "Há algo mais em que possamos ajudar?"
)

await service.schedule_followup(
    user_id="user123",
    channel="whatsapp",
    followup_type=FollowUpType.POST_SERVICE,
    delay_hours=24,
    message_template=message_template,
    metadata={
        "nome": "João",
        "assunto": "produto X"
    }
)
```

## Persistência

Atualmente, os follow-ups são armazenados em memória. Para produção, recomenda-se:

1. **Banco de Dados**: Armazenar em PostgreSQL
2. **Fila de Tarefas**: Usar Celery com Redis/RabbitMQ
3. **Agendamento**: Usar Celery Beat ou cron jobs

**Exemplo com Celery:**

```python
# tasks.py
from celery import Celery

app = Celery('followups')

@app.task
def process_followups():
    from src.modules.followup.followup_service import FollowUpService
    service = FollowUpService()
    await service.process_pending_followups()

# celerybeat_schedule
from celery.schedules import crontab

app.conf.beat_schedule = {
    'process-followups-every-minute': {
        'task': 'tasks.process_followups',
        'schedule': crontab(minute='*'),  # A cada minuto
    },
}
```

## Exemplo Completo

```python
from src.modules.followup.followup_service import FollowUpService, FollowUpType
from datetime import datetime, timedelta

service = FollowUpService()

# 1. Agendar follow-up pós-atendimento
await service.schedule_post_service_followup(
    user_id="5511999999999",
    channel="whatsapp",
    delay_hours=24
)

# 2. Agendar lembrete de evento
evento_data = datetime.now() + timedelta(days=1)
await service.schedule_reminder(
    user_id="5511999999999",
    channel="whatsapp",
    reminder_time=evento_data,
    message="Lembrete: Sua consulta é amanhã às 14h!"
)

# 3. Processar follow-ups pendentes (chamar periodicamente)
await service.process_pending_followups()

# 4. Consultar follow-ups
pendentes = service.get_pending_followups(user_id="5511999999999")
print(f"Follow-ups pendentes: {len(pendentes)}")

# 5. Cancelar se necessário
await service.cancel_followup(user_id="5511999999999")
```

## Boas Práticas

1. **Não spammar**: Respeite intervalos razoáveis entre follow-ups
2. **Personalização**: Use dados do usuário para personalizar mensagens
3. **Cancelamento**: Permita que usuários cancelem follow-ups
4. **Monitoramento**: Monitore taxas de abertura e resposta
5. **Horários**: Considere horários comerciais ao agendar


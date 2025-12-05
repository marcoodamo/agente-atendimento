"""
Exemplos de uso do Agente IA Multicanal
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.orchestrator import AgentOrchestrator


async def example_basic_conversation():
    """Exemplo básico de conversa"""
    print("=== Exemplo: Conversa Básica ===\n")
    
    orchestrator = AgentOrchestrator()
    user_id = "example_user"
    
    messages = [
        "Olá, preciso de ajuda",
        "Quais são os horários de atendimento?",
        "Obrigado!"
    ]
    
    for msg in messages:
        print(f"Usuário: {msg}")
        result = await orchestrator.process_message(
            user_message=msg,
            user_id=user_id,
            channel="example"
        )
        print(f"Agente: {result['response']}\n")


async def example_with_rag():
    """Exemplo usando RAG (base de conhecimento)"""
    print("=== Exemplo: Conversa com RAG ===\n")
    
    # Primeiro, adicionar um documento à base
    from src.modules.rag.rag_service import RAGService
    
    rag_service = RAGService()
    
    # Criar documento de exemplo
    example_doc = Path(__file__).parent / "example_knowledge.txt"
    example_doc.write_text("""
    Horários de Atendimento:
    - Segunda a Sexta: 9h às 18h
    - Sábado: 9h às 13h
    - Domingo: Fechado
    
    Contato:
    - Email: atendimento@empresa.com
    - Telefone: (11) 9999-9999
    """)
    
    # Adicionar à base
    doc_id = await rag_service.add_document(str(example_doc))
    print(f"Documento adicionado: {doc_id}\n")
    
    # Buscar informações
    query = "Quais são os horários de atendimento?"
    results = await rag_service.search(query, top_k=3)
    
    print(f"Busca: {query}")
    print(f"Resultados encontrados: {len(results)}\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['content'][:100]}...")
        print(f"   Similaridade: {result['similarity']:.2f}\n")


async def example_whatsapp_webhook():
    """Exemplo de processamento de webhook WhatsApp"""
    print("=== Exemplo: Webhook WhatsApp ===\n")
    
    from src.modules.whatsapp.whatsapp_service import WhatsAppService
    
    whatsapp_service = WhatsAppService()
    
    # Simular webhook da Evolution API
    webhook_data = {
        "event": "messages.upsert",
        "data": {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "id": "msg123",
                "fromMe": False
            },
            "message": {
                "conversation": "Olá, preciso de ajuda"
            },
            "messageTimestamp": 1234567890
        }
    }
    
    # Processar webhook
    message_data = whatsapp_service.parse_webhook_message(webhook_data)
    
    if message_data:
        print(f"Mensagem recebida:")
        print(f"  De: {message_data['phone_number']}")
        print(f"  Conteúdo: {message_data['content']}")
        print(f"  Tipo: {message_data['type']}")


async def example_calendly_integration():
    """Exemplo de integração com Calendly"""
    print("=== Exemplo: Integração Calendly ===\n")
    
    from src.modules.calendly.calendly_service import CalendlyService
    from datetime import datetime, timedelta
    
    calendly_service = CalendlyService()
    
    # Listar tipos de eventos disponíveis
    event_types = await calendly_service.get_event_types()
    print(f"Tipos de eventos disponíveis: {len(event_types)}\n")
    
    if event_types:
        event_type_uri = event_types[0].get("uri")
        print(f"Usando tipo: {event_type_uri}\n")
        
        # Buscar horários disponíveis
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=7)
        
        available_times = await calendly_service.get_available_times(
            event_type_uri=event_type_uri,
            start_time=start_time,
            end_time=end_time
        )
        
        print(f"Horários disponíveis: {len(available_times)}\n")


async def main():
    """Executa todos os exemplos"""
    print("Exemplos de Uso do Agente IA Multicanal\n")
    print("=" * 50 + "\n")
    
    try:
        await example_basic_conversation()
        print("\n" + "=" * 50 + "\n")
        
        await example_with_rag()
        print("\n" + "=" * 50 + "\n")
        
        await example_whatsapp_webhook()
        print("\n" + "=" * 50 + "\n")
        
        # Descomente se tiver Calendly configurado
        # await example_calendly_integration()
        
    except Exception as e:
        print(f"Erro ao executar exemplos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())


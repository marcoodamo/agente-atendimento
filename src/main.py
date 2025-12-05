"""
Ponto de entrada principal do Agente IA Multicanal
"""
import asyncio
import logging
import argparse
from pathlib import Path

from src.config.config import config
from src.core.orchestrator import AgentOrchestrator
from src.api.webhook_server import create_app

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.agent.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse argumentos da linha de comando"""
    parser = argparse.ArgumentParser(description="Agente IA Multicanal")
    
    # Flags de módulos
    parser.add_argument(
        "--agendamento",
        action="store_true",
        help="Ativa módulo de agendamento Calendly"
    )
    parser.add_argument(
        "--followup",
        action="store_true",
        help="Ativa módulo de follow-up automático"
    )
    parser.add_argument(
        "--voz",
        action="store_true",
        help="Ativa módulo de atendimento por voz"
    )
    parser.add_argument(
        "--knowledge",
        action="store_true",
        help="Ativa módulo RAG (base de conhecimento)"
    )
    parser.add_argument(
        "--no-transbordo",
        action="store_true",
        help="Desativa transbordo para humano"
    )
    
    # Modo de execução
    parser.add_argument(
        "--mode",
        choices=["api", "cli", "test"],
        default="api",
        help="Modo de execução (api, cli, test)"
    )
    
    # Porta da API
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta para o servidor API"
    )
    
    return parser.parse_args()


async def run_cli_mode():
    """Modo CLI - interação direta via terminal"""
    logger.info("Iniciando modo CLI")
    orchestrator = AgentOrchestrator()
    
    print("Agente IA Multicanal - Modo CLI")
    print("Digite 'sair' para encerrar\n")
    
    user_id = "cli_user"
    
    while True:
        try:
            user_input = input("Você: ")
            
            if user_input.lower() in ["sair", "exit", "quit"]:
                print("Encerrando...")
                break
            
            if not user_input.strip():
                continue
            
            # Processar mensagem
            result = await orchestrator.process_message(
                user_message=user_input,
                user_id=user_id,
                channel="cli"
            )
            
            print(f"\nAgente: {result['response']}\n")
            
            if result.get("sources"):
                print(f"Fontes: {', '.join(result['sources'])}\n")
                
        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as e:
            logger.error(f"Erro: {e}")
            print(f"Erro: {e}\n")


def run_api_mode(port: int):
    """Modo API - servidor webhook/API"""
    import uvicorn
    
    app = create_app()
    
    logger.info(f"Iniciando servidor API na porta {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.agent.log_level.lower()
    )


async def run_test_mode():
    """Modo de teste - executa testes básicos"""
    logger.info("Executando testes básicos")
    
    orchestrator = AgentOrchestrator()
    
    # Teste básico
    test_message = "Olá, como posso ajudar?"
    result = await orchestrator.process_message(
        user_message=test_message,
        user_id="test_user",
        channel="test"
    )
    
    print(f"Teste: {test_message}")
    print(f"Resposta: {result['response']}")
    print(f"Intenção: {result.get('intent', {})}")


def main():
    """Função principal"""
    args = parse_args()
    
    # Atualizar flags de módulos se fornecidas via CLI
    if args.agendamento:
        config.agent.enable_agendamento = True
    if args.followup:
        config.agent.enable_followup = True
    if args.voz:
        config.agent.enable_voz = True
    if args.knowledge:
        config.agent.enable_knowledge = True
    if args.no_transbordo:
        config.agent.enable_transbordo_humano = False
    
    logger.info("Iniciando Agente IA Multicanal")
    logger.info(f"Módulos ativos: agendamento={config.agent.enable_agendamento}, "
                f"followup={config.agent.enable_followup}, "
                f"voz={config.agent.enable_voz}, "
                f"knowledge={config.agent.enable_knowledge}")
    
    if args.mode == "cli":
        asyncio.run(run_cli_mode())
    elif args.mode == "api":
        run_api_mode(args.port)
    elif args.mode == "test":
        asyncio.run(run_test_mode())


if __name__ == "__main__":
    main()


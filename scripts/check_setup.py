#!/usr/bin/env python3
"""
Script para verificar se o ambiente está configurado corretamente
"""
import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_env_file():
    """Verifica se .env existe"""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("❌ Arquivo .env não encontrado")
        print("   Execute: cp .env.example .env")
        return False
    print("✅ Arquivo .env encontrado")
    return True

def check_env_vars():
    """Verifica variáveis de ambiente essenciais"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        "OPENAI_API_KEY": "Chave OpenAI (obrigatória)",
        "API_KEY": "API Key para autenticação",
    }
    
    optional_vars = {
        "REDIS_HOST": "Host do Redis (padrão: localhost)",
        "POSTGRES_PASSWORD": "Senha PostgreSQL (padrão: agente123)",
    }
    
    missing_required = []
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"  - {var}: {desc}")
    
    if missing_required:
        print("❌ Variáveis obrigatórias não configuradas:")
        for var in missing_required:
            print(var)
        return False
    
    print("✅ Variáveis obrigatórias configuradas")
    
    missing_optional = []
    for var, desc in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"  - {var}: {desc} (usando padrão)")
    
    if missing_optional:
        print("⚠️  Variáveis opcionais não configuradas (usando padrões):")
        for var in missing_optional:
            print(var)
    
    return True

def check_dependencies():
    """Verifica se dependências estão instaladas"""
    try:
        import fastapi
        import langchain
        import openai
        import redis
        print("✅ Dependências principais instaladas")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("   Execute: pip install -r requirements.txt")
        return False

def check_docker():
    """Verifica se Docker está rodando"""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Verificar se containers estão rodando
            if "agente-postgres" in result.stdout or "agente-redis" in result.stdout:
                print("✅ Containers Docker rodando")
                return True
            else:
                print("⚠️  Docker está rodando mas containers não encontrados")
                print("   Execute: docker-compose up -d")
                return False
        else:
            print("⚠️  Docker não está rodando ou não está instalado")
            return False
    except FileNotFoundError:
        print("⚠️  Docker não encontrado (opcional se não usar containers)")
        return False
    except Exception as e:
        print(f"⚠️  Erro ao verificar Docker: {e}")
        return False

def check_redis_connection():
    """Verifica conexão com Redis"""
    try:
        import asyncio
        from src.utils.redis_client import redis_client
        
        async def test():
            try:
                await redis_client.connect()
                await redis_client.client.ping()
                print("✅ Redis conectado com sucesso")
                await redis_client.disconnect()
                return True
            except Exception as e:
                print(f"⚠️  Redis não disponível: {e}")
                print("   Sistema usará fallback em memória")
                return False
        
        return asyncio.run(test())
    except Exception as e:
        print(f"⚠️  Erro ao testar Redis: {e}")
        return False

def check_config():
    """Verifica se configuração está correta"""
    try:
        from src.config.config import config
        print("✅ Configuração carregada")
        print(f"   LLM Provider: {config.llm.provider}")
        print(f"   LLM Model: {config.llm.model}")
        print(f"   API Auth: {config.api.enable_auth}")
        return True
    except Exception as e:
        print(f"❌ Erro ao carregar configuração: {e}")
        return False

def main():
    """Executa todas as verificações"""
    print("=" * 60)
    print("🔍 Verificação do Ambiente - Agente IA Multicanal")
    print("=" * 60)
    print()
    
    checks = [
        ("Arquivo .env", check_env_file),
        ("Variáveis de Ambiente", check_env_vars),
        ("Dependências Python", check_dependencies),
        ("Docker", check_docker),
        ("Configuração", check_config),
        ("Redis", check_redis_connection),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Verificando: {name}")
        print("-" * 40)
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 Resumo")
    print("=" * 60)
    
    all_ok = True
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
        if not result:
            all_ok = False
    
    print()
    if all_ok:
        print("✅ Ambiente configurado corretamente!")
        print("\nPara iniciar o servidor:")
        print("  python -m src.main --mode api")
    else:
        print("⚠️  Alguns problemas foram encontrados.")
        print("   Consulte TROUBLESHOOTING.md para mais informações.")
        sys.exit(1)

if __name__ == "__main__":
    main()


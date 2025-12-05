"""
Script de exemplo para testar a API
"""
import requests
import json
import sys
from typing import Optional

# Configuração
API_URL = "http://localhost:8000"
API_KEY = None  # Configure sua API Key aqui ou via variável de ambiente


def test_health_check():
    """Testa o health check (não requer autenticação)"""
    print("🔍 Testando Health Check...")
    try:
        response = requests.get(f"{API_URL}/health")
        response.raise_for_status()
        print(f"✅ Health Check OK: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Erro no Health Check: {e}")
        return False


def test_process_message(api_key: str, message: str, user_id: str = "test_user"):
    """Testa processamento de mensagem"""
    print(f"\n💬 Enviando mensagem: '{message}'")
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": message,
        "user_id": user_id,
        "channel": "api",
        "metadata": {
            "name": "Usuário Teste",
            "source": "test_script"
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/message",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Resposta recebida:")
            print(f"   Resposta: {result.get('response', 'N/A')}")
            if result.get('sources'):
                print(f"   Fontes: {', '.join(result['sources'])}")
            return result
        elif response.status_code == 401:
            print("❌ Erro 401: API Key não fornecida ou inválida")
            print(f"   Detalhes: {response.json()}")
            return None
        elif response.status_code == 403:
            print("❌ Erro 403: API Key inválida")
            print(f"   Detalhes: {response.json()}")
            return None
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        return None


def test_rag_search(api_key: str, query: str, top_k: int = 5):
    """Testa busca na base de conhecimento"""
    print(f"\n🔍 Buscando: '{query}'")
    
    headers = {
        "X-API-Key": api_key
    }
    
    params = {
        "query": query,
        "top_k": top_k
    }
    
    try:
        response = requests.get(
            f"{API_URL}/api/rag/search",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Resultados encontrados: {len(result.get('results', []))}")
            for i, doc in enumerate(result.get('results', []), 1):
                print(f"   [{i}] {doc.get('content', '')[:100]}...")
                print(f"       Similaridade: {doc.get('similarity', 0):.2f}")
            return result
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao buscar: {e}")
        return None


def main():
    """Função principal"""
    print("=" * 60)
    print("🧪 Teste da API - Agente IA Multicanal")
    print("=" * 60)
    
    # Verificar API Key
    api_key = API_KEY or input("\n🔑 Digite sua API Key (ou pressione Enter para pular autenticação): ").strip()
    
    if not api_key:
        print("⚠️  API Key não fornecida. Testando apenas endpoints públicos...")
        api_key = "dummy"  # Para não quebrar, mas vai falhar na autenticação
    
    # Teste 1: Health Check
    if not test_health_check():
        print("\n❌ Health Check falhou. Verifique se o servidor está rodando.")
        sys.exit(1)
    
    # Teste 2: Processar mensagem (requer autenticação)
    if api_key and api_key != "dummy":
        print("\n" + "=" * 60)
        print("TESTE: Processamento de Mensagem")
        print("=" * 60)
        
        # Primeira mensagem
        test_process_message(
            api_key=api_key,
            message="Olá, preciso de ajuda",
            user_id="test_user_1"
        )
        
        # Segunda mensagem (testa contexto)
        test_process_message(
            api_key=api_key,
            message="Quais são os horários de atendimento?",
            user_id="test_user_1"
        )
        
        # Teste 3: Busca RAG (se módulo ativo)
        print("\n" + "=" * 60)
        print("TESTE: Busca na Base de Conhecimento")
        print("=" * 60)
        
        test_rag_search(
            api_key=api_key,
            query="horários de atendimento",
            top_k=3
        )
    else:
        print("\n⚠️  Pulei testes que requerem autenticação.")
        print("   Configure API_KEY no script ou forneça via input.")
    
    print("\n" + "=" * 60)
    print("✅ Testes concluídos!")
    print("=" * 60)


if __name__ == "__main__":
    main()


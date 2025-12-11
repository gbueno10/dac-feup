#!/bin/bash
# Script para configurar e executar o Gridfinity Generator

set -e

echo "🗃️ Gridfinity Generator - Setup"
echo "================================"

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.10 ou superior."
    exit 1
fi

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate

# Instala dependências
echo "📥 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Executa a aplicação
echo ""
echo "🚀 Iniciando Gridfinity Generator..."
echo "   Acesse: http://localhost:8501"
echo ""
streamlit run app.py

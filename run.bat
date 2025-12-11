@echo off
REM Script para configurar e executar o Gridfinity Generator no Windows

echo 🗃️ Gridfinity Generator - Setup
echo ================================

REM Verifica se Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Python não encontrado. Por favor, instale Python 3.10 ou superior.
    exit /b 1
)

REM Cria ambiente virtual se não existir
if not exist "venv" (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
)

REM Ativa ambiente virtual
echo 🔄 Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instala dependências
echo 📥 Instalando dependências...
pip install --upgrade pip
pip install -r requirements.txt

REM Executa a aplicação
echo.
echo 🚀 Iniciando Gridfinity Generator...
echo    Acesse: http://localhost:8501
echo.
streamlit run app.py

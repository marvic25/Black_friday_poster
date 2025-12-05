@echo off
title Gerador Cartazes Black Friday

:: 1. Muda para a pasta onde este arquivo está salvo
cd /d "%~dp0"

echo "================================================================="
echo " Ativando ambiente virtual e instalando/atualizando pacotes... "
echo "================================================================="
:: 2. Ativa o ambiente virtual e garante que as dependências estejam instaladas
call .venv\Scripts\activate
pip install -r requirements.txt

echo.
echo "==================================="
echo " Iniciando o servidor local..."
echo "==================================="

:: 3. Abre o navegador no endereço da aplicação
start "" "http://127.0.0.1:5050"

:: 4. Inicia o servidor Flask
python app.py

:: Se o servidor parar, pausa para que a janela não feche e seja possível ler o erro
pause
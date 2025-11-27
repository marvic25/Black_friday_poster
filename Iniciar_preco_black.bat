@echo off
title Gerador Cartazes Black Friday

:: 1. Muda para a pasta onde este arquivo está salvo
cd /d "%~dp0"

:: 2. Abre o navegador automaticamente no endereço certo
start "" "http://127.0.0.1:5050"

:: 3. Ativa o ambiente virtual e inicia o servidor
call venv\Scripts\activate
python app.py

:: Se o servidor parar, pausa para leres o erro
pause
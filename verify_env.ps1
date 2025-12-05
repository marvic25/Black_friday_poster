<#
verify_env.ps1 - Verifica .venv e dependências (Windows PowerShell)
Execução: .\verify_env.ps1
#>

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'

Write-Host "Project root: $projectRoot"

if (-Not (Test-Path $venvPython)) {
    Write-Host ".venv não encontrado ou o python dentro de .venv está ausente." -ForegroundColor Yellow
    Write-Host "Para criar e instalar dependências rode:" 
    Write-Host "  python -m venv .venv"
    Write-Host "  .\\.venv\\Scripts\\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    exit 1
}

Write-Host "Usando python do venv: $venvPython"

# Versão do Python
& $venvPython --version

# Checa importação de img2pdf e imprime versão ou erro
$safeCmd = @"
try:
    import img2pdf, sys
    print('img2pdf:', getattr(img2pdf,'__version__', 'unknown'))
except Exception as e:
    print('IMG2PDF_IMPORT_ERROR:', e)
"@

$result = & $venvPython -c $safeCmd 2>&1
Write-Host $result

# Lista pacotes instalados (mostra até 200 linhas)
Write-Host "`nInstalled packages (pip freeze):" -ForegroundColor Cyan
& $venvPython -m pip freeze | Select-Object -First 200

Write-Host "`nVerificação concluída." -ForegroundColor Green

Verificação do ambiente (Windows / PowerShell)
=============================================

Este arquivo descreve como verificar o ambiente virtual do projeto e confirmar que `img2pdf` e outras dependências estão instaladas corretamente.

Passos rápidos (PowerShell):

1. Ativar o venv e checar `img2pdf`:

```powershell
& ".\.venv\Scripts\Activate.ps1"
& ".\.venv\Scripts\python.exe" -c "import img2pdf, sys; print('img2pdf version:', getattr(img2pdf,'__version__', 'unknown'))"
```

2. Se não existir `.venv`, criar e instalar dependências:

```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

3. Listar pacotes instalados no `venv`:

```powershell
& ".\.venv\Scripts\python.exe" -m pip freeze
```

4. Executar aplicativo (com `venv` ativo):

```powershell
& ".\.venv\Scripts\python.exe" app.py
```

Script auxiliar `verify_env.ps1`:

- O script `verify_env.ps1` localizado na raiz do projeto tenta localizar o `python.exe` dentro de `.venv`, imprime a versão do Python, testa a importação de `img2pdf` (mostrando versão ou erro) e exibe a lista de pacotes instalados.
- Execute com: `./verify_env.ps1` (ou `.\\verify_env.ps1` no PowerShell).

Se quiser que eu atualize `README.md` para incluir esse conteúdo diretamente, eu posso aplicar essa alteração também (atualmente adicionei `ENVIRONMENT.md` para evitar edições diretas do `README.md`).

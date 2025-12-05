# Poster Black Friday — Gerador de Pôsteres (Atualizado)

Este README inclui instruções de verificação de ambiente e uso do script `verify_env.ps1`.

Resumo rápido
- Projeto: gerador de pôsteres (Flask + Pillow)
- Dependências principais: `Pillow`, `Babel`, `Flask`, `img2pdf` (opcional)

Instruções de instalação e uso

```powershell
# criar venv (recomendado)
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt

# rodar a aplicação Flask
& ".\.venv\Scripts\python.exe" app.py
```

Verificação do ambiente (Windows / PowerShell)
--------------------------------------------

Para garantir que o ambiente virtual e as dependências estão corretas, use o script auxiliar `verify_env.ps1` incluído no projeto ou execute os comandos abaixo manualmente.

- Ativar o `venv` e checar se `img2pdf` está disponível:

```powershell
& ".\.venv\Scripts\Activate.ps1"
& ".\.venv\Scripts\python.exe" -c "import img2pdf, sys; print('img2pdf version:', getattr(img2pdf,'__version__', 'unknown'))"
```

- Se não existir `.venv`, crie e instale as dependências:

```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

- Para listar pacotes instalados no `venv`:

```powershell
& ".\.venv\Scripts\python.exe" -m pip freeze
```

Script auxiliar `verify_env.ps1`
--------------------------------

O arquivo `verify_env.ps1` localizado na raiz do projeto realiza as seguintes checagens:
- Verifica se `.\.venv\Scripts\python.exe` existe
- Imprime a versão do Python usada pelo `venv`
- Testa a importação de `img2pdf` e imprime a versão ou a mensagem de erro
- Mostra os pacotes instalados (pip freeze)

Execute com:

```powershell
.\verify_env.ps1
```

Observações e próximos passos
- Se quiser, posso substituir o `README.md` original pelo conteúdo atualizado automaticamente (posso criar um commit), ou posso abrir um PR com a alteração.
- Também posso estender `verify_env.ps1` para checar versões mínimas ou executar testes automáticos de geração de PDF.

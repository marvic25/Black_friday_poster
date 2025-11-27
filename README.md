# Poster Black Friday — Gerador de Pôsteres

Este script gera um pôster vertical (1080x1920) com promoções no estilo Black Friday.

Principais recursos:
- Gera pôster usando Pillow (Python Imaging Library).
- Formata preços com `de` e `por` usando `Babel` para formato em moeda (pt_BR).
- Aceita um arquivo JSON com lista de ofertas (cada oferta = {"produto":"nome","de":valor,"por":valor}) — passe o caminho do JSON como argumento ao script.

Exemplo de uso (Python):

```powershell
# criar venv (recomendado)
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
# rodar com JSON de ofertas
python poster_black.py ofertas.json

# ou executar em modo interativo para inserir/editar as ofertas na hora
python poster_black.py -i
```

Novos parâmetros CLI e suporte de impressão
-----------------------------------------

Agora o script aceita opções para controle de margem, DPI e bleed (sangria):

```powershell
# usar margem em pixels (ex: 24, 48, 72), DPI (ex: 300) e bleed em mm (ex: 3)
python poster_black.py ofertas.json --margin 48 --dpi 300 --bleed 3
You can also change the poster colors from the CLI using hex color values (e.g. #000000):

```powershell
python poster_black.py ofertas.json --bg-color #000000 --text-color #ffffff --accent-color #ffd400 --badge-color #222222
```

Or configure colors from the web UI using the color pickers for Background, Text, Accent and Badge.


# modo interativo aceita margens/DPI/bleed quando solicitado
python poster_black.py -i
```

Web UI
------
O servidor Flask (`app.py`) agora exibe controles no formulário para ajustar:
- Margem (px) — controla o espaço seguro para impressão
- DPI — metadata de resolução do arquivo de saída
- Bleed (mm) — adiciona sangria ao redor do canvas (útil para gráficas)

Há também um botão "Preview" que gera a imagem no servidor e a exibe inline sem forçar download.


Formato do JSON `ofertas.json` (cada item pode conter `produto`, `de`, `por`, `local`, `locale`):

```json
[
  {"produto": "Smart TV 50\"", "de": 2999.00, "por": 1999.00, "local": "Loja A", "locale": "pt_BR"},
  {"produto": "Smartphone X", "de": 2499.00, "por": 1299.00, "local": "Online", "locale": "pt_BR"}
]
```

Integração com Node.js ou Java

- Node.js
  - Se você preferir gerar pôsteres a partir de um servidor Node, você pode:
    1. Criar um endpoint REST (Express) que conecte com o script Python usando child_process (`spawn`) e passe um JSON. O script Python retorna o caminho do arquivo criado.
    2. Alternativa: gerar o pôster em HTML/CSS e usar `puppeteer` ou `headless-chrome` para gerar imagem/PDF.

- Java
  - Opções para integração:
    1. Criar um microserviço Python (Flask/FastAPI) que gere o pôster a partir de JSON. Seu app Java (Spring Boot) chama esse endpoint via HTTP.
    2. Gerar o pôster diretamente em Java usando `Graphics2D` + `ImageIO`, ou usar bibliotecas como iText (para PDF) se preferir saída PDF.

Qual abordagem você prefere para integrar (API Python, Node.js-spawn, HTML->Puppeteer, ou implementação Java nativa)? Posso implementar a opção escolhida e dar exemplos práticos.

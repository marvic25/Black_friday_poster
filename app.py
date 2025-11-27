from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import csv
import tempfile
import shutil

# Tenta importar img2pdf para gerar o arquivo multipágina
try:
    import img2pdf
except ImportError:
    img2pdf = None

from poster_black import (
    gerar_poster_a_partir_de_lista, 
    TEXTO_VIGENCIA, 
    TEXTO_ESTOQUES, 
    PRINT_MARGIN, 
    DEFAULT_BG, 
    DEFAULT_TEXT, 
    DEFAULT_ACCENT
)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

# --- Funções Auxiliares ---

def rgb_to_hex(rgb):
    try:
        return '#%02x%02x%02x' % rgb
    except Exception:
        return '#000000'

def parse_csv(filepath):
    ofertas = []
    encodings = ['utf-8-sig', 'latin-1'] 
    csv_data = []
    
    for encoding in encodings:
        try:
            with open(filepath, newline='', encoding=encoding) as csvfile:
                reader = csv.DictReader(csvfile)
                csv_data = list(reader)
            break 
        except UnicodeDecodeError:
            continue
            
    for row in csv_data:
        # Normaliza chaves para minúsculo
        row = {k.lower(): v for k, v in row.items() if k}
        
        # Tratamento robusto de FLOAT para dinheiro
        try:
            # Remove R$, espaços e troca vírgula por ponto
            val_de_str = str(row.get('de', '0')).replace('R$', '').replace(' ', '').replace(',', '.')
            de_val = float(val_de_str)
        except ValueError:
            de_val = 0.0
            
        try:
            val_por_str = str(row.get('por', '0')).replace('R$', '').replace(' ', '').replace(',', '.')
            por_val = float(val_por_str)
        except ValueError:
            por_val = 0.0
            
        ofertas.append({
            'produto': row.get('produto', '').strip(),
            'de': de_val,
            'por': por_val,
            'local': row.get('local', '').strip(),
            'locale': row.get('locale', 'pt_BR').strip() or 'pt_BR'
        })
    return ofertas

def dividir_lista(lista, tamanho_do_grupo):
    """Divide a lista total em pedaços (páginas)."""
    for i in range(0, len(lista), tamanho_do_grupo):
        yield lista[i:i + tamanho_do_grupo]

# --- Rotas ---

@app.route('/', methods=['GET', 'POST'])
def index():
    # EXEMPLOS FARMACÊUTICOS (Nomes longos para teste)
    default_offers = [
        {'produto':'Dipirona Monohidratada 500mg 10 Comp','de':8.99,'por':2.99,'local':'','locale':'pt_BR'},
        {'produto':'Protetor Solar Facial FPS 70 Toque Seco 50g','de':89.90,'por':59.90,'local':'','locale':'pt_BR'},
        {'produto':'Fralda Geriátrica Plenitud G 8 Unidades','de':45.50,'por':32.90,'local':'','locale':'pt_BR'},
        {'produto':'Vitamina C Efervescente 1g Laranja c/ 10','de':19.90,'por':12.49,'local':'','locale':'pt_BR'},
        {'produto':'Shampoo Anticaspa Intensivo 200ml','de':35.00,'por':27.90,'local':'','locale':'pt_BR'},
        {'produto':'Kit Creme Dental Leve 3 Pague 2','de':15.90,'por':9.99,'local':'','locale':'pt_BR'},
    ]

    if request.method == 'POST':
        ofertas = []
        csv_file = request.files.get('csvfile')
        
        # 1. Processar CSV
        if csv_file and csv_file.filename:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_csv:
                csv_file.save(tmp_csv.name)
                tmp_path = tmp_csv.name
            try:
                ofertas = parse_csv(tmp_path)
            finally:
                if os.path.exists(tmp_path): os.remove(tmp_path)
        
        # 2. Processar Manual
        else:
            # Lê até 16 produtos manuais (2 páginas cheias)
            for i in range(1, 17):
                nome = request.form.get(f'produto_{i}', '').strip()
                if not nome: continue
                
                # Tratamento float no input manual
                try:
                    de_str = request.form.get(f'de_{i}', '0').replace(',', '.')
                    de_val = float(de_str)
                except ValueError: de_val = 0.0
                
                try:
                    por_str = request.form.get(f'por_{i}', '0').replace(',', '.')
                    por_val = float(por_str)
                except ValueError: por_val = 0.0
                
                local = request.form.get(f'local_{i}', '')
                locale = request.form.get(f'locale_{i}', 'pt_BR')
                ofertas.append({'produto': nome, 'de': de_val, 'por': por_val, 'local': local, 'locale': locale})

        if not ofertas:
            flash("Nenhuma oferta válida encontrada.")
            return redirect(url_for('index'))

        # 3. Paginação e Layout
        layout_mode = request.form.get('layout_mode', 'list')
        
        if layout_mode == 'individual':
            itens_por_pagina = 1
        else:
            try:
                qtd_input = int(request.form.get('qtd_itens', 6))
                if qtd_input < 2: itens_por_pagina = 2
                elif qtd_input > 8: itens_por_pagina = 8
                else: itens_por_pagina = qtd_input
            except ValueError:
                itens_por_pagina = 6
            
        # Parâmetros visuais
        vigencia_text = request.form.get('vigencia', '').strip() or None
        aviso_estoques = request.form.get('estoques', '').strip() or None
        
        # Cores
        bg_color = request.form.get('bg_color')
        text_color = request.form.get('text_color')
        accent_color = request.form.get('accent_color')
        badge_color = request.form.get('badge_color')

        # 4. GERAÇÃO EM LOTE (Paginação Automática)
        temp_images = []
        try:
            # Aqui acontece a mágica: se tiver 20 itens e limite 5, cria 4 grupos
            grupos = list(dividir_lista(ofertas, itens_por_pagina))
            
            for idx, grupo in enumerate(grupos):
                path = gerar_poster_a_partir_de_lista(
                    grupo, 
                    vigencia_text=vigencia_text, 
                    aviso_estoques=aviso_estoques, 
                    bg_color=bg_color, 
                    text_color=text_color, 
                    accent_color=accent_color, 
                    badge_color=badge_color
                )
                # Renomeia para garantir ordem (page_01.png, page_02.png)
                new_path = path.replace('.png', f'_pg{idx}.png')
                shutil.move(path, new_path)
                temp_images.append(new_path)

            # 5. Saída (PDF ou PNG)
            # Se for só 1 página e o usuário pediu PNG/Preview
            if len(temp_images) == 1 and request.form.get('format') != 'pdf':
                if request.form.get('action') == 'preview':
                    return send_file(temp_images[0], mimetype='image/png')
                return send_file(temp_images[0], as_attachment=True)

            # Se for PDF (ou múltiplas páginas que obrigam PDF)
            if not img2pdf:
                flash('Erro: img2pdf não instalado para gerar múltiplas páginas.')
                return redirect(url_for('index'))

            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                pdf_bytes = img2pdf.convert(temp_images)
                tmp_pdf.write(pdf_bytes)
                pdf_path = tmp_pdf.name

            # Limpeza das imagens
            for img in temp_images:
                if os.path.exists(img): os.remove(img)

            return send_file(pdf_path, as_attachment=True, download_name='cartazes_ofertas.pdf')

        except Exception as e:
            flash(f"Erro ao processar: {e}")
            return redirect(url_for('index'))

    defaults = {
        'offers': default_offers,
        'vigencia_default': TEXTO_VIGENCIA,
        'estoque_default': TEXTO_ESTOQUES,
        'margin_default': PRINT_MARGIN,
        'bg_default': rgb_to_hex(DEFAULT_BG),
        'text_default': rgb_to_hex(DEFAULT_TEXT),
        'accent_default': rgb_to_hex(DEFAULT_ACCENT)
    }

    return render_template('index.html', **defaults)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
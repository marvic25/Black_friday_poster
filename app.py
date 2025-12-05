from flask import Flask, render_template, request, send_file, redirect, url_for, flash, after_this_request
import io
from werkzeug.utils import secure_filename
import os
import csv
import tempfile
import shutil
import zipfile

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

# --- Definição de Temas ---
THEMES = {
    'blackfriday': {
        'bg': '#000000',
        'text': '#ffff00',
        'accent': '#ffffff',
        'badge': '#ff0000'
    },
    'natalino': {
        'bg': '#0a3a0a',
        'text': '#ffffff',
        'accent': '#ffcc00',
        'badge': '#ff0000'
    },
    'farmacia': {
        'bg': '#ffffff',
        'text': '#cc0000',
        'accent': '#ffcc00',
        'badge': '#cc0000'
    }
}

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
        elif layout_mode == 'simple':
            # Lista simples: pode conter até 12 produtos por página
            itens_por_pagina = 12
        elif layout_mode == 'gondola':
            # Gôndola / cartazete: 8 por página
            itens_por_pagina = 8
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
        poster_title = request.form.get('poster_title', 'OFERTAS')
        
        # Cores: usa o form, que já foi preenchido pelo JS do tema
        bg_color = request.form.get('bg_color')
        text_color = request.form.get('text_color')
        accent_color = request.form.get('accent_color')
        badge_color = request.form.get('badge_color')

        # 4. GERAÇÃO EM LOTE E LIMPEZA DE ARQUIVOS
        files_to_cleanup = []
        try:
            # Registra uma função para limpar todos os arquivos temporários (PNGs, PDF, ZIP)
            # depois que a requisição for concluída com sucesso.
            @after_this_request
            def cleanup_files(response):
                for f in files_to_cleanup:
                    try:
                        if os.path.exists(f):
                            os.remove(f)
                    except Exception as e:
                        # Idealmente, logar esse erro em um sistema de logging
                        app.logger.error(f"Falha ao limpar arquivo temporário {f}: {e}")
                return response

            # Geração das imagens PNG para cada página
            temp_images = []
            grupos = list(dividir_lista(ofertas, itens_por_pagina))
            for grupo in grupos:
                path = gerar_poster_a_partir_de_lista(
                    grupo,
                    vigencia_text=vigencia_text,
                    aviso_estoques=aviso_estoques,
                    bg_color=bg_color,
                    text_color=text_color,
                    accent_color=accent_color,
                    badge_color=badge_color,
                    layout_mode=layout_mode,
                    poster_title=poster_title,
                )
                temp_images.append(path)
            
            # Adiciona os PNGs gerados à lista de limpeza
            files_to_cleanup.extend(temp_images)

            # Se for uma pré-visualização, sempre retorna a primeira imagem (PNG)
            if request.form.get("action") == "preview":
                # Lê em memória e envia para liberar o arquivo no Windows
                from io import BytesIO
                with open(temp_images[0], 'rb') as f:
                    data = f.read()
                buf = BytesIO(data)
                buf.seek(0)
                return send_file(buf, mimetype='image/png')

            # 5. Saída (PDF, PNG ou ZIP)
            # Se for só 1 página e o usuário pediu PNG/Preview
            if len(temp_images) == 1 and request.form.get("format") != "pdf":
                image_to_send = temp_images[0]
                if request.form.get("action") == "preview":
                    from io import BytesIO
                    with open(image_to_send, 'rb') as f:
                        data = f.read()
                    buf = BytesIO(data)
                    buf.seek(0)
                    return send_file(buf, mimetype='image/png')
                # Para download, também envia em memória para permitir remoção do arquivo
                from io import BytesIO
                with open(image_to_send, 'rb') as f:
                    data = f.read()
                buf = BytesIO(data)
                buf.seek(0)
                return send_file(buf, as_attachment=True, download_name=os.path.basename(image_to_send))

            # Se for PDF (ou múltiplas páginas que obrigam PDF)
            # Tenta gerar PDF primeiro (img2pdf é preferencial pela qualidade)
            if img2pdf:
                fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
                os.close(fd)
                files_to_cleanup.append(pdf_path) # Adiciona à lista de limpeza

                # Converte as imagens e salva no arquivo PDF
                pdf_bytes = img2pdf.convert(temp_images)
                with open(pdf_path, "wb") as f:
                    f.write(pdf_bytes)

                # Envia o PDF em memória para permitir remoção do arquivo no Windows
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()
                buf_pdf = io.BytesIO(pdf_data)
                buf_pdf.seek(0)
                return send_file(buf_pdf, as_attachment=True, download_name="cartazes_ofertas.pdf", mimetype='application/pdf')

            # Se img2pdf não estiver disponível, tenta criar PDF com Pillow (PIL)
            try:
                from PIL import Image

                # Abre imagens e converte para RGB (requisito para salvar em PDF)
                pil_imgs = [Image.open(p).convert("RGB") for p in temp_images]

                fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
                os.close(fd)
                files_to_cleanup.append(pdf_path)

                # Salva multipage PDF usando PIL
                if len(pil_imgs) == 1:
                    pil_imgs[0].save(pdf_path, format="PDF", resolution=150)
                else:
                    pil_imgs[0].save(pdf_path, format="PDF", save_all=True, append_images=pil_imgs[1:], resolution=150)

                # Envia o PDF em memória para permitir remoção do arquivo no Windows
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()
                buf_pdf = io.BytesIO(pdf_data)
                buf_pdf.seek(0)
                return send_file(buf_pdf, as_attachment=True, download_name="cartazes_ofertas.pdf", mimetype='application/pdf')
            except Exception:
                # Último recurso: empacotar imagens em ZIP
                fd, zip_path = tempfile.mkstemp(suffix=".zip")
                os.close(fd)
                files_to_cleanup.append(zip_path)

                with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for img in temp_images:
                        arcname = os.path.basename(img)
                        zf.write(img, arcname=arcname)

                flash("Não foi possível gerar PDF (tentadas img2pdf e PIL) — fornecendo ZIP com as imagens geradas.")
                # Envia o ZIP em memória
                with open(zip_path, 'rb') as f:
                    zip_data = f.read()
                buf_zip = io.BytesIO(zip_data)
                buf_zip.seek(0)
                return send_file(buf_zip, as_attachment=True, download_name="cartazes_ofertas.zip", mimetype='application/zip')

        except Exception as e:
            # Em caso de erro, faz a limpeza manualmente, pois o hook @after_this_request não será executado.
            for f in files_to_cleanup:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception as e_clean:
                    app.logger.error(f"Falha ao limpar arquivo temporário {f} durante tratamento de erro: {e_clean}")
            
            app.logger.error(f"Erro ao processar a geração do poster: {e}", exc_info=True)
            flash(f"Erro ao processar: {str(e)}")
            return redirect(url_for("index"))

    defaults = {
        'offers': default_offers,
        'vigencia_default': TEXTO_VIGENCIA,
        'estoque_default': TEXTO_ESTOQUES,
        'margin_default': PRINT_MARGIN,
        'bg_default': THEMES['blackfriday']['bg'],
        'text_default': THEMES['blackfriday']['text'],
        'accent_default': THEMES['blackfriday']['accent'],
        'badge_default': THEMES['blackfriday']['badge'],
        'themes': THEMES
    }

    return render_template('index.html', **defaults)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
& ".\.venv\Scripts\Activate.ps1"
& ".\.venv\Scripts\python.exe" app.py
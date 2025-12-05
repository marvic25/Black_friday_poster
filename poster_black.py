import os
import tempfile
import uuid
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURAÇÕES VISUAIS ---
DEFAULT_BG = (0, 0, 0)
DEFAULT_TEXT = (255, 255, 0)     # Amarelo
DEFAULT_ACCENT = (255, 255, 255) # Branco
BADGE_COLOR = (255, 0, 0)        # Vermelho

PRINT_MARGIN = 40
TEXTO_VIGENCIA = "Ofertas válidas enquanto durarem os estoques."
TEXTO_ESTOQUES = "Consulte disponibilidade."

# --- FUNÇÕES DE FONTE ---

def get_font_path(bold=False):
    """Seleciona a fonte correta dependendo do sistema (Windows/Linux)."""
    if bold:
        # Tenta Arial Bold, depois DejaVu Bold
        options = ["arialbd.ttf", "DejaVuSans-Bold.ttf", "FreeSansBold.ttf"]
    else:
        options = ["arial.ttf", "DejaVuSans.ttf", "FreeSans.ttf"]
    
    for font in options:
        # Verifica se o arquivo existe no sistema ou na pasta atual
        try:
            ImageFont.truetype(font, 10) # Teste rápido
            return font
        except IOError:
            continue
    return "arial.ttf" # Fallback final

def get_font(size, bold=False):
    try:
        return ImageFont.truetype(get_font_path(bold), int(size))
    except IOError:
        return ImageFont.load_default()

def formatar_moeda(valor):
    """Recebe float (2.99) e retorna string ('R$ 2,99')."""
    try:
        val_float = float(valor)
        return f"R$ {val_float:,.2f}".replace('.', ',')
    except:
        return "R$ 0,00"

# --- INTELIGÊNCIA DE TEXTO (A CORREÇÃO PRINCIPAL) ---

def caber_texto_na_caixa(draw, text, max_width, max_height, start_font_size, is_bold=True):
    """
    Tenta encaixar o texto na caixa (Largura x Altura).
    1. Quebra o texto em linhas (Word Wrap).
    2. Calcula a altura total.
    3. Se for maior que max_height, diminui a fonte e tenta de novo.
    """
    size = int(start_font_size)
    min_size = 14 # Tamanho mínimo aceitável
    font_path = get_font_path(bold=is_bold)

    while size >= min_size:
        try:
            font = ImageFont.truetype(font_path, size)
        except:
            font = ImageFont.load_default()
            return [text], font, size # Falha na fonte

        # 1. Lógica de Word Wrap (Quebra de linha)
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Simula a linha com a palavra adicionada
            test_line = ' '.join(current_line + [word])
            w_line = draw.textlength(test_line, font=font)
            
            if w_line <= max_width:
                current_line.append(word)
            else:
                # Linha cheia, guarda e começa nova
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word] # A palavra que não coube começa a nova linha
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # 2. Verifica Altura Total
        # Altura da linha = tamanho da fonte + 15% de espaçamento
        line_height = size * 1.15
        total_block_height = len(lines) * line_height
        
        # Se couber na altura disponível, SUCESSO!
        if total_block_height <= max_height:
            return lines, font, total_block_height, line_height

        # Se não coube, reduz a fonte e repete o loop
        size -= 2

    # Se saiu do loop, é porque nem no tamanho mínimo coube.
    # Trunca o texto com "..."
    return [text[:30] + "..."], font, total_block_height, line_height


# --- DESENHO DOS CARTAZES ---

def desenhar_item_individual(draw, item, W, H, margin, y_start, y_end, text_color, accent_color, badge_color):
    """
    Layout Individual:
    - Nome usa a lógica inteligente (quebra linha e reduz fonte se for longo).
    """
    area_h = y_end - y_start
    
    # --- 1. NOME DO PRODUTO (INTELIGENTE) ---
    prod_raw = item.get('produto', 'Produto').upper()
    
    # Define a área disponível para o nome (Topo da área útil)
    # Vamos dar 35% da altura útil para o nome, para sobrar espaço pro preço gigante
    max_h_name = area_h * 0.35
    max_w_name = W - (margin * 2)
    ideal_font_size = W * 0.10 # Começa tentando ser gigante (10% da largura)

    lines, font_prod, total_h, line_h = caber_texto_na_caixa(
        draw, prod_raw, max_w_name, max_h_name, ideal_font_size, is_bold=True
    )
    
    # Desenha as linhas centralizadas
    y_cursor = y_start + 20
    for line in lines:
        w_line = draw.textlength(line, font=font_prod)
        x_line = (W - w_line) / 2
        draw.text((x_line, y_cursor), line, font=font_prod, fill=accent_color)
        y_cursor += line_h

    # --- 2. PREÇOS ---
    # O espaço que sobrou abaixo do nome
    remaining_y_start = y_cursor + 20
    remaining_h = y_end - remaining_y_start
    center_price_y = remaining_y_start + (remaining_h / 2)

    de = item.get('de', 0.0)
    por = item.get('por', 0.0)

    # Preço DE
    if de > por:
        font_de_size = W * 0.06
        font_de = get_font(font_de_size, bold=True)
        texto_de = f"DE: {formatar_moeda(de)}"
        
        bbox = draw.textbbox((0, 0), texto_de, font=font_de)
        w_de = bbox[2] - bbox[0]
        h_de = bbox[3] - bbox[1]
        
        y_de = center_price_y - (h_de * 1.8)
        x_de = (W - w_de) / 2
        
        draw.text((x_de, y_de), texto_de, font=font_de, fill=badge_color)
        draw.line((x_de, y_de + h_de/2 + 5, x_de + w_de, y_de + h_de/2 + 5), fill=badge_color, width=4)
        y_por_base = center_price_y + (h_de * 0.2)
    else:
        y_por_base = center_price_y - (W * 0.08)

    # Preço POR
    font_lbl_size = W * 0.05
    font_rs_size = W * 0.10
    font_int_size = W * 0.35
    font_dec_size = W * 0.15
    
    font_lbl = get_font(font_lbl_size, bold=True)
    font_rs = get_font(font_rs_size, bold=True)
    font_int = get_font(font_int_size, bold=True)
    font_dec = get_font(font_dec_size, bold=True)
    
    # Separa R$ XX, YY
    val_str = f"{por:.2f}"
    inteiro, decimal = val_str.split('.')
    
    # Label "POR:"
    lbl_text = "POR:"
    w_lbl = draw.textlength(lbl_text, font=font_lbl)
    x_lbl = (W - w_lbl) / 2
    draw.text((x_lbl, y_por_base - font_lbl_size - 10), lbl_text, font=font_lbl, fill=text_color)
    
    # Valor
    y_val = y_por_base + 10
    w_rs = draw.textlength("R$", font=font_rs)
    w_int = draw.textlength(inteiro, font=font_int)
    w_dec = draw.textlength("," + decimal, font=font_dec)
    total_w = w_rs + w_int + w_dec
    start_x = (W - total_w) / 2
    
    draw.text((start_x, y_val + (font_int_size - font_rs_size)), "R$", font=font_rs, fill=text_color)
    draw.text((start_x + w_rs, y_val), inteiro, font=font_int, fill=text_color)
    draw.text((start_x + w_rs + w_int, y_val), "," + decimal, font=font_dec, fill=text_color)


def desenhar_lista_produtos(draw, ofertas, W, H, margin, y_start, y_end, text_color, accent_color, badge_color):
    """
    Layout Lista:
    - Coluna Nome (Esq): Usa 'caber_texto_na_caixa' para quebrar e reduzir fonte.
    - Coluna Preço (Dir): Fixa e alinhada.
    """
    qtd = len(ofertas)
    # Altura exata de cada linha da tabela
    row_height = (y_end - y_start) / qtd
    
    # Definição das colunas
    usable_width = W - (margin * 2)
    col_name_w = usable_width * 0.55
    # col_price_w = usable_width * 0.40
    
    # Fonte base ideal (vai reduzir se não couber)
    ideal_font_size = row_height * 0.35
    
    # Fontes de preço (fixas para manter padrão)
    f_price_lbl = row_height * 0.15
    f_price_val = row_height * 0.35
    font_lbl = get_font(f_price_lbl, bold=True)
    font_val = get_font(f_price_val, bold=True)

    for i, item in enumerate(ofertas):
        y_pos = y_start + (i * row_height)
        y_center = y_pos + (row_height / 2)
        
        # Zebrado
        if i % 2 == 0:
            draw.rectangle([margin, y_pos, W - margin, y_pos + row_height], fill=(25, 25, 25))

        # --- NOME (ESQUERDA - INTELIGENTE) ---
        prod_raw = item.get('produto', '').upper()
        # O texto pode ocupar até 85% da altura da linha, senão reduz
        max_h_text = row_height * 0.85
        
        # CHAMA A FUNÇÃO DE AJUSTE
        lines, font_final, total_h, line_h = caber_texto_na_caixa(
            draw, prod_raw, col_name_w, max_h_text, ideal_font_size, is_bold=True
        )
        
        # Desenha as linhas centralizadas verticalmente na célula
        y_cursor = y_pos + (row_height - total_h) / 2
        for line in lines:
            draw.text((margin + 10, y_cursor), line, font=font_final, fill=accent_color)
            y_cursor += line_h

        # --- PREÇOS (DIREITA) ---
        de = item.get('de', 0.0)
        por = item.get('por', 0.0)
        x_anchor = W - margin - 10
        
        # Valor POR
        str_por = formatar_moeda(por)
        w_por = draw.textlength(str_por, font=font_val)
        y_por = y_center - (f_price_val / 2) + (f_price_lbl / 2)
        
        draw.text((x_anchor - w_por, y_por), str_por, font=font_val, fill=text_color)
        
        # Label POR
        str_lbl = "POR:"
        draw.text((x_anchor - w_por, y_por - f_price_lbl - 2), str_lbl, font=font_lbl, fill=text_color)
        
        # Valor DE (se existir)
        if de > por:
            str_de = f"DE: {formatar_moeda(de)}"
            w_de = draw.textlength(str_de, font=font_lbl)
            y_de = y_por - f_price_lbl - f_price_lbl - 8
            x_de = x_anchor - w_de # Alinha pelo final
            
            draw.text((x_de, y_de), str_de, font=font_lbl, fill=badge_color)
            draw.line((x_de, y_de + f_price_lbl/2, x_anchor, y_de + f_price_lbl/2), fill=badge_color, width=2)


def desenhar_lista_simples(draw, ofertas, W, H, margin, y_start, y_end, text_color, accent_color, badge_color):
    """
    Layout simples: lista com nome do produto (esquerda) e preço final (direita).
    Pensado para até 12 itens por folha — usa fonte maior e limpa.
    """
    qtd = len(ofertas) if len(ofertas) > 0 else 1
    available_h = y_end - y_start
    row_height = available_h / qtd

    # Coluna nome ocupa ~70% da largura
    usable_width = W - (margin * 2)
    col_name_w = usable_width * 0.70

    # Fontes: nome e preço
    font_name_size = max(14, int(row_height * 0.35))
    font_price_size = max(14, int(row_height * 0.45))
    font_name = get_font(font_name_size, bold=False)
    font_price = get_font(font_price_size, bold=True)

    for i, item in enumerate(ofertas):
        y_pos = y_start + (i * row_height)
        y_center = y_pos + (row_height / 2)

        # Alterna leve cor de fundo para leitura
        if i % 2 == 0:
            draw.rectangle([margin, y_pos, W - margin, y_pos + row_height], fill=(20, 20, 20))

        prod_raw = item.get('produto', '').strip()
        por = item.get('por', 0.0)

        # Quebra o nome na largura disponível, reduzindo fonte se necessário
        max_h_text = row_height * 0.9
        lines, font_final, total_h, line_h = caber_texto_na_caixa(
            draw, prod_raw.upper(), col_name_w, max_h_text, font_name_size, is_bold=False
        )

        y_cursor = y_pos + (row_height - total_h) / 2
        for line in lines:
            draw.text((margin + 10, y_cursor), line, font=font_final, fill=accent_color)
            y_cursor += line_h

        # Preço final alinhado à direita
        price_text = formatar_moeda(por)
        w_price = draw.textlength(price_text, font=font_price)
        x_price = W - margin - 10 - w_price
        y_price = y_center - (font_price_size / 2)
        draw.text((x_price, y_price), price_text, font=font_price, fill=text_color)


def desenhar_gondola(draw, ofertas, W, H, margin, y_start, y_end, text_color, accent_color, badge_color):
    """
    Gôndola / Cartazete: 8 por página em grid 2x4.
    Cada item ocupa um 'cartazete' com nome (esquerda/alto) e preço (direita/baixo) legível.
    """
    cols = 2
    rows = 4
    gap = max(8, int(W * 0.02))

    usable_w = W - (margin * 2) - (gap * (cols - 1))
    card_w = usable_w / cols
    usable_h = (y_end - y_start) - (gap * (rows - 1))
    card_h = usable_h / rows

    # Fonte base aproximada
    for idx, item in enumerate(ofertas[:cols * rows]):
        r = idx // cols
        c = idx % cols

        x0 = margin + c * (card_w + gap)
        y0 = y_start + r * (card_h + gap)
        x1 = int(x0 + card_w)
        y1 = int(y0 + card_h)

        # Card background (slightly lighter to separate)
        draw.rectangle([x0, y0, x1, y1], fill=(18, 18, 18))

        padding = 8

        # Nome produto (usa até 60% da largura do cartazete)
        name_w = (card_w - padding * 2) * 0.65
        name_max_h = card_h * 0.55
        name_font_start = max(12, int(card_h * 0.16))
        prod_raw = item.get('produto', '').upper()
        lines, font_final, total_h, line_h = caber_texto_na_caixa(
            draw, prod_raw, name_w, name_max_h, name_font_start, is_bold=False
        )

        y_cursor = y0 + padding + (name_max_h - total_h) / 2
        for line in lines:
            draw.text((x0 + padding, y_cursor), line, font=font_final, fill=accent_color)
            y_cursor += line_h

        # Preço grande alinhado à direita/bottom do cartazete
        por = item.get('por', 0.0)
        price_font_size = max(14, int(card_h * 0.28))
        font_price = get_font(price_font_size, bold=True)
        price_text = formatar_moeda(por)
        w_price = draw.textlength(price_text, font=font_price)
        px = x1 - padding - w_price
        py = y1 - padding - price_font_size
        draw.text((px, py), price_text, font=font_price, fill=text_color)

        # DE (se existir) pequeno acima do preço
        de = item.get('de', 0.0)
        if de > por:
            font_de = get_font(max(10, int(price_font_size * 0.45)), bold=True)
            de_text = f"DE: {formatar_moeda(de)}"
            w_de = draw.textlength(de_text, font=font_de)
            dx = x1 - padding - w_de
            dy = py - (font_de.size if hasattr(font_de, 'size') else price_font_size * 0.5) - 4
            draw.text((dx, dy), de_text, font=font_de, fill=badge_color)


def gerar_poster_a_partir_de_lista(ofertas, vigencia_text=None, aviso_estoques=None, 
                                   print_margin=None, dpi=None, bleed_mm=None,
                                   bg_color=None, text_color=None, accent_color=None, badge_color=None,
                                   layout_mode='list', poster_title="OFERTAS"):
    
    DPI = dpi or 150
    W = int((210 * DPI) / 25.4)
    H = int((297 * DPI) / 25.4)
    margin = print_margin if print_margin is not None else int(PRINT_MARGIN * (DPI/72))

    def hex_to_rgb(h): return tuple(int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    c_bg = hex_to_rgb(bg_color) if bg_color else DEFAULT_BG
    c_text = hex_to_rgb(text_color) if text_color else DEFAULT_TEXT
    c_accent = hex_to_rgb(accent_color) if accent_color else DEFAULT_ACCENT
    c_badge = hex_to_rgb(badge_color) if badge_color else BADGE_COLOR

    img = Image.new('RGB', (W, H), color=c_bg)
    draw = ImageDraw.Draw(img)

    # 1. RODAPÉ (Calcula espaço necessário)
    vigencia = vigencia_text if vigencia_text else TEXTO_VIGENCIA
    if aviso_estoques: vigencia += f" | {aviso_estoques}"
    
    font_foot = get_font(int(W * 0.025))
    # Usa a função inteligente também para o rodapé (para não quebrar errado)
    lines_foot, _, total_h_foot, line_h_foot = caber_texto_na_caixa(
        draw, vigencia, W - (margin*2), H * 0.1, int(W * 0.025), is_bold=False
    )
    
    y_foot = H - margin - total_h_foot
    for line in lines_foot:
        w_line = draw.textlength(line, font=font_foot)
        draw.text(((W - w_line)/2, y_foot), line, font=font_foot, fill=c_accent)
        y_foot += line_h_foot

    # 2. CABEÇALHO (com ajuste automático de título)
    h_header = int(H * 0.12)
    y_header_start = margin

    max_w_title = W - (margin * 2)
    max_h_title = h_header
    start_font_size_title = int(h_header * 0.7) # Start with a large font

    # Usa a função inteligente para ajustar o título (quebra linhas e reduz fonte)
    title_lines, title_font, title_total_h, title_line_h = caber_texto_na_caixa(
        draw, poster_title.upper(), max_w_title, max_h_title, start_font_size_title, is_bold=True
    )
    
    # Desenha o título centralizado (horizontal e verticalmente na área do cabeçalho)
    y_cursor = y_header_start + (max_h_title - title_total_h) / 2
    for line in title_lines:
        w_line = draw.textlength(line, font=title_font)
        x_line = (W - w_line) / 2
        draw.text((x_line, y_cursor), line, font=title_font, fill=c_text)
        y_cursor += title_line_h

    # 3. ÁREA ÚTIL
    y_start = margin + h_header
    y_end = H - margin - total_h_foot - 20
    
    # Escolhe o layout de desenho de acordo com o modo solicitado
    if layout_mode == 'individual' or len(ofertas) == 1:
        desenhar_item_individual(draw, ofertas[0], W, H, margin, y_start, y_end, c_text, c_accent, c_badge)
    elif layout_mode == 'simple':
        desenhar_lista_simples(draw, ofertas, W, H, margin, y_start, y_end, c_text, c_accent, c_badge)
    elif layout_mode == 'gondola':
        desenhar_gondola(draw, ofertas, W, H, margin, y_start, y_end, c_text, c_accent, c_badge)
    else:
        desenhar_lista_produtos(draw, ofertas, W, H, margin, y_start, y_end, c_text, c_accent, c_badge)

    # Salva a imagem em um arquivo temporário único para evitar conflitos
    out_filename = f"poster_{uuid.uuid4()}.png"
    out_path = os.path.join(tempfile.gettempdir(), out_filename)
    img.save(out_path)
    return out_path
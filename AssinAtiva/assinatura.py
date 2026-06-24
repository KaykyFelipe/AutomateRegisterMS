from PIL import Image, ImageDraw, ImageFont
import os
import sys
import unicodedata

def baixar_fontes():
    """
    Instrui o usuário a baixar as fontes necessárias
    """
    print("\n⚠️  FONTES NECESSÁRIAS:")
    print("1. Rubik Bold - https://fonts.google.com/specimen/Rubik")
    print("2. Nunito SemiBold e Regular - https://fonts.google.com/specimen/Nunito")
    print("\nBaixe as fontes e coloque os arquivos .ttf na pasta 'fonts' na raiz deste repositório.")
    print("(Ex: ./fonts/Rubik-Bold.ttf e ./fonts/Nunito-Regular.ttf)\n")

def criar_assinatura(nome_param=None, cargo_param=None, filial_param=None, local_param=None, telefone_filial_param=None, email_manual_param=None, telefone_param=None, ramal_param=None, email_param=None):
    """
    Cria uma assinatura de e-mail personalizada em formato PNG
    usando o modelo base fornecido com especificações exatas
    """

    # Coletar informações do usuário
    print("=== GERADOR DE ASSINATURA DE E-MAIL ATIVA LOCAÇÃO ===\n")

    nome = nome_param if nome_param is not None else input("Qual nome do colaborador? ").strip()
    nome_limpo = unicodedata.normalize('NFD', nome).encode('ascii', 'ignore').decode('utf-8')
    email = ".".join(nome_limpo.lower().split())
    cargo = cargo_param if cargo_param is not None else input("Qual cargo? ").strip()

    # Dicionário de filiais
    filiais = {
        '1': {
            'local': 'Matriz/SP',
            'telefone': '(16) 3603-8114'
        },
        '2': {
            'local': 'Cuiabá/MT',
            'telefone': '(65) 3665-4224'
        },
        '3': {
            'local': 'Uberlândia/MG',
            'telefone': '(34) 3226-2223'
        },
        '4': {
            'local': 'Limeira/SP',
            'telefone': '(19) 3444-6753'
        },
        '5': {
            'local': 'Campo Grande/MS',
            'telefone': '(67) 3354-6060'
        },
        '6': {
            'local': 'Araçatuba/SP',
            'telefone': '(18) 3621-0669'
        },
        '7': {
            'local': 'Londrina/PR',
            'telefone': '(43) 3343-1604'
        },
        '8': {
            'local': 'Ribeirão Preto/SP',
            'telefone': '(16) 3603-8114'
        }
    }

    filial = filial_param if filial_param is not None else input("Qual o número da filial?\n1-Matriz/SP\n2-Cuiabá/MT\n3-Uberlândia/MG\n4-Limeira/SP\n5-Campo Grande/MS\n6-Araçatuba/SP\n7-Londrina/PR\n8-Ribeirão Preto/SP\n9-Personalizado\n").strip()
    while filial not in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
        print("Opção inválida. Por favor, escolha um número de 1 a 9.")
        filial = input("Qual o número da filial?\n1-Matriz/SP\n2-Cuiabá/MT\n3-Uberlândia/MG\n4-Limeira/SP\n5-Campo Grande/MS\n6-Araçatuba/SP\n7-Londrina/PR\n8-Ribeirão Preto/SP\n9-Personalizado\n").strip()

    if filial == '9':
        local = local_param if local_param is not None else input("Qual local da filial? (Ex: São Paulo/SP) ").strip()
        telefone_filial = telefone_filial_param if telefone_filial_param is not None else input("Qual telefone da filial? (Pressione ENTER para pular) ").strip()
        
        # Look up the telephone if it was not provided but local matches
        if not telefone_filial:
            for key, val in filiais.items():
                if val['local'] == local:
                    telefone_filial = val['telefone']
                    break

        email_manual = email_manual_param if email_manual_param is not None else input("Qual e-mail? (Pressione ENTER para usar email padrão) ").strip()
        if '/' in local:
            cidade, uf = local.split('/', 1)
            cidade = cidade.strip()
            uf = uf.strip()
        else:
            cidade = local
            uf = ''
    else:
        cidade = filiais[filial]['local'].split('/')[0]
        uf = filiais[filial]['local'].split('/')[1]
        telefone_filial = filiais[filial]['telefone']
        email_manual = email_manual_param if email_manual_param is not None else ""

    telefone = telefone_param if telefone_param is not None else input("Qual TELEFONE? (Pressione ENTER para pular) ").strip()
    ramal = ramal_param if ramal_param is not None else input("Qual ramal? (Pressione ENTER para pular) ").strip()

    # Base do repositório (pasta onde está este script)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Procurar modelo (aceita model.png ou model.jpg na raiz do repositório)
    modelo_path = os.path.join(base_dir, 'model.png')
    if not os.path.exists(modelo_path):
        modelo_path = os.path.join(base_dir, 'model.jpg')

    # Verificar se o modelo existe
    if not os.path.exists(modelo_path):
        print(f"\n❌ Erro: Modelo não encontrado em {modelo_path}")
        print("Coloque 'model.png' ou 'model.jpg' na raiz do repositório ao lado de assinatura.py")
        return None

    # Abrir imagem modelo
    img = Image.open(modelo_path)
    draw = ImageDraw.Draw(img)

    # Cores em RGB (convertido de hexadecimal)
    cor_azul = (9, 83, 160)      # #0953A0
    cor_verde = (78, 173, 64)     # #4EAD40

    # Tentar carregar fontes
    fontes_carregadas = True

    # Pasta de fontes dentro do repositório
    fonts_dir = os.path.join(base_dir, 'fonts')

    def find_font_path(fonts_root, keywords, exact=False):
        if not os.path.exists(fonts_root):
            return None
        for root, _, files in os.walk(fonts_root):
            for f in files:
                if f.lower().endswith('.ttf'):
                    name = f.lower()
                    if exact and all(k.lower() in name for k in keywords) and name.count('-') >= len(keywords) - 1:
                        return os.path.join(root, f)
                    if not exact and all(k.lower() in name for k in keywords):
                        return os.path.join(root, f)
        if exact:
            return None
        # fallback: any that contains any keyword
        for root, _, files in os.walk(fonts_root):
            for f in files:
                if f.lower().endswith('.ttf'):
                    name = f.lower()
                    if any(k.lower() in name for k in keywords):
                        return os.path.join(root, f)
        return None

    try:
        # Tentar carregar fontes a partir da pasta ./fonts/ do repositório
        rubik_path = find_font_path(fonts_dir, ['rubik', 'bold'], exact=True) or find_font_path(fonts_dir, ['rubik', 'bold']) or find_font_path(fonts_dir, ['rubik'])
        nunito_bold_path = find_font_path(fonts_dir, ['nunito', 'bold'], exact=True) or find_font_path(fonts_dir, ['nunito', 'bold'])
        nunito_semibold_path = find_font_path(fonts_dir, ['nunito', 'semibold'], exact=True) or find_font_path(fonts_dir, ['nunito', 'semibold'])
        nunito_regular_path = find_font_path(fonts_dir, ['nunito', 'regular'], exact=True) or find_font_path(fonts_dir, ['nunito', 'regular'])

        if rubik_path and (nunito_bold_path or nunito_semibold_path) and nunito_regular_path:
            fonte_nome = ImageFont.truetype(rubik_path, 65)
            fonte_cargo_path = nunito_bold_path or nunito_semibold_path
            fonte_cargo = ImageFont.truetype(fonte_cargo_path, 29)
            fonte_info = ImageFont.truetype(nunito_regular_path, 29)
            print(f"Fonts loaded from repo:\n Rubik: {rubik_path}\n Nunito cargo: {fonte_cargo_path}\n Nunito Regular: {nunito_regular_path}")
        else:
            # Tentar carregar das fontes do sistema (se instaladas)
            fonte_nome = ImageFont.truetype("Rubik-Bold.ttf", 65)
            fonte_cargo = ImageFont.truetype("Nunito-Bold.ttf", 29)
            fonte_info = ImageFont.truetype("Nunito-Regular.ttf", 29)
    except Exception:
        fontes_carregadas = False
        print("\n⚠️  AVISO: Fontes Rubik e Nunito não encontradas no repositório nem no sistema!")
        print("O resultado pode não ficar idêntico ao modelo.")
        print("Para melhor resultado, coloque os arquivos .ttf em ./fonts/ ou instale as fontes no sistema.\n")

        # Usar Arial como fallback
        try:
            fonte_nome = ImageFont.truetype("arialbd.ttf", 65)
            fonte_cargo = ImageFont.truetype("arialbd.ttf", 29)
            fonte_info = ImageFont.truetype("arial.ttf", 29)
        except Exception:
            fonte_nome = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 65)
            fonte_cargo = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 29)
            fonte_info = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 29)
            print("E")

    # Configurar espaçamento entre letras (letter spacing -3%)
    # Pillow não tem suporte nativo para letter-spacing, então vamos desenhar caractere por caractere

    def desenhar_texto_com_spacing(draw, pos, texto, fonte, cor, spacing_percent=-0.03, stroke_width=0, stroke_fill=None):
        """
        Desenha texto com letter spacing personalizado
        spacing_percent: percentual de espaçamento (-0.03 = -3%)
        stroke_width: espessura do contorno usado para dar efeito de negrito
        stroke_fill: cor do contorno (se None, usa a mesma cor de preenchimento)
        """
        x, y = pos
        for char in texto:
            sf = stroke_fill if stroke_fill is not None else cor
            draw.text((x, y), char, fill=cor, font=fonte, stroke_width=stroke_width, stroke_fill=sf)
            char_width = draw.textbbox((0, 0), char, font=fonte)[2]
            x += char_width + (char_width * spacing_percent)

    # NOME - Rubik Bold, 65pt, Cor: #0953A0, Posição: X:449 Y:44
    # Letter spacing: -3%, sem forçar maiúsculas
    desenhar_texto_com_spacing(draw, (449, 44), nome, fonte_nome, cor_azul)

    # CARGO - CIDADE/UF - Nunito SemiBold, 29pt, Cor: #4EAD40
    # Letter spacing: -3%, sem forçar maiúsculas
    location_text = f"{cidade}/{uf}" if cidade and uf else cidade
    cargo_completo = f"{cargo} - {location_text}" if location_text else cargo
    if filial != '9':
        desenhar_texto_com_spacing(draw, (449, 119), cargo_completo, fonte_cargo, cor_verde)

    # E-MAIL - Nunito Regular, 29pt, Cor: #0953A0
    # Letter spacing: -3%
    if email_param is not None:
        email_completo = email_param
    elif email_manual and email_manual.strip() != "":
        email_completo = email_manual
    else:
        email_completo = f"{email}@ativalocacao.com.br"

    if filial == '9':
        current_y = 119

        if cargo_completo:
            desenhar_texto_com_spacing(draw, (449, current_y), cargo_completo, fonte_cargo, cor_verde)
            current_y += 42

        if email_completo:
            desenhar_texto_com_spacing(draw, (449, current_y), email_completo, fonte_info, cor_azul)
            current_y += 42

        if telefone_filial and telefone:
            telefone_texto = f"Tel.: {telefone_filial} / {telefone}"
        elif telefone_filial:
            telefone_texto = f"Tel.: {telefone_filial}"
        elif telefone:
            telefone_texto = f"Tel.: {telefone}"
        else:
            telefone_texto = ""

        if telefone_texto:
            desenhar_texto_com_spacing(draw, (449, current_y), telefone_texto, fonte_info, cor_azul)
            current_y += 42

        if ramal:
            ramal_label = "Whatsapp:" if len(''.join(ch for ch in ramal if ch.isdigit())) > 5 else "Ramal:"
            ramal_texto = f"{ramal_label} {ramal}"
            desenhar_texto_com_spacing(draw, (449, current_y), ramal_texto, fonte_info, cor_azul)
    else:
        desenhar_texto_com_spacing(draw, (449, 166), email_completo, fonte_info, cor_azul)

        if telefone_filial and telefone:
            telefone_texto = f"Tel.: {telefone_filial} / {telefone}"
        elif telefone_filial:
            telefone_texto = f"Tel.: {telefone_filial}"
        elif telefone:
            telefone_texto = f"Tel.: {telefone}"
        else:
            telefone_texto = ""

        if telefone_texto:
            desenhar_texto_com_spacing(draw, (449, 208), telefone_texto, fonte_info, cor_azul)

        if ramal:
            ramal_label = "Whatsapp:" if len(''.join(ch for ch in ramal if ch.isdigit())) > 5 else "Ramal:"
            ramal_texto = f"{ramal_label} {ramal}"
            desenhar_texto_com_spacing(draw, (449, 246), ramal_texto, fonte_info, cor_azul)

    # Criar diretório de saída dentro do repositório
    output_dir = os.path.join(base_dir, 'Assinaturas')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Nome do arquivo
    nome_arquivo = f"{nome.replace(' ', '_').lower()}_assinatura.png"
    caminho_completo = os.path.join(output_dir, nome_arquivo)

    # Salvar imagem
    img.save(caminho_completo, "PNG")

    print("\nAssinatura criada com sucesso!")
    print(f"Arquivo salvo em: {caminho_completo}")
    print(f"Filial: {cidade}/{uf} - Tel.: {telefone_filial}")

    if fontes_carregadas:
        print("Fontes corretas aplicadas!")

    return caminho_completo

if __name__ == "__main__":
    try:
        # Verificar se as fontes estão disponíveis
        base_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.join(base_dir, 'fonts')
        if not os.path.exists(fonts_dir):
            os.makedirs(fonts_dir)
            baixar_fontes()

        criar_assinatura()

    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro ao criar assinatura: {e}")
        print("\nVerifique:")
        print("1. Se a biblioteca Pillow está instalada: pip install Pillow")
        print("2. Se o arquivo model.png ou model.jpg existe ao lado de assinatura.py")
        print("3. Se as fontes estão instaladas no sistema ou em ./fonts/ dentro do repositório")





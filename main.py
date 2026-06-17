import unicodedata
import re
import random
import string
import requests
import os
import sys
import time
import base64
import msal
import openpyxl
from dotenv import load_dotenv

import database

# Adiciona o diretório AssinAtiva ao sys.path para importar o gerador
base_dir = os.path.dirname(os.path.abspath(__file__))
assin_ativa_path = os.path.join(base_dir, 'AssinAtiva')
if assin_ativa_path not in sys.path:
    sys.path.append(assin_ativa_path)

try:
    import assinatura
except ImportError:
    print("Aviso: Módulo 'assinatura' não encontrado em AssinAtiva.")

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do Azure AD / Microsoft Graph
CLIENT_ID = os.environ.get("MS_CLIENT_ID", "seu_client_id_aqui").strip()
CLIENT_SECRET = os.environ.get("MS_CLIENT_SECRET", "seu_client_secret_aqui").strip()
TENANT_ID = os.environ.get("MS_TENANT_ID", "seu_tenant_id_aqui").strip()

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

def remove_accents(input_str):
    """Remove acentos de uma string."""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode('utf-8')

def sanitize_and_extract_names(full_name):
    """Extrai e sanitiza o primeiro e último nome."""
    # Remove extra spaces
    clean_name = " ".join(full_name.strip().split())
    
    parts = clean_name.split(" ")
    if len(parts) < 2:
        raise ValueError("O nome completo deve conter pelo menos primeiro e último nome (Ex: João Silva).")
    
    first_name_raw = parts[0].title()
    last_name_raw = parts[-1].title()
    
    first_name_clean = re.sub(r'[^a-z0-9]', '', remove_accents(first_name_raw).lower())
    last_name_clean = re.sub(r'[^a-z0-9]', '', remove_accents(last_name_raw).lower())
    
    return first_name_raw, last_name_raw, first_name_clean, last_name_clean

def generate_password(length=12):
    """Gera uma senha forte temporária."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    # Garantir pelo menos um caractere de cada tipo necessário
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*")
    ]
    password += random.choices(characters, k=length-4)
    random.shuffle(password)
    return "".join(password)

def get_access_token():
    """Obtém o token de acesso da API do Microsoft Graph."""
    if CLIENT_ID == "seu_client_id_aqui":
        print("[AVISO] Credenciais do Azure AD não configuradas. Utilizando Mock API.")
        return "mock_token"
        
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_silent(SCOPES, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=SCOPES)
    
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Erro ao obter token: {result.get('error')} - {result.get('error_description')}")

def get_business_basic_sku(access_token):
    """Busca o SKU ID da licença Microsoft 365 Business Basic."""
    if access_token == "mock_token":
        return "mock_sku_id"
        
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://graph.microsoft.com/v1.0/subscribedSkus", headers=headers)
    response.raise_for_status()
    skus = response.json().get("value", [])
    
    # O skuPartNumber para Business Basic geralmente é O365_BUSINESS_ESSENTIALS ou SPB.
    for sku in skus:
        if sku.get("skuPartNumber") in ["O365_BUSINESS_ESSENTIALS", "SPB", "M365_BUSINESS_BASIC"]:
            return sku.get("skuId")
    
    raise Exception("Licença Microsoft 365 Business Basic não encontrada no tenant.")

def create_user(access_token, display_name, first_name, last_name, email, password):
    """Cria o usuário no Microsoft 365."""
    if access_token == "mock_token":
        print(f"      [MOCK] Chamada de API para criar usuário '{email}'.")
        return "mock_user_id"
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    user_data = {
        "accountEnabled": True,
        "displayName": display_name,
        "mailNickname": email.split('@')[0],
        "userPrincipalName": email,
        "givenName": first_name,
        "surname": last_name,
        "usageLocation": "BR",
        "passwordProfile": {
            "forceChangePasswordNextSignIn": False,
            "password": password
        }
    }
    
    response = requests.post("https://graph.microsoft.com/v1.0/users", headers=headers, json=user_data)
    if response.status_code == 201:
        return response.json().get("id")
    else:
        raise Exception(f"Erro ao criar usuário: {response.text}")

def assign_license(access_token, user_id, sku_id):
    """Atribui a licença ao usuário criado."""
    if access_token == "mock_token":
        print(f"      [MOCK] Chamada de API para atribuir licença '{sku_id}' ao usuário '{user_id}'.")
        return True
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    license_data = {
        "addLicenses": [
            {
                "skuId": sku_id
            }
        ],
        "removeLicenses": []
    }
    
    response = requests.post(f"https://graph.microsoft.com/v1.0/users/{user_id}/assignLicense", headers=headers, json=license_data)
    if response.status_code == 200:
        return True
    else:
        raise Exception(f"Erro ao atribuir licença: {response.text}")

def save_to_excel_sp(access_token, admissao, matricula, filial, nome, vpn_user, ms365_email, ms365_pass):
    """Salva os dados gerados na planilha SharePoint via Graph API."""
    site_id = os.getenv("SP_SITE_ID")
    drive_id = os.getenv("SP_DRIVE_ID")
    item_id = os.getenv("SP_ITEM_ID")
    sheet_name = os.getenv("SP_SHEET_NAME", "todos")

    if not all([site_id, drive_id, item_id]):
        print("      [!] Falta configuração de variáveis SP no .env.")
        return False

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        # 1. Obter o usedRange para descobrir a próxima linha vazia
        used_range_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{item_id}/workbook/worksheets/{sheet_name}/usedRange"
        res = requests.get(used_range_url, headers=headers)
        if res.status_code != 200:
            print(f"      [!] Erro ao buscar usedRange: {res.text}")
            return False
        
        data = res.json()
        values = data.get("values", [])
        
        # O range real que a API devolve (ex: 'todos!A1:AM105'). Vamos assumir que começa na linha 1 pela estrutura comum.
        # Procurar a primeira linha inteiramente vazia
        next_row_index = len(values) + 1 # default se todas estiverem cheias
        
        for i, row in enumerate(values):
            if i == 0: continue # pular cabeçalho
            is_empty = True
            for cell in row:
                if cell is not None and str(cell).strip() != "":
                    is_empty = False
                    break
            if is_empty:
                next_row_index = i + 1 # 1-based index
                break

        # Formatar Data de Admissão
        if admissao and len(admissao) == 8 and admissao.isdigit():
            admissao_fmt = f"{admissao[6:8]}/{admissao[4:6]}/{admissao[0:4]}"
        else:
            admissao_fmt = admissao
            
        # O array de atualização precisa corresponder da coluna A até M (13 colunas)
        # A=0, C=2, D=3, E=4, H=7, I=8, L=11, M=12
        row_values = [
            admissao_fmt, # A
            "",           # B
            matricula,    # C
            filial,       # D
            nome.title(), # E
            "",           # F
            "",           # G
            vpn_user,     # H
            "",           # I (Senha VPN)
            "",           # J
            "",           # K
            ms365_email,  # L
            ms365_pass    # M
        ]
        
        update_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{item_id}/workbook/worksheets/{sheet_name}/range(address='A{next_row_index}:M{next_row_index}')"
        patch_payload = {
            "values": [row_values]
        }
        
        patch_res = requests.patch(update_url, headers=headers, json=patch_payload)
        if patch_res.status_code == 200:
            return True
        else:
            print(f"      [!] Erro ao atualizar linha {next_row_index}: {patch_res.text}")
            return False
            
    except Exception as e:
        print(f"      [!] Erro ao comunicar com SP: {e}")
        return False

def main():
    print("===========================================")
    print(" Automação de Registro Microsoft 365 ")
    print("===========================================\n")
    
    matricula = input("Matrícula do Colaborador no Protheus: ").strip()
    filial_protheus = input("Filial no Protheus (ex: 01, 02...): ").strip()
    
    print("\nConsultando Banco de Dados...")
    try:
        db = database.DataBase()
        emp_data = db.get_employee_data(matricula, filial_protheus)
        db.close()
    except Exception as e:
        print(f"Erro ao conectar ou consultar o banco: {e}")
        return
        
    if not emp_data:
        print(f"❌ Não foi possível encontrar a Matrícula '{matricula}' na Filial '{filial_protheus}' no banco de dados Protheus.")
        return
        
    full_name = emp_data['nome']
    print(f"✅ Colaborador encontrado: {full_name} (Admissão: {emp_data['admissao']})")
    
    cargo = input("\nQual o Cargo? ")
    
    # Filial
    filial = input("Qual o número da filial?\n1-Matriz/SP\n2-Cuiabá/MT\n3-Uberlândia/MG\n4-Limeira/SP\n5-Campo Grande/MS\n6-Araçatuba/SP\n7-Londrina/PR\n8-Ribeirão Preto/SP\n9-Personalizado\n").strip()
    local = None
    telefone_filial = None
    email_manual = None
    if filial == '9':
        local = input("Qual local da filial? (Ex: São Paulo/SP) ").strip()
        telefone_filial = input("Qual telefone da filial? (Pressione ENTER para pular) ").strip()
        email_manual = input("Qual e-mail? (Pressione ENTER para usar email padrão) ").strip()
        
    telefone = input("Qual TELEFONE do colaborador? (Pressione ENTER para pular) ").strip()
    ramal = input("Qual RAMAL? (Pressione ENTER para pular) ").strip()
    
    try:
        # 1. Extração e Sanitização
        first_raw, last_raw, first_clean, last_clean = sanitize_and_extract_names(full_name)
        
        default_username = f"{first_clean}.{last_clean}"
        print(f"\nSugestão de usuário: {default_username}")
        custom_user = input("Aperte ENTER para aceitar a sugestão ou digite um usuário personalizado (ex: joao.psilva): ").strip()
        
        if custom_user:
            # Sanitiza o que o usuário digitou caso tenha colocado acento ou letras maiúsculas
            username = re.sub(r'[^a-z0-9\.]', '', remove_accents(custom_user).lower())
        else:
            username = default_username
            
        email = f"{username}@ativalocacao.com.br"
        password = generate_password()
        display_name = f"{first_raw} {last_raw} - Ativa Locação"
        
        print("\n[1/4] Extração e Sanitização concluídas...")
        print(f"      Usuário: {username}")
        print(f"      E-mail:  {email}")
        print(f"      Nome de Exibição: {display_name}")
        
        # 2. Autenticação na API
        print("\n[2/4] Autenticando na Microsoft Graph API...")
        token = get_access_token()
        
        # 3. Criação de Usuário
        print("\n[3/4] Criando usuário e definindo senha...")
        user_id = create_user(token, display_name, first_raw, last_raw, email, password)
        
        # 4. Atribuição de Licença
        print("\n[4/4] Atribuindo licença Microsoft 365 Business Basic...")
        sku_id = get_business_basic_sku(token)
        assign_license(token, user_id, sku_id)
        
        usuario_vpn = f"atv.{username}"
        
        # Output Final
        print("\n" + "="*45)
        print("✅ Criação Concluída com Sucesso!")
        print("="*45)
        print(f"> E-mail: {email}")
        print(f"> Senha: {password}")
        print(f"> Usuário VPN: {usuario_vpn}")
        print("="*45)
        
        # 5. Gerar Assinatura
        print("\nGerando imagem da assinatura...")
        
        # Formata o nome para a assinatura (Apenas Primeiro e Último nome, com iniciais maiúsculas)
        nome_assinatura = f"{first_raw} {last_raw}"
        
        image_path = assinatura.criar_assinatura(
            nome_param=nome_assinatura,
            cargo_param=cargo,
            filial_param=filial,
            local_param=local,
            telefone_filial_param=telefone_filial,
            email_manual_param=email_manual,
            telefone_param=telefone,
            ramal_param=ramal,
            email_param=email
        )
        
        if image_path and os.path.exists(image_path):
            print(f"      [!] Assinatura PNG gerada com sucesso em: {image_path}")
            print(f"      [!] Nota: A Microsoft Graph API não suporta a injeção automática de assinatura no Outlook.")
            print(f"      [!] A imagem está pronta para ser enviada/configurada no Outlook do usuário.")
        else:
            print("⚠️ Falha ao gerar a imagem da assinatura.")
        
        # 6. Preencher Planilha (SharePoint)
        print("\nSalvando dados na planilha do SharePoint...")
        sucesso_planilha = save_to_excel_sp(
            access_token=token,
            admissao=emp_data.get('admissao', ''),
            matricula=matricula,
            filial=filial_protheus,
            nome=full_name,
            vpn_user=usuario_vpn,
            ms365_email=email,
            ms365_pass=password
        )
        if sucesso_planilha:
            print(f"      [!] Dados salvos com sucesso na planilha SharePoint.")
            
    except Exception as e:
        print(f"\n❌ Ocorreu um erro durante o processo: {e}")

if __name__ == "__main__":
    main()

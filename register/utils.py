import unicodedata
import re
import random
import string
import requests
import os
import sys
import msal
from dotenv import load_dotenv

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
    clean_name = " ".join(full_name.strip().split())
    parts = clean_name.split(" ")
    if len(parts) < 2:
        # Se só tiver um nome, repete o primeiro para o last name (fallback)
        parts.append(parts[0])
    
    first_name_raw = parts[0].title()
    last_name_raw = parts[-1].title()
    
    first_name_clean = re.sub(r'[^a-z0-9]', '', remove_accents(first_name_raw).lower())
    last_name_clean = re.sub(r'[^a-z0-9]', '', remove_accents(last_name_raw).lower())
    
    return first_name_raw, last_name_raw, first_name_clean, last_name_clean

def generate_password(length=12):
    """Gera uma senha forte temporária."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
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
    
    for sku in skus:
        if sku.get("skuPartNumber") in ["O365_BUSINESS_ESSENTIALS", "SPB", "M365_BUSINESS_BASIC"]:
            return sku.get("skuId")
    
    raise Exception("Licença Microsoft 365 Business Basic não encontrada no tenant.")

def create_user(access_token, display_name, first_name, last_name, email, password):
    """Cria o usuário no Microsoft 365."""
    if access_token == "mock_token":
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
        return True
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    license_data = {
        "addLicenses": [{"skuId": sku_id}],
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
        return False, "Falta configuração de variáveis SP no .env."

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        used_range_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{item_id}/workbook/worksheets/{sheet_name}/usedRange"
        res = requests.get(used_range_url, headers=headers)
        if res.status_code != 200:
            return False, f"Erro ao buscar usedRange: {res.text}"
        
        data = res.json()
        values = data.get("values", [])
        
        next_row_index = len(values) + 1
        
        for i, row in enumerate(values):
            if i == 0: continue
            is_empty = True
            for cell in row:
                if cell is not None and str(cell).strip() != "":
                    is_empty = False
                    break
            if is_empty:
                next_row_index = i + 1
                break

        if admissao and len(admissao) == 8 and admissao.isdigit():
            admissao_fmt = f"{admissao[6:8]}/{admissao[4:6]}/{admissao[0:4]}"
        else:
            admissao_fmt = admissao
            
        row_values = [
            admissao_fmt, "", matricula, filial, nome.title(), "", "",
            vpn_user, "", "", "", ms365_email, ms365_pass
        ]
        
        update_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{item_id}/workbook/worksheets/{sheet_name}/range(address='A{next_row_index}:M{next_row_index}')"
        patch_payload = {"values": [row_values]}
        
        patch_res = requests.patch(update_url, headers=headers, json=patch_payload)
        if patch_res.status_code == 200:
            return True, "Sucesso"
        else:
            return False, f"Erro ao atualizar linha {next_row_index}: {patch_res.text}"
            
    except Exception as e:
        return False, f"Erro ao comunicar com SP: {e}"

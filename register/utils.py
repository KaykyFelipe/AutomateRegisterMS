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

def get_user_info(access_token, user_email):
    """Busca as informações do usuário no Graph API."""
    if access_token == "mock_token":
        return {"displayName": "Mock User"}
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(f"https://graph.microsoft.com/v1.0/users/{user_email}", headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        raise Exception(f"Erro ao buscar info do usuário {user_email}: {res.text}")

def get_or_create_folder(access_token, user_email, folder_name, parent_id="root"):
    """Retorna o ID da pasta. Cria se não existir."""
    if access_token == "mock_token":
        return "mock_folder_id"
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 1. Tentar obter a pasta existente
    if parent_id == "root":
        path_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{folder_name}"
    else:
        path_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/items/{parent_id}:/{folder_name}"
        
    res = requests.get(path_url, headers=headers)
    if res.status_code == 200:
        return res.json().get("id")
        
    # 2. Se não existir (404), criar a pasta
    if parent_id == "root":
        create_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root/children"
    else:
        create_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/items/{parent_id}/children"
        
    payload = {
        "name": folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "rename"
    }
    res_create = requests.post(create_url, headers=headers, json=payload)
    if res_create.status_code in [200, 201]:
        return res_create.json().get("id")
    else:
        raise Exception(f"Erro ao criar pasta {folder_name} para {user_email}: {res_create.text}")

def copy_onedrive_items(access_token, source_email, dest_email):
    """Copia todos os itens da raiz do source_email para uma pasta de backup no dest_email."""
    if access_token == "mock_token":
        return True, "Mock: Cópia iniciada com sucesso."

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        # 1. Pega informações do usuário de origem para nomear a pasta
        source_info = get_user_info(access_token, source_email)
        display_name = source_info.get("displayName", source_email.split("@")[0])
        safe_name = "".join([c if c.isalnum() or c in " .-_" else "_" for c in display_name]).strip()
        
        # 2. Obter o driveId do destino
        dest_drive_res = requests.get(f"https://graph.microsoft.com/v1.0/users/{dest_email}/drive", headers=headers)
        if dest_drive_res.status_code != 200:
            return False, f"Erro ao buscar Drive do destino: {dest_drive_res.text}"
        dest_drive_id = dest_drive_res.json().get("id")

        # 3. Criar a pasta 'Backups' na raiz do destino
        backups_folder_id = get_or_create_folder(access_token, dest_email, "Backups", parent_id="root")

        # 4. Criar a pasta do usuário desligado dentro de 'Backups'
        user_backup_folder_id = get_or_create_folder(access_token, dest_email, safe_name, parent_id=backups_folder_id)

        # 5. Listar arquivos e pastas na raiz do usuário de origem
        source_items_url = f"https://graph.microsoft.com/v1.0/users/{source_email}/drive/root/children"
        res_items = requests.get(source_items_url, headers=headers)
        if res_items.status_code != 200:
            return False, f"Erro ao listar itens da origem: {res_items.text}"
            
        items = res_items.json().get("value", [])
        if not items:
            return True, "O OneDrive de origem está vazio. Nenhuma cópia necessária."
            
        # 6. Para cada item, enviar comando de copy
        monitor_urls = []
        for item in items:
            item_id = item.get("id")
            copy_url = f"https://graph.microsoft.com/v1.0/users/{source_email}/drive/items/{item_id}/copy"
            copy_payload = {
                "parentReference": {
                    "driveId": dest_drive_id,
                    "id": user_backup_folder_id
                }
            }
            res_copy = requests.post(copy_url, headers=headers, json=copy_payload)
            if res_copy.status_code in [200, 201, 202]:
                loc = res_copy.headers.get("Location")
                if loc:
                    monitor_urls.append(loc)

        return True, f"Comandos de cópia enviados com sucesso para a pasta Backups/{safe_name}.", monitor_urls

    except Exception as e:
        return False, str(e), []

def check_backup_status(access_token, monitor_urls):
    """Consulta o status atual das URLs de monitoramento de cópia."""
    if not monitor_urls:
        return 100.0

    if access_token == "mock_token":
        return 100.0

    headers = {"Authorization": f"Bearer {access_token}"}
    total_percentage = 0.0

    for url in monitor_urls:
        try:
            # allow_redirects=False é crucial: se concluir, a API retorna 303 See Other
            res = requests.get(url, headers=headers, allow_redirects=False)
            print(f"Monitor URL GET: {url}")
            print(f"Status Code: {res.status_code}")
            
            if res.status_code == 200:
                data = res.json()
                print(f"Data 200: {data}")
                pct = data.get("percentageComplete", 0)
                status = data.get("status", "inProgress")
                if status == "completed":
                    pct = 100.0
                total_percentage += pct
            elif res.status_code in [303, 201]:
                # 303 See Other significa que terminou com sucesso e redireciona pro novo item
                total_percentage += 100.0
            else:
                print(f"Erro/Status inesperado: {res.status_code} - {res.text}")
                # Se deu erro temporário (ex: 401, 500) não assumimos 100%, 
                # vamos somar 0% ou logar. Se falhar sempre, pode travar, 
                # então podemos checar se foi 404 (expirou/não achou).
                if res.status_code == 404:
                    total_percentage += 100.0
                else:
                    # Em outros erros (como 401), não sabemos o status. 
                    # Assumimos 0% para não finalizar antes da hora.
                    total_percentage += 0.0
        except Exception as e:
            # Erro de conexão, etc. Assume 0% para não encerrar prematuramente
            total_percentage += 0.0

    avg_percentage = total_percentage / len(monitor_urls)
    return avg_percentage

def remove_all_licenses(access_token, user_email):
    """Remove todas as licenças Microsoft 365 de um usuário."""
    if access_token == "mock_token":
        return True, "Mock: Licenças removidas com sucesso."
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 1. Obter quais licenças estão atribuídas
        res = requests.get(f"https://graph.microsoft.com/v1.0/users/{user_email}/licenseDetails", headers=headers)
        if res.status_code != 200:
            return False, f"Erro ao buscar licenças: {res.text}"
            
        license_details = res.json().get("value", [])
        if not license_details:
            return True, "O usuário já não possui nenhuma licença."
            
        skus_to_remove = [item.get("skuId") for item in license_details]
        
        # 2. Remover licenças
        license_data = {
            "addLicenses": [],
            "removeLicenses": skus_to_remove
        }
        
        res_remove = requests.post(f"https://graph.microsoft.com/v1.0/users/{user_email}/assignLicense", headers=headers, json=license_data)
        if res_remove.status_code == 200:
            return True, "Licença removida com sucesso."
        else:
            return False, f"Erro ao remover licença: {res_remove.text}"
            
    except Exception as e:
        return False, str(e)

import re

def sanitize_filename(name):
    """Remove caracteres inválidos para nomes de arquivos no Windows/OneDrive."""
    if not name:
        return "Sem_Assunto"
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def backup_outlook_to_onedrive(access_token, source_email, dest_email):
    """Faz o download dos emails e sobe como .eml na pasta Backups/Nome/Outlook do OneDrive."""
    if access_token == "mock_token":
        return True, "Mock: Backup do Outlook concluído (0 emails)."
        
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # 1. Obter ou criar pastas no destino
        safe_name = source_email.split('@')[0]
        backup_folder_id = get_or_create_folder(access_token, dest_email, "Backups")
        if not backup_folder_id:
            return False, "Erro ao acessar/criar pasta Backups."
            
        user_backup_folder_id = get_or_create_folder(access_token, dest_email, safe_name, parent_id=backup_folder_id)
        outlook_folder_id = get_or_create_folder(access_token, dest_email, "Outlook_Backup", parent_id=user_backup_folder_id)
        
        # Obter driveId do destino
        res_dest_drive = requests.get(f"https://graph.microsoft.com/v1.0/users/{dest_email}/drive", headers=headers)
        if res_dest_drive.status_code != 200:
            return False, "Erro ao acessar OneDrive destino."
        dest_drive_id = res_dest_drive.json().get("id")

        # 2. Loop pelas mensagens (paginado)
        # top=50 para um compromisso de velocidade e estabilidade
        url_messages = f"https://graph.microsoft.com/v1.0/users/{source_email}/messages?$select=id,subject&$top=50"
        messages_copied = 0
        
        while url_messages and messages_copied < 30000: # Limite de segurança bastante alto (20.000 emails)
            res_msgs = requests.get(url_messages, headers=headers)
            if res_msgs.status_code != 200:
                if messages_copied == 0:
                    return False, f"Falha ao ler emails. Erro Graph ({res_msgs.status_code}): {res_msgs.text}"
                break
                
            data_msgs = res_msgs.json()
            messages = data_msgs.get("value", [])
            
            for msg in messages:
                msg_id = msg.get("id")
                subject = sanitize_filename(msg.get("subject", "Email"))
                
                # Baixa o conteúdo MIME
                res_eml = requests.get(f"https://graph.microsoft.com/v1.0/users/{source_email}/messages/{msg_id}/$value", headers=headers)
                if res_eml.status_code == 200:
                    eml_content = res_eml.content
                    
                    # Upload para o OneDrive (Direct upload < 4MB)
                    # Caso exceda, falhará esse email especifico por enquanto
                    upload_url = f"https://graph.microsoft.com/v1.0/drives/{dest_drive_id}/items/{outlook_folder_id}:/{subject}_{msg_id[-5:]}.eml:/content"
                    headers_upload = headers.copy()
                    headers_upload["Content-Type"] = "message/rfc822"
                    
                    res_up = requests.put(upload_url, headers=headers_upload, data=eml_content)
                    if res_up.status_code in [200, 201]:
                        messages_copied += 1
                        
            url_messages = data_msgs.get("@odata.nextLink")
            
        return True, f"Backup Outlook finalizado. {messages_copied} e-mails baixados em .eml."
        
    except Exception as e:
        return False, f"Erro Outlook: {str(e)}"

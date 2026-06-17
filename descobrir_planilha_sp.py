import requests
from main import get_access_token
import json

def buscar_ids():
    token = get_access_token()
    if token == "mock_token":
        print("Erro: Utilizando mock token.")
        return
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    # 1. Buscar o Site ID
    print("\n1. Buscando Site ID...")
    site_url = "https://graph.microsoft.com/v1.0/sites/ativalocacao.sharepoint.com:/sites/TI-AtivaLocao-Usurios"
    response = requests.get(site_url, headers=headers)
    if response.status_code == 200:
        site_id = response.json().get('id')
        print(f"Site ID: {site_id}")
    else:
        print(f"Erro ao buscar Site: {response.status_code} - {response.text}")
        return

    # 2. Buscar o arquivo (Pesquisa no Site inteiro)
    print("\n2. Buscando o arquivo 'Usuários'...")
    search_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root/search(q='Usuários')"
    response = requests.get(search_url, headers=headers)
    
    if response.status_code == 200:
        items = response.json().get('value', [])
        found = False
        for item in items:
            if 'xls' in item.get('name', '').lower():
                print("\n=== ARQUIVO ENCONTRADO ===")
                print(f"Nome do Arquivo: {item.get('name')}")
                print(f"Drive ID: {item.get('parentReference', {}).get('driveId')}")
                print(f"Item ID: {item.get('id')}")
                print("==========================")
                found = True
                
                # Fetch worksheets
                print("\n3. Buscando Abas (Worksheets)...")
                ws_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{item.get('parentReference', {}).get('driveId')}/items/{item.get('id')}/workbook/worksheets"
                ws_response = requests.get(ws_url, headers=headers)
                if ws_response.status_code == 200:
                    for ws in ws_response.json().get('value', []):
                        print(f"Aba encontrada: {ws.get('name')}")
                else:
                    print(f"Erro ao buscar abas: {ws_response.text}")
        
        if not found:
            print("Nenhum arquivo Excel encontrado na busca por 'Usuários'.")
    else:
        print(f"Erro ao buscar arquivo: {response.status_code} - {response.text}")

if __name__ == "__main__":
    buscar_ids()

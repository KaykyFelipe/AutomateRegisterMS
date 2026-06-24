import os
import sys
import json
import re
import shutil
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Adiciona a raiz ao path para importar database e assinatura
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import database
from AssinAtiva import assinatura
from . import utils

def index(request):
    return render(request, 'register/index.html')

@csrf_exempt
def check_employee(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            matricula = data.get('matricula')
            filial = data.get('filial')
            
            if not matricula or not filial:
                return JsonResponse({'error': 'Matrícula e Filial são obrigatórios.'}, status=400)
                
            db = database.DataBase()
            emp_data = db.get_employee_data(matricula, filial)
            
            if emp_data:
                # Sanitiza e sugere nome
                full_name = emp_data['nome']
                _, _, first_clean, last_clean = utils.sanitize_and_extract_names(full_name)
                suggested_user = f"{first_clean}.{last_clean}"
                
                return JsonResponse({
                    'success': True,
                    'nome': full_name,
                    'admissao': emp_data['admissao'],
                    'suggested_user': suggested_user
                })
            else:
                return JsonResponse({'success': False, 'message': 'Colaborador não encontrado.'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)

@csrf_exempt
def create_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            matricula = data.get('matricula')
            filial_protheus = data.get('filial_protheus')
            full_name = data.get('full_name')
            admissao = data.get('admissao')
            
            cargo = data.get('cargo', '')
            local = data.get('local', '')
            telefone = data.get('telefone', '')
            ramal = data.get('ramal', '')
            custom_user = data.get('username', '')
            
            if not matricula or not full_name:
                return JsonResponse({'error': 'Dados incompletos.'}, status=400)
            
            first_raw, last_raw, first_clean, last_clean = utils.sanitize_and_extract_names(full_name)
            
            if custom_user:
                username = re.sub(r'[^a-z0-9\.]', '', utils.remove_accents(custom_user).lower())
            else:
                username = f"{first_clean}.{last_clean}"
                
            email = f"{username}@ativalocacao.com.br"
            password = utils.generate_password()
            display_name = f"{first_raw} {last_raw} - Ativa Locação"
            
            # Autentica e cria no Microsoft 365
            token = utils.get_access_token()
            user_id = utils.create_user(token, display_name, first_raw, last_raw, email, password)
            sku_id = utils.get_business_basic_sku(token)
            utils.assign_license(token, user_id, sku_id)
            
            assinaturas_dir = os.path.join(BASE_DIR, 'register', 'static', 'signatures')
            os.makedirs(assinaturas_dir, exist_ok=True)
            
            signature_name = f"{first_raw} {last_raw}"
            generated_path = assinatura.criar_assinatura(
                nome_param=signature_name,
                cargo_param=cargo,
                filial_param='9',
                local_param=local,
                telefone_filial_param='',
                email_manual_param='',
                telefone_param=telefone,
                ramal_param=ramal,
                email_param=email
            )
            
            image_name = f"assinatura_{matricula}.png"
            final_image_path = os.path.join(assinaturas_dir, image_name)
            if os.path.exists(generated_path):
                shutil.copy(generated_path, final_image_path)
            
            # Salva na Planilha
            usuario_vpn = f"atv.{username}"
            success_sp, msg_sp = utils.save_to_excel_sp(
                token, admissao, matricula, filial_protheus, full_name, usuario_vpn, email, password
            )
            
            image_url = f"/static/signatures/{image_name}"
            
            return JsonResponse({
                'success': True,
                'email': email,
                'password': password,
                'vpn_user': usuario_vpn,
                'signature_url': image_url,
                'sp_status': msg_sp
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)

@csrf_exempt
def backup_onedrive(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            source_email = data.get('source_email')
            dest_email = data.get('dest_email')
            
            if not source_email or not dest_email:
                return JsonResponse({'error': 'E-mail de origem e destino são obrigatórios.'}, status=400)
                
            token = utils.get_access_token()
            success, message, monitor_urls = utils.copy_onedrive_items(token, source_email, dest_email)
            
            if success:
                return JsonResponse({'success': True, 'message': message, 'monitor_urls': monitor_urls})
            else:
                return JsonResponse({'success': False, 'message': message}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)

@csrf_exempt
def check_backup_progress(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            monitor_urls = data.get('monitor_urls', [])
            
            token = utils.get_access_token()
            percentage = utils.check_backup_status(token, monitor_urls)
            return JsonResponse({'success': True, 'percentage': percentage})
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)

@csrf_exempt
def remove_license(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            source_email = data.get('source_email')
            
            if not source_email:
                return JsonResponse({'error': 'E-mail é obrigatório.'}, status=400)
                
            token = utils.get_access_token()
            success, message = utils.remove_all_licenses(token, source_email)
            
            if success:
                return JsonResponse({'success': True, 'message': message})
            else:
                return JsonResponse({'success': False, 'message': message}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)

@csrf_exempt
def backup_outlook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            source_email = data.get('source_email')
            dest_email = data.get('dest_email')
            
            if not source_email or not dest_email:
                return JsonResponse({'error': 'E-mail de origem e destino são obrigatórios.'}, status=400)
                
            token = utils.get_access_token()
            success, message = utils.backup_outlook_to_onedrive(token, source_email, dest_email)
            
            if success:
                return JsonResponse({'success': True, 'message': message})
            else:
                return JsonResponse({'success': False, 'message': message}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)

@csrf_exempt
def generate_signature(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            full_name = data.get('full_name')
            cargo = data.get('cargo', '')
            filial = data.get('filial', '9')
            local = data.get('local', '')
            telefone = data.get('telefone', '')
            ramal = data.get('ramal', '')
            email_manual = data.get('email_manual', '')
            
            if not full_name:
                return JsonResponse({'error': 'Nome é obrigatório.'}, status=400)
                
            first_raw, last_raw, _, _ = utils.sanitize_and_extract_names(full_name)
            signature_name = f"{first_raw} {last_raw}"
            
            assinaturas_dir = os.path.join(BASE_DIR, 'register', 'static', 'signatures')
            os.makedirs(assinaturas_dir, exist_ok=True)
            
            generated_path = assinatura.criar_assinatura(
                nome_param=signature_name,
                cargo_param=cargo,
                filial_param=filial,
                local_param=local,
                telefone_filial_param='',
                email_manual_param=email_manual,
                telefone_param=telefone,
                ramal_param=ramal,
                email_param=None
            )
            
            # Formatar nome do arquivo com timestamp para não conflitar
            import time
            timestamp = int(time.time())
            image_name = f"assinatura_avulsa_{first_raw.lower()}_{timestamp}.png"
            final_image_path = os.path.join(assinaturas_dir, image_name)
            
            if os.path.exists(generated_path):
                import shutil
                shutil.copy(generated_path, final_image_path)
            else:
                return JsonResponse({'error': 'Falha ao gerar a imagem da assinatura.'}, status=500)
            
            image_url = f"/static/signatures/{image_name}"
            
            return JsonResponse({
                'success': True,
                'signature_url': image_url
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método não permitido.'}, status=405)

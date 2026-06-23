from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/check_employee', views.check_employee, name='check_employee'),
    path('api/create_user', views.create_user, name='create_user'),
    path('api/backup_onedrive', views.backup_onedrive, name='backup_onedrive'),
    path('api/backup_status', views.check_backup_progress, name='backup_status'),
    path('api/backup_outlook', views.backup_outlook, name='backup_outlook'),
    path('api/remove_license', views.remove_license, name='remove_license'),
    path('api/generate_signature', views.generate_signature, name='generate_signature'),
]

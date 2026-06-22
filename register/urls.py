from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/check_employee', views.check_employee, name='check_employee'),
    path('api/create_user', views.create_user, name='create_user'),
]

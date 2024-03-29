from django.urls import path
from . import views

#Rutas de la aplicación "Usuarios"
urlpatterns = [
    path('registroUsuario/', views.registroUsuarios) #Vista RegistroUsuario
]
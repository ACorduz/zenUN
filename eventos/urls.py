from django.urls import path
from . import views

#Rutas de la aplicación "Usuarios"
urlpatterns = [
    path('generarInformes/',
         views.mostra_vista_informes,
         name='generarInformes')
]
from django.urls import path
from . import views

#Rutas de la aplicación "Usuarios"
urlpatterns = [
    path('registroEstudiante/', views.mostrar_registro_estudiante, name='registroEstudiante'), #Vista RegistroEstudiante
    path('procesarRegistroEstudiante/', views.procesar_registro_estudiante, name='procesar_registro_estudiante'), #Ruta para el formulario
    path('login/',views.mostrar_login_usuario,name='loginUsuario')
]
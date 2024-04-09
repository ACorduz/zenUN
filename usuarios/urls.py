from django.urls import path
from . import views

#Rutas de la aplicación "Usuarios"
urlpatterns = [
    path('registroEstudiante/', 
            views.mostrar_registro_estudiante, 
            name='registroEstudiante'), #Vista RegistroEstudiante
    path('procesarRegistroEstudiante/', 
            views.procesar_registro_estudiante, 
            name='procesar_registro_estudiante'), #Ruta para el formulario de RegistroEstudiante
    path('login/',
            views.mostrar_login_usuario,
            name='loginUsuario'), # Vista Login
    path('autenticarCredenciales/',
            views.autenticar_credenciales_usuario, 
            name='autenticar_credenciales_usuario'), #Ruta para el formulario Login
    path('paginaPrincipalEstudiante/', 
            views.mostrar_mainPage_estudiante, 
            name='paginaPrincipal_estudiante'),  #vista Principal estudiante
    path('login/EnvioRecuperacionContraseña', 
            views.mostrar_enviarCorreo_contrasena, 
            name="enviarCorreo_contrasena"), # Vista para el envio del correo de RecuperarContraseña
    path('login/procesarEnvioCorreoRecuperarContraseña/',
            views.procesar_enviarCorreo_contrasena, 
            name='procesar_enviarCorreo_contrasena'),#Ruta para el formulario de enviar correo
    path('resetPassword/<str:token>/', 
            views.mostrar_ResetPasswordPage, 
            name="cambiar_contrasena"),  # Vista Reset Password
    path('cambiarContraseña/<str:correo_usuario>/<str:token>/procesarCambioContraseña/', 
            views.procesar_cambio_contrasena, 
            name="procesar_cambio_contrasena"), #Ruta para el formulario reset Password
    path('verificacionCorreo/<str:token>/',
          views.mostrar_otp,
          name="mostrar_otp"), #Ruta para el formulario de verificación del correo por OTP
    path('verificacionCorreo/aprobar/<str:token>/',
         views.aprobar_OTP,
         name="aprobar_OTP"), #Ruta para la vista de aprobación del OTP
]
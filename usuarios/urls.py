from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

#Rutas de la aplicación "Usuarios"
urlpatterns = [
    path('registroEstudiante/', 
            views.mostrar_registro_estudiante, 
            name='registroEstudiante'), #Vista RegistroEstudiante
    path('procesarRegistroEstudiante/', 
            views.procesar_registro_estudiante, 
            name='procesar_registro_estudiante'), #Ruta para el formulario de RegistroEstudiante
    path('',
            views.mostrar_login_usuario,
            name='loginUsuario'), # Vista Login
    path('autenticarCredenciales/',
            views.autenticar_credenciales_usuario, 
            name='autenticar_credenciales_usuario'), #Ruta para el formulario Login
    path('paginaPrincipalEstudiante/', 
            login_required(views.mostrar_mainPage_estudiante), 
            name='paginaPrincipal_estudiante'), #vista Principal estudiante
    path('cerrar-sesion/', 
            views.cerrar_sesion, 
            name='cerrar_sesion'), #Cerrar Sesión
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
          name="mostrar_otp"), #Ruta para mostrar el formulario de verificación del correo por OTP
    path('verificacionCorreo/aprobar/<str:token>',
         views.aprobar_OTP,
         name="aprobar_OTP"), #Ruta para la vista de aprobación del OTP
    path('verificacionCorreoAdminBienestar/',
         views.mostrar_vistaVerificarCorreoAdminBienestar,
         name="verificacionCorreoAdminBienestar"),
    path('verificacionCorreoAdminBienestar/procesar',
         views.procesar_verificar_correo_Admin_Bienestar,
         name='procesarVerificacionCorreoAdminBienestar'),
    path('registroAdministradorBienestar/',
         views.mostrar_registro_administrativo,
         name='registroAdministradorBienestar'),
    path('registroAdministradorBienestar/procesar',
         views.procesar_registro_administrador_bienestar,
         name="procesarRegistroAdministradorBienestar"),
    path('procesarAsignacionRol',
         views.procesar_asignacion_rol_administrador_bienestar,
         name="procesarAsignacionRolAdminBienestar")
]
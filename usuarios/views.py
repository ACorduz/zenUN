from django.shortcuts import render, redirect
from functools import wraps
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import login, logout
from usuarios.models import usuario
from usuarios.models import tipoDocumento
from usuarios.models import razonCambio
from django.urls import reverse
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.core.signing import Signer, BadSignature
from datetime import datetime
from django.utils import timezone
import time
import random


########################################Funcionalidad acceso según el ROL#########################
def role_required(role_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Verificar si el usuario tiene el rol necesario
            if request.user.is_authenticated and request.user.roles.filter(nombreRol=role_name).exists():
                return view_func(request, *args, **kwargs)
            else:
                # Si el usuario no tiene el rol necesario, redirigir a una página de acceso denegado
                return redirect(reverse('accesoDenegado'))  # Puedes definir una URL para una página de acceso denegado
        return _wrapped_view
    return decorator

def access_denied(request):
    return render(request, 'accesoDenegado.html')


#################Funcionalidad de Registro Estudiantes################

#Este método solo se encarga de mostrar la vista de registro
def mostrar_registro_estudiante(request):
    tipos_documentos = tipoDocumento.objects.all()
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'RegisterPage.html', {'tipos_documentos' : tipos_documentos, 'mensaje': mensaje})

#Este método se encarga de procesar el formulario de registro cuando se envía
def procesar_registro_estudiante(request):
    try:
        if request.method == "POST":
            #Obtener los datos del formulario
            nombres = request.POST.get('fullName')
            apellidos = request.POST.get('lastName')
            email_usuario = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirmPassword')
            tipo_documento = int(request.POST.get('documentType'))
            phone = request.POST.get('phone')
            numero_documento = request.POST.get('documentNumber')
            
            if not email_usuario.endswith('@unal.edu.co'):
                mensaje = "El correo debe ser de dominio @unal.edu.co"
            elif password != confirm_password:
                mensaje = "Las contraseñas no coinciden"
            elif usuario.objects.filter(correoInstitucional = email_usuario).exists():
                mensaje = "El correo ya se encuentra registrado"
            elif usuario.objects.filter(numeroDocumento = numero_documento).exists():
                mensaje = "El número de documento ya se encuentra registrado"
            else:
            #Lógica de creación de usuario si todas las validaciones son exitosas
                #Tipo de documento
                tipo_doc = tipoDocumento.objects.get(pk=tipo_documento)

                #Primero, generar el hash de la contraseña
                password_hash = make_password(password)

                #Luego, crear el objeto usuario utilizando el hash de la contraseña
                estudiante = usuario(
                        numeroDocumento = numero_documento,
                        idTipoDocumento = tipo_doc,
                        nombres = nombres,
                        apellidos = apellidos,
                        correoInstitucional = email_usuario,
                        password = password_hash,
                        numeroCelular = phone,
                        codigoVerificacion = crear_otp(),
                        usuarioVerificado = False                        
                )
                #Se asigna el tipo de cambio que se hace para trazabilidad
                #El cambio 1 es cuando se registra el usuario en la bd faltando todavía verificar el correo
                idRazonCambio = razonCambio.objects.get(pk=1)
                estudiante._change_reason = idRazonCambio
                
                estudiante.save()

                #Asignar el rol de estudiante
                idRazonCambio = razonCambio.objects.get(pk=7) #Razón cambio 7: Asignación rol estudiante
                estudiante._change_reason = idRazonCambio
                estudiante.roles.add(estudiante.numeroDocumento, 1)                

                ##Envio de correo con el código de verificación
                #El correo necesita un asunto, mensaje que se quiere enviar, quien lo envia, y los correos a los que se quiere enviar
                subject = "Codigo de verificación"
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [email_usuario]

                signer = Signer()
                # Firmar el un token con el correo electrónico del usuario
                token = signer.sign(f"{email_usuario}")

                #Generar el enlace para ingresar el código
                verificacion_url = request.build_absolute_uri(reverse('mostrar_otp', args=[token]))

                #Generamos un html para que el correo que se envia sea más vistoso y no solo texto plano
                context = {
                            "codigo_verificacion": str(estudiante.codigoVerificacion),
                            "link_codigo_verificacion" : verificacion_url,
                        }
                #Renderizamos el template html
                template = get_template("SendMessageEmailOtp.html")
                content = template.render(context)

                email = EmailMultiAlternatives(
                        subject,
                        content,
                        email_from,
                        recipient_list
                        )

                email.attach_alternative(content, "text/html")
                email.send()

                mensaje = '¡Registro exitoso! Revise su correo para verificar la cuenta y poder acceder.'
                return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')
            
    except Exception as e:
        mensaje = f"Ocurrió un error: {str(e)}"
        return redirect(reverse('registroEstudiante') + f'?mensaje={mensaje}')
    
    return redirect(reverse('registroEstudiante') + f'?mensaje={mensaje}')

########################Funcionalidad de OTP####################################

#Método para mostrar la vista de la OTP
def mostrar_otp(request, token):
    try:
        signer = Signer()
        #Desfirmar el token
        correo_usuario = signer.unsign(token).split(":")[0]  # Obtén el primer elemento de la lista (el correo electrónico)
        
        if usuario.objects.filter(correoInstitucional = correo_usuario).exists():
            return render(request, 'OTP.html', {'token': token})
        else:
            # Si el usuario no existe, puedes redirigir a alguna otra página o mostrar un mensaje de error (token invalido)
            mensaje = "Token inválido."
            return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')
        
    except Exception as e:
        mensaje = f"Ocurrió un error: {str(e)}"
        return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')


#Método que procesa el código para verificar al usuario
def aprobar_OTP(request, token):
    try:
        if request.method == "POST":
            signer = Signer()
            #Desfirmar el token
            correo_usuario = signer.unsign(token).split(":")[0]  # Obtén el primer elemento de la lista (el correo electrónico)
            user = usuario.objects.get(correoInstitucional = correo_usuario)
            print(user)
            if user:
                #Obtener los datos del formulario
                OTP = int(request.POST.get('otp_code'))

                if OTP == user.codigoVerificacion:
                    user.usuarioVerificado = True
                    idRazonCambio = razonCambio.objects.get(pk=2) #Cambio 2 es cuando se verfica el correo
                    user._change_reason = idRazonCambio
                    user.save()
                    mensaje = "Validación exitosa. Ya puede iniciar sesión."
                    return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')
                else:
                    mensaje = "Código de verificación incorrecto."
                    return render(request,'OTP.html',{'token': token, 'mensaje': mensaje})
            else:
                mensaje = 'Correo de verificación inválido, intente acceder nuevamente desde el enlace de su correo.'
                return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')
        
    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}"
            return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')


#Metodo para crear la OTP de 6 digitos de longitud
def crear_otp():
    otp = random.randint(100001, 999999)
    return otp

########################Funcionalidad de Login Usuarios####################################

#Este método solo se encarga de mostrar la vista de login
def mostrar_login_usuario(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'LoginPage.html', {'mensaje': mensaje})    

#Este método se encarga de autenticar las credenciales de usuario 
def autenticar_credenciales_usuario(request):
    try:
        if request.method == "POST":
            #Obtener los datos del formulario
            correo_usuario = request.POST.get('email')
            password_usuario = request.POST.get('password')
            
            if  not usuario.objects.filter(correoInstitucional=correo_usuario).exists():
                mensaje = "Usuario no registrado."
                return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')
    
            else:
            #Lógica de validacion de contraseña si la validacion de usuario es exitosa
                # primero obtener el usuario
                user = usuario.objects.get(correoInstitucional = correo_usuario)

                # mirar con la funcion chack_password si es la misma
                if check_password(password_usuario, user.password):

                    # revisar si el usuario esta validado
                    validacionUsuario = user.usuarioVerificado
                
                    if(validacionUsuario == True):
                        #autenticar usuario
                        login(request, user)
                        user.lastLogin = timezone.now()
                        idRazonCambio = razonCambio.objects.get(pk=3)
                        user._change_reason = idRazonCambio
                        user.save() #Guarda el último inicio de sesión
                        # Verifica cuántos roles tiene el usuario
                        roles_count = user.roles.count()
                        roles = user.roles.all()
                        for rol in roles:
                            nombre_rol = rol.nombreRol
                            print(nombre_rol)
                        if roles_count > 1:
                            return redirect(reverse('SeleccionarRol'))
                        else:
                        # Redirige a donde quieras si el usuario tiene un solo rol
                            if request.user.roles.filter(nombreRol='Estudiante').exists():
                                return redirect(reverse('paginaPrincipal_estudiante'))
                            elif request.user.roles.filter(nombreRol='Administrador Bienestar').exists():
                                return redirect(reverse('paginaPrincipalAdministradorBienestar'))
                            elif request.user.roles.filter(nombreRol='Administrador Master').exists():
                                return redirect(reverse('paginaPrincipalAdministradorMaster'))
                    else: 
                        # si no está validado el usuario
                        mensaje = "Revise su correo para válidar la cuenta."
                        return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}') 

                else:
                    # contraseña incorrecta
                    mensaje = "Correo o contraseña incorrectos"
                    return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}&username={correo_usuario}')
                
    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}"
            return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')

#Método se encarga de mostrar los roles que tiene el usuario que se loguea    
def seleccionar_rol(request):
    # Aquí obtienes todos los roles disponibles para el usuario
    roles = request.user.roles.all()
    return render(request, 'SeleccionRolUsuario.html', {'roles': roles})

#Método que se encarga de procesar la selección del rol
def procesar_seleccionar_rol(request):
    if request.method == "POST":
        rol = request.POST.get('selected_role')
        if rol == '1':
            return redirect(reverse('paginaPrincipal_estudiante'))
        elif rol == '2':
            return redirect(reverse('paginaPrincipalAdministradorBienestar'))
        else:
            return redirect(reverse('principalAdminMaster'))

@role_required('Estudiante')
#Este método se encarga de mostrar la vista de PaginaPrincipal Estudiante
def mostrar_mainPage_estudiante(request):
    roles_count = request.user.roles.count()
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'MainPageStudent.html', {'mensaje': mensaje,  'roles_count': roles_count})

@role_required('Administrador Bienestar')
def mostrar_principalAdminBienestar(request):
    roles_count = request.user.roles.count()
    correo_usuario = request.user.correoInstitucional
    return render(request,"PrincipalAdminBienestar.html", {'correo':correo_usuario ,'roles_count': roles_count})

@role_required('Administrador Informes')
def mostrar_principalAdminMaster(request):
    correo_usuario = request.user.correoInstitucional
    mensaje = request.GET.get('mensaje', '')
    return render(request, 'PrincipalAdminMaster.html', {'correo':correo_usuario, 'mensaje':mensaje})

#Cerrar Sesión
def cerrar_sesion(request):
    logout(request)
    return redirect(reverse('loginUsuario'))


########################Funcionalidad de Recuperar Contraseña####################################

#Este método se encarga de mostrar la vista donde el usuario ingresa que desea recuperar contraseña
def mostrar_enviarCorreo_contrasena(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'SendEmailResetPasswordPage.html', {'mensaje': mensaje})

#Metodo para enviar el correo electronico con el link para el reestablecimiento de la contraseña
def procesar_enviarCorreo_contrasena(request):
    try: 
        if request.method=="POST":
            #Obtener los datos del formulario
            correoUsuario = request.POST.get('email')

            #Verificar si el correo ingresado si pertenece a la base de datos
            if  not usuario.objects.filter(correoInstitucional = correoUsuario).exists():
                mensaje = "Usuario no encontrado."
                return redirect(reverse('enviarCorreo_contrasena') + f'?mensaje={mensaje}')

            else:
                #Generar un token único y firmarlo
                signer = Signer()
                # Firmar el token con el correo electrónico del usuario y la marca de tiempo actual
                token = signer.sign(f"{correoUsuario}:{time.time()}")

                #El correo necesita un asunto, mensaje que se quiere enviar, quien lo envia, y los correos a los que se quiere enviar
                subject = "Restablecer tu contraseña"
                message = "No hay problema, puedes restablecer tu contraseña de zenUN\ntras hacer clic en el siguiente enlace:\n\nRestablecer contraseña\n\nSi no solicitaste el restablecimiento de tu contraseña, puedes borrar este email y continuar disfrutando tu aplicación.\nSaludos.\nEl equipo de zenUN Los Capis"
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [correoUsuario]

                #Generar el enlace con el token incluido
                reset_url = request.build_absolute_uri(reverse('cambiar_contrasena', args=[token]))

                #Generamos un html para que el correo que se envia sea más vistoso y no solo texto plano
                context = {
                            "link_resetPassword": reset_url,  # Pasamos link_resetPassword al contexto de ese html
                        }
                #Renderizamos el template html
                template = get_template("SendMessageEmail.html")
                content = template.render(context)

                email = EmailMultiAlternatives(
                        subject,
                        message,
                        email_from,
                        recipient_list
                    )

                email.attach_alternative(content, "text/html")
                email.send()

                #send_mail(subject ,message, email_from, recipient_list,html_message=template,)
                return render(request, "CorreoEnviado.html")
            
    except Exception as e:
        mensaje = f"Ocurrió un error: {str(e)}"
        return redirect(reverse('enviarCorreo_contrasena') + f'?mensaje={mensaje}')

########################Funcionalidad de cambiar contraseña####################################
#Este método muestra la vista de cambiar contraseña 
def mostrar_ResetPasswordPage(request, token):
    # Configurar la duración máxima del token
    DURACION_MAXIMA_TOKEN_SEGUNDOS = 30*60 #30 min máximo

    try:
        signer = Signer()
        # Desfirmar el token
        correo_usuario, tiempo_creacion = signer.unsign(token).split(":")
        
        # Verificar si el token ha expirado comparando la marca de tiempo actual con la marca de tiempo de creación
        tiempo_actual = time.time()

        if (tiempo_actual - float(tiempo_creacion) <= DURACION_MAXIMA_TOKEN_SEGUNDOS) and (usuario.objects.filter(correoInstitucional = correo_usuario).exists()):
            mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
            return render(request, 'ResetPasswordPage.html', {'mensaje':mensaje, 'correo_usuario': correo_usuario, 'token': token})
        else:
            mensaje = 'El token ha expirado. Solicite nuevamente un enlace de recuperación de contraseña.'
            return redirect(reverse('enviarCorreo_contrasena') + f'?mensaje={mensaje}')
        
    except BadSignature:
        mensaje = 'Token inválido.'
        return render(request, 'SendEmailResetPasswordPage.html', {'mensaje': mensaje})
    except Exception as e:
        mensaje = f"Ocurrió un error: {str(e)}"
        return render(request, 'SendEmailResetPasswordPage.html', {'mensaje': mensaje})

#Este metodo procesar el cambio de la contraseña
def procesar_cambio_contrasena(request, correo_usuario, token):
    try:
        if request.method == "POST":
            #Obtener los datos del formulario
            nuevaContraseña = request.POST.get('newPassword')
            confirmacion = request.POST.get('confirmPassword')
            
            # Revisar si el usuario existe
            if  usuario.objects.filter(correoInstitucional= correo_usuario).exists():
                # Revisar si las contraseñas son iguales
                if(nuevaContraseña == confirmacion):
                    #LUEGO CAMBIAR LA CONTRASEÑA EN LA BD
                    #primero buscar al usuario por correo
                        user = usuario.objects.get(correoInstitucional= correo_usuario)
                        password_hash = make_password(nuevaContraseña)
                        user.password = password_hash
                        idRazonCambio = razonCambio.objects.get(pk=4) #Razon de cambio 4: Cambio de contraseña
                        user._change_reason = idRazonCambio
                        user.save()

                        mensaje = "EL CAMBIO DE CONTRASEÑA FUE EXITOSO"
                        return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')
                else:
                    mensaje = 'Las contraseñas no coinciden.'
                    return redirect(reverse('cambiar_contrasena', args=[token]) + f'?mensaje={mensaje}')

            else:
                mensaje = "Solicite un correo de recuperación de contraseña nuevamente"
                return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')

    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}"
            return redirect(reverse('cambiar_contrasena', args=[token]) + f'?mensaje={mensaje}')
    

########################Funcionalidad Registro Administrativo###################################

#Método para mostrar la vista en donde se puede verificar si un posible usuario administrador ya está
#registrado como estudiante o como admin de bienestar
@role_required('Administrador Informes')
def mostrar_vistaVerificarCorreoAdminBienestar(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'VerificacionCorreoRegistroAdministradorBienestar.html', {'mensaje': mensaje})

#Funcionalidad para verificar si un usuario ya está registrado como estudiante
def procesar_verificar_correo_Admin_Bienestar(request):
    try:
        if request.method == "POST":
            correoUsuario = request.POST.get('email')
            
        
            #Verificación del dominio del correo que ingresa
            if not correoUsuario.endswith('@unal.edu.co'):
                mensaje = "El correo debe ser de dominio @unal.edu.co"
                return redirect(reverse('verificacionCorreoAdminBienestar') + f'?mensaje={mensaje}')
            
            # Revisar si el usuario existe
            if not usuario.objects.filter(correoInstitucional=correoUsuario).exists():
                mensaje = "Por favor registre los siguientes datos del nuevo administrador de bienestar."
                print(correoUsuario)
                return redirect(reverse('registroAdministradorBienestar') + f'?mensaje={mensaje}&correo={correoUsuario}')
            else:
                user = usuario.objects.get(correoInstitucional= correoUsuario)
                
                #Verificar si el usuario tiene el rol de ESTUDIANTE y no tiene el de ADMINISTRADOR DE BIENESTAR
                if user.usuarioVerificado==True and user.roles.filter(idRol="1").exists() and not (user.roles.filter(idRol="2").exists()):
                    mensaje = "El usuario" + " " + correoUsuario + " " + "ya se encuentra registrado como estudiante, por favor asigne el rol de Administrador de Bienestar."
                    numeroDocumento = user.numeroDocumento
                    nombres = user.nombres
                    apellidos = user.apellidos
                    return render(request, 'AsignacionRolAdministradorBienestar.html', {'mensaje': mensaje, 'correo': correoUsuario, 'numeroDocumento': numeroDocumento, 'nombres':nombres, 'apellidos':apellidos})
                
                elif user.roles.filter(idRol="2").exists():
                    mensaje = "El usuario" + " " + correoUsuario + " " + "ya se encuentra registrado como Administrador de Bienestar."
                    return redirect(reverse('verificacionCorreoAdminBienestar') + f'?mensaje={mensaje}')
                
                else:
                    mensaje = "El usuario" + " " + correoUsuario + " " + "se encuentra registrado como estudiante pero no ha verificado su cuenta, por favor verifique su cuenta antes de continuar."
                    return redirect(reverse('verificacionCorreoAdminBienestar') + f'?mensaje={mensaje}')
                
    except Exception as e:
        mensaje = f"Ocurrió un error: {str(e)}"
        return redirect(reverse('verificacionCorreoAdminBienestar') + f'?mensaje={mensaje}')
    

@role_required('Administrador Informes')
#Método para mostrar la vista de registro admnistrador bienestar
def mostrar_registro_administrativo(request):
    tipos_documentos = tipoDocumento.objects.all()
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'RegistroAdministradorBienestar.html', {'tipos_documentos':tipos_documentos, 'mensaje': mensaje})

#Este método se encarga de procesar el formulario de registro cuando se envía
def procesar_registro_administrador_bienestar(request):
    try:
        if request.method == "POST":
            #Obtener los datos del formulario
            nombres = request.POST.get('fullName')
            apellidos = request.POST.get('lastName')
            email_usuario = request.POST.get('email')
            email_usuario.lower()
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirmPassword')
            tipo_documento = int(request.POST.get('documentType'))
            phone = request.POST.get('phone')
            numero_documento = request.POST.get('documentNumber')
            
            if not email_usuario.endswith('@unal.edu.co'):
                mensaje = "El correo debe ser de dominio @unal.edu.co"
            elif password != confirm_password:
                mensaje = "Las contraseñas no coinciden"
            elif usuario.objects.filter(correoInstitucional = email_usuario).exists():
                mensaje = "El correo ya se encuentra registrado"
            elif usuario.objects.filter(numeroDocumento = numero_documento).exists():
                mensaje = "El número de documento ya se encuentra registrado"
            else:
            #Lógica de creación de usuario si todas las validaciones son exitosas
                #Tipo de documento
                tipo_doc = tipoDocumento.objects.get(pk=tipo_documento)

                #Primero, generar el hash de la contraseña
                password_hash = make_password(password)

                #Luego, crear el objeto usuario utilizando el hash de la contraseña
                administradorBienestar = usuario(
                        numeroDocumento = numero_documento,
                        idTipoDocumento = tipo_doc,
                        nombres = nombres,
                        apellidos = apellidos,
                        correoInstitucional = email_usuario,
                        password = password_hash,
                        numeroCelular = phone,
                        codigoVerificacion = crear_otp(),
                        usuarioVerificado = False
                )
                idRazonCambio = razonCambio.objects.get(pk=6) #Razón cambio 6: Registro usuario desde el formulario admin
                administradorBienestar._change_reason = idRazonCambio
                administradorBienestar.save()

                #Asignar el rol de administrador de Bienestar
                idRazonCambio = razonCambio.objects.get(pk=5) #Razón cambio 5: Asignación rol admin
                administradorBienestar._change_reason = idRazonCambio
                administradorBienestar.roles.add(administradorBienestar.numeroDocumento, 2)
                
                ##Envio de correo con el código de verificación
                #El correo necesita un asunto, mensaje que se quiere enviar, quien lo envia, y los correos a los que se quiere enviar
                subject = "Codigo de verificación"
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [email_usuario]

                signer = Signer()
                # Firmar el un token con el correo electrónico del usuario
                token = signer.sign(f"{email_usuario}")

                #Generar el enlace para ingresar el código
                verificacion_url = request.build_absolute_uri(reverse('mostrar_otp', args=[token]))

                #Generamos un html para que el correo que se envia sea más vistoso y no solo texto plano
                context = {
                            "codigo_verificacion": str(administradorBienestar.codigoVerificacion),
                            "link_codigo_verificacion" : verificacion_url,
                        }
                #Renderizamos el template html
                template = get_template("SendMessageEmailOtp.html")
                content = template.render(context)

                email = EmailMultiAlternatives(
                        subject,
                        content,
                        email_from,
                        recipient_list
                        )

                email.attach_alternative(content, "text/html")
                email.send()

                mensaje = '¡Registro exitoso! Revise el correo para verificar la cuenta y poder acceder.'
                return redirect(reverse('principalAdminMaster') + f'?mensaje={mensaje}')
            
    except Exception as e:
        mensaje = f"Ocurrió un error: {str(e)}"
        return redirect(reverse('registroAdministradorBienestar') + f'?mensaje={mensaje}')
    
    return redirect(reverse('registroAdministradorBienestar') + f'?mensaje={mensaje}')

#Este método se encarga de asignar el rol de administrador de bienestar al usuario que ya está registrado como estudiante
def procesar_asignacion_rol_administrador_bienestar(request):
    try:
        if request.method == "POST":
            correoUsuario = request.POST.get('email')
            correoUsuario.lower()

            if not correoUsuario.endswith('@unal.edu.co'):
                mensaje = "El correo debe ser de dominio @unal.edu.co"
                return render(request, 'AsignacionRolAdministradorBienestar.html', {'mensaje': mensaje, 'correo': correoUsuario})
            else:
                #Asignacion de rol de administrador de Bienestar
                user = usuario.objects.get(correoInstitucional= correoUsuario)
                idRazonCambio = razonCambio.objects.get(pk=5)
                user._change_reason = idRazonCambio
                user.roles.add(user.numeroDocumento, 2)

                mensaje = "Asignación de rol Administrador de Bienestar exitosa!"
                return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')
    except Exception as e:
        mensaje = f"Ocurrió un error: {str(e)}"
        return render(request, 'AsignacionRolAdministradorBienestar.html', {'mensaje': mensaje, 'correo': correoUsuario})
    

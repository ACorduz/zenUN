from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from usuarios.models import usuario
from usuarios.models import tipoDocumento
from django.urls import reverse
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.core.signing import Signer, BadSignature
import time
import random

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
                estudiante = usuario.objects.create(
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
                estudiante.save()

                #Asignar el rol de estudiante
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
                return redirect(reverse('loginUsuario') + f'mensaje={mensaje}')
    
            else:
            #Lógica de validacion de contraseña si la validacion de usuario es exitosa
                # primero obtener el usuario
                user = usuario.objects.get(correoInstitucional = correo_usuario)

                # mirar con la funcion chack_password si es la misma
                if check_password(password_usuario, user.password):

                    # revisar si el usuario esta validado
                    validacionUsuario = user.usuarioVerificado
                
                    if(validacionUsuario == True):
                        mensaje = "Validacion exitosa."
                        return redirect(reverse('paginaPrincipal_estudiante') + f'?mensaje={mensaje}')
                    else: 
                        # si no está validado el usuario
                        mensaje = "Revise su correo para válidar la cuenta."
                        return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}') 

                else:
                    # contraseña incorrecta
                    mensaje = "Correo y/o contraseña incorrectos"
                    return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}&username={correo_usuario}')
                
    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}"
            return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')

#Este método se encarga de mostrar la vista de PaginaPrincipal Estudiante
def mostrar_mainPage_estudiante(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'MainPageStudent.html', {'mensaje': mensaje})


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

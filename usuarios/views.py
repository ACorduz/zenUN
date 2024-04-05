from django.shortcuts import render
from django.contrib.auth.hashers import make_password, check_password
from usuarios.models import usuario
from usuarios.models import tipoDocumento
from django.shortcuts import redirect
from django.urls import reverse

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from usuarios.forms import FormularioContacto

from django.views.decorators.csrf import csrf_exempt


#Funcionalidad de Registro Estudiantes#

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
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirmPassword')
            tipo_documento = int(request.POST.get('documentType'))
            phone = request.POST.get('phone')
            numero_documento = request.POST.get('documentNumber')
            
            if not email.endswith('@unal.edu.co'):
                mensaje = "El correo debe ser de dominio @unal.edu.co"
            elif password != confirm_password:
                mensaje = "Las contraseñas no coinciden"
            elif usuario.objects.filter(correoInstitucional=email).exists():
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
                        correoInstitucional = email,
                        password = password_hash,
                        numeroCelular = phone,
                        codigoVerificacion = 1234,
                        usuarioVerificado = False
                )
                estudiante.save()

                #Asignar el rol de estudiante
                estudiante.roles.add(estudiante.numeroDocumento, 1)
                
                mensaje = '¡Registro exitoso!'

    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}"

    return redirect(reverse('registroEstudiante') + f'?mensaje={mensaje}')

#Este método solo se encarga de mostrar la vista de login
def mostrar_login_usuario(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'LoginPage.html', {'mensaje': mensaje})


#Este método se encarga de autenticar las credenciales de usuario 
@csrf_exempt
def autenticar_credenciales_usuario(request):
    try:
        if request.method == "POST":
            #Obtener los datos del formulario
            usuarioInterfaz = request.POST.get('username')
            contraseña = request.POST.get('password')
            
            if  not usuario.objects.filter(correoInstitucional=usuarioInterfaz).exists():
                mensaje = "correo no registrado"
                return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')
    
            else:
            #Lógica de validacion de contraseña si la validacion de usuario es exitosa
                # primero obtener el usuario
                user = usuario.objects.get(correoInstitucional= usuarioInterfaz)

                # mirar con la funcion chack_password si es la misma
                if check_password(contraseña, user.password):

                    # revisar si el usuario esta validado
                    validacionUsuario = user.usuarioVerificado
                
                    if(validacionUsuario == True):
                        mensaje = "Validacion exitosa"
                        return redirect(reverse('paginaPrincipal_estudiante') + f'?mensaje={mensaje}')
                    else: 
                        # sino esta validado el usuario
                        mensaje = "Revise su correo. Para validar cuenta"
                        return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}') 
    
                else:
                    # contraseña incorrecta
                    mensaje = "correo y/o contraseña incorrectos"
                    return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}&username={usuarioInterfaz}')
    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}"
            return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')
    

def mostrar_enviarCorreo_contrasena(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'MainPageStudent.html', {'mensaje': mensaje})

#Este método solo se encarga de mostrar la vista de PaginaPrincipal Estudiante
def mostrar_mainPage_estudiante(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'SendEmailResetPasswordPage.html', {'mensaje': mensaje})
   
#Este metodo se encarga de mostrar la vista donde el usuario ingresa que desea recuperar contraseña
#Metodo para enviar el correo electronico con el link para el reestablecimiento de la contraseña
def procesar_enviarCorreo_contrasena(request):
    if request.method=="POST":

        #Creamos un formulario que guardara la información del HTML 
        miFormulario=FormularioContacto(request.POST)
        
        #Verificamos que los campos del formulario sean validos como por ejemplo que sea un correo @
        if miFormulario.is_valid():

            #Obtener los datos del formulario 
            infForm=miFormulario.cleaned_data

            #El correo necesita un asunto, mensaje que se quiere enviar, quien lo envia, y los correos a los que se quiere enviar
            subject = "Restablecer tu contraseña"

            message = "No hay problema, puedes restablecer tu contraseña de zenUN\ntras hacer clic en el siguiente enlace:\n\nRestablecer contraseña\n\nSi no solicitaste el restablecimiento de tu contraseña, puedes borrar este email y continuar disfrutando tu aplicación.\nSaludos.\nEl equipo de zenUN Los Capis"

            email_from = settings.EMAIL_HOST_USER

            recipient_list=[infForm.get('email','')]

   

            #Verificar si el correo ingresado si pertenece a la base de datos
            if  not usuario.objects.filter(correoInstitucional=infForm.get('email','')).exists():
                mensaje = "correo no registrado"
                print(mensaje)
                return render(request, "SendEmailResetPasswordPage.html",{"form":miFormulario})
            
            else:
                # variable necesitada en el template sendMessageEmail, (link_resetPassword)
                user = usuario.objects.get(correoInstitucional= infForm.get('email',''))
                correo = user.correoInstitucional
                # ese codigo cifrado es provisional. Hay que crear una funcion que cree un codigo en numeros y despues pueda ser validado comoCorrecto, con otra funcion
                codigoCifrado = 213115614532
                link_resetPassword = request.build_absolute_uri(reverse('cambiar_contrasena', args=[correo, codigoCifrado]))

                #generamos un html para que el correo que se envia sea más vistoso y no solo texto plano
                context = {
                           "link_resetPassword": link_resetPassword,  # Pasamos link_resetPassword al contexto de ese html
                        }
                # renderizamos el template html
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
    else:
        miFormulario=FormularioContacto()
    
    return render(request, "SendEmailResetPasswordPage.html",{"form":miFormulario})


#Este método muestra la vista de cambiar contraseña 
def mostrar_ResetPasswordPage(request, correoUsuario, codigoCifrado):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    # Pasar los parámetros al contexto
    context = {
        'correoUsuario': str(correoUsuario),
        'codigoCifrado': codigoCifrado, 
        'mensaje': mensaje
    }
    return render(request, 'ResetPasswordPage.html', context)



# Este metodo solo procesar el formulario  y cambio de contraseña en la vista cambio de contraseña
def procesar_cambio_contrasena(request,correoUsuario2, codigoCifrado2):
    try:
        if request.method == "POST":
            # Ojo el correo del usuario es correoUsuario2 y  codigoCifrado = codigoCifrado2

            #Obtener los datos del formulario
            nuevaContraseña = request.POST.get('newPassword')
            confirmacion = request.POST.get('confirmPassword')
            
            # Revisar si el usuario existe
            if  usuario.objects.filter(correoInstitucional= correoUsuario2).exists():
                # Revisar si el codigo es correcto
                ### Mejorar segun una funcion para decifrar y que pase true
                if (codigoCifrado2 == 213115614532):
                    # Revisar si las contraseñas son iguales
                    if(nuevaContraseña == confirmacion):
                        mensaje = "Las contraseñas coinciden"
                        # LUEGO CAMBIAR LA CONTRASEÑA EN LA BD
                        # primero traer al usuario
                        user = usuario.objects.get(correoInstitucional= correoUsuario2)
                        password_hash = make_password(nuevaContraseña)
                        user.password = password_hash
                        user.save()

                        mensaje = "EL CAMBIO DE CONTRASEÑA FUE EXITOSO"
                        return redirect(reverse('cambiar_contrasena', args=("Ya hizo cambio", 0000)) + f'?mensaje={mensaje}')
                    else:
                        mensaje = "las contraseñas NO coinciden"
                        return redirect(reverse('cambiar_contrasena', args=(correoUsuario2, codigoCifrado2)) + f'?mensaje={mensaje}')
                else:
                    mensaje = "Pida un correo de recuperación de contraseña nuevamente"
                    return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')
            else:
                # usuario no registrado redireccion vista registro estudiante
                mensaje = "Usuario no registrado"
                return redirect(reverse('registroEstudiante') + f'?mensaje={mensaje}')

    
    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}"
            return redirect(reverse('loginUsuario') + f'?mensaje={mensaje}')

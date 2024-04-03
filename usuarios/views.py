from django.shortcuts import render
from django.contrib.auth.hashers import make_password, check_password
from usuarios.models import usuario
from usuarios.models import tipoDocumento
from django.shortcuts import redirect
from django.urls import reverse

from django.conf import settings
from django.core.mail import send_mail
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
    
#Este método solo se encarga de mostrar la vista de PaginaPrincipal Estudiante
def mostrar_mainPage_estudiante(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    return render(request, 'MainPageStudent.html', {'mensaje': mensaje})

    

#Este metodo se encarga de mostrar la vista donde el usuario ingresa que desea recuperar contraseña
"""def mostrar_recuperar_contra(requets):

    if requets.method == "POST":

        subject = "Correo de prueba"

        message = "Ojala y funcione"

        email_from = settings.EMAIL_HOST_USER

        recipient_list=[requets.POST["mail"],"cbarrerar"]

        print("entra aqui")
        print(recipient_list)

        send_mail(subject, message, email_from, recipient_list)

        return render(requets, "CorreoEnviado.html",{})
    
    return render(requets, "EnviarCorreoRecup.html",{})"""


def mostrar_recuperar_contra(request):
    if request.method=="POST":

        miFormulario=FormularioContacto(request.POST)
        if miFormulario.is_valid():
            infForm=miFormulario.cleaned_data
            print(infForm['asunto'])
            print(infForm['mensaje'])
            print(infForm.get('email',''))
            send_mail(infForm['asunto'], infForm['mensaje'], settings.EMAIL_HOST_USER,[infForm.get('email','')],)
            print("Valio aqui")
            return render(request, "CorreoEnviado.html")
    else:
        miFormulario=FormularioContacto()
    
    return render(request, "EnviarCorreoRecup.html",{"form":miFormulario})

from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from usuarios.models import usuario
from usuarios.models import tipoDocumento
from django.shortcuts import redirect
from django.urls import reverse

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
from django.shortcuts import render,redirect
from django.urls import reverse
from prestamos.models import prestamo, implemento, edificio, comentarioImplemento
from usuarios.models import usuario




################# Funcionalidad Solicitar Prestamo Estudiante ################

#Este método solo se encarga de mostrar la vista de solicitar Prestamo
def mostrar_solicitarPrestamo(request):
    # Aqui se utiliza la base de datos para traer los datos que necesitamos
    implemento = "Implemento X"
    edificio = "Edificio Y"
    nombre_estudiante = "Juan"
    correo_estudiante = "juan@example.com"
    inicio_reserva = "10:00 AM"
    fin_reserva = "11:00 AM"
    devolucion_implemento = "11:30 AM"

    # Pasas los datos al contexto para que puedan ser renderizados en el template
    context = {
        'implemento': implemento,
        'edificio': edificio,
        'nombre_estudiante': nombre_estudiante,
        'correo_estudiante': correo_estudiante,
        'inicio_reserva': inicio_reserva,
        'fin_reserva': fin_reserva,
        'devolucion_implemento': devolucion_implemento,
    }
    
    return render(request, 'LoanApply.html', context)


################# Funcionalidad Devolucion Prestamo AdministradorBienestar ################
def mostrar_devolucionImplementos_administradorBienestar(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    implemento_prestado = request.GET.get('implemento_prestado', '')  # Obtener el implementoPrestado de la URL, si está presente
    facultad_implemento = request.GET.get('facultad_implemento', '')  # Obtener el facultad_implemento de la URL, si está presente
    nombre_estudiante  = request.GET.get('nombre_estudiante', '')  # Obtener el nombre_estudiante de la URL, si está presente
    correo_estudiante  = request.GET.get('correo_estudiante', '')  # Obtener el correo_estudiante de la URL, si está presente
    inicio_prestamo = request.GET.get('inicio_prestamo', '')  # Obtener el inicio_prestamo de la URL, si está presente
    fin_prestamo = request.GET.get('fin_prestamo', '')  # Obtener el fin_prestamo de la URL, si está presente
    revision_datos = request.GET.get('revision_datos', '0')  # Obtener un parametro que nos dice si la persona reviso los datos , si está presente

    # pasarle el contexto de lo que haya
    contexto = {
                'mensaje': mensaje,
                'implemento_prestado': implemento_prestado,
                'facultad_implemento': facultad_implemento,
                'nombre_estudiante': nombre_estudiante,
                'correo_estudiante': correo_estudiante,
                'inicio_prestamo': inicio_prestamo,
                'fin_prestamo': fin_prestamo,
                'revision_datos':revision_datos
            }
    # retornar la URL
    return render(request, 'DevolucionImplementos.html', contexto)

def mostrar_informacionPrestamo_devolucionImplementos_administradorBienestar(request):
    try:
        if request.method == "POST":

            # Obtener los datos del formulario
            NumeroDocumento = request.POST.get('documentNumber')
            try:
                # ver si existe el prestamo
                if prestamo.objects.filter(estudianteNumeroDocumento=NumeroDocumento, estadoPrestamo="ACTIVO"):

                    ## Traer los objetos de la BD
                    objetoPrestamo = prestamo.objects.get(estudianteNumeroDocumento=NumeroDocumento, estadoPrestamo="ACTIVO")
                    objetoImplemento =  implemento.objects.get(idImplemento = objetoPrestamo.idImplemento)
                    objetoEdificio = edificio.objects.get(idEdificio = objetoImplemento.edificioId)
                    objetoEstudiante = usuario.objects.get(numeroDocumento= objetoPrestamo.estudianteNumeroDocumento)


                    ## poner los datos de la BD en variables para el front
                    mensaje = "Obtencion de datos exitosa"
                    implemento_prestado =  objetoImplemento.nombreImplemento
                    facultad_implemento = objetoEdificio.nombreEdificio
                    nombre_estudiante = f"´{objetoEstudiante.nombres} {objetoEstudiante.apellidos}"
                    correo_estudiante = objetoEstudiante.correoInstitucional
                    inicio_prestamo = objetoPrestamo.fechaHoraInicioPrestamo
                    fin_prestamo = objetoPrestamo.fechaHoraFinPrestamo
                    revision_datos="1" # para saber si el adm. Bienestar reviso los datos de la persona 

                    # Pasar los datos a una cadena para que puedan ser pasados a la url
                    cadenaURLParametros = f'?mensaje={mensaje}&implemento_prestado={implemento_prestado}&facultad_implemento={facultad_implemento}&nombre_estudiante={nombre_estudiante}&correo_estudiante={correo_estudiante}&inicio_prestamo={inicio_prestamo}&fin_prestamo={fin_prestamo}&revision_datos={revision_datos}'
                    # mandar los datos a la vista devolucion de implementos
                    return redirect(reverse("devolucionImplementos") + cadenaURLParametros)   
                
                else: #si no hay ningun objetoPrestamo con ese numero de documento
                    mensaje = f"El estudiante con ese numero de documento no tiene ningun prestamo activo" # solo se le pasaria el mensaje en la URL 
                    return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')

            except Exception as e:
                mensaje = f"Ocurrió un error con la BD: {str(e)}" # solo se le pasaria el mensaje en la URL 
                return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')
    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}" # solo se le pasaria el mensaje en la URL 
            return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')


def procesar_devolucion_devolucionImplementos_administradorBienestar(request):
    try:
        if request.method == "POST":

            #Obtener los datos del formulario
            comentario = request.POST.get('comentario')

            ## meter el comentario en la BD y cambiar el estado del implemento

    
            mensaje = 'Devolucion del implemento exitoso'# solo se le pasaria el mensaje en la URL 
            return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')
        
    except Exception as e:
        mensaje = f"Ocurrió un error: {str(e)}" # solo se le pasaria el mensaje en la URL 
        return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')

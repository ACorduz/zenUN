from django.shortcuts import render,redirect
from django.urls import reverse



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

            #Obtener los datos del formulario
            nombres = request.POST.get('documentNumber')

            # Datos traidos de la BD
            mensaje = "DatoBD"
            implemento_prestado = "DatoBD"
            facultad_implemento = "DatoBD"
            nombre_estudiante = "DatoBD"
            correo_estudiante = "DatoBD"
            inicio_prestamo = "DatoBD"
            fin_prestamo = "DatoBD"
            revision_datos="1" # para saber si el adm. Bienestar reviso los datos de la persona 

            # Pasar los datos a la cadena para que puedan ser pasados a la url 
            cadenaURLParametros = f'?mensaje={mensaje}&implemento_prestado={implemento_prestado}&facultad_implemento={facultad_implemento}&nombre_estudiante={nombre_estudiante}&correo_estudiante={correo_estudiante}&inicio_prestamo={inicio_prestamo}&fin_prestamo={fin_prestamo}&revision_datos={revision_datos}'''
        
        return redirect(reverse("devolucionImplementos") + cadenaURLParametros)
            
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

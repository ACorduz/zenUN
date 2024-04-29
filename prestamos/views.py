from django.shortcuts import render

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
    return render(request, 'DevolucionImplementos.html', {'mensaje': mensaje})

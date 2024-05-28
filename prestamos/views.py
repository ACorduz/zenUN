from django.shortcuts import render,redirect
from django.urls import reverse
from prestamos.models import prestamo, implemento, edificio, comentarioImplemento, estadoImplemento,estadoPrestamo
from usuarios.models import usuario
from usuarios.models import razonCambio
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Max
from usuarios.views import role_required
from django.contrib import messages
from apscheduler.schedulers.background import BackgroundScheduler


################# Funcionalidad Solicitar Prestamo Estudiante ################
#Función para revisar si pasaron 15 minutos desde que el estudiante pidio el prestamo

def verificar_tiempoReserva(request):
    #print("Entro a la función")

    #Obtener el numero de documento del usuario que esta en la sesión y la hora actual
    numeroDocumento = request.user.numeroDocumento
    fecha_actual = timezone.now() + timedelta(hours=-5)

    #Verificar si el estudiante aun no ha reclamado su implemento, si esta vacia la lista es False
    prestamo_filtrado = prestamo.objects.filter(estadoPrestamo_id="1",estudianteNumeroDocumento=numeroDocumento)
    if prestamo_filtrado:
        #print("La reserva se paso de su tiempo limite")
        #Obtener el id del prestamo y del implemento del prestamo que se encontro del estudiante
        for prestamo_obj in prestamo_filtrado:
            id_prestamo = prestamo_obj.idPrestamo
            id_implemento = prestamo_obj.idImplemento.idImplemento

        #Pasar el estado del prestamo a 4 "CANCELADO"
        prestamo_cancelar = prestamo.objects.get(idPrestamo = id_prestamo)
        Estado_prestamo = estadoPrestamo.objects.get(idEstadoPrestamo = 4)
        prestamo_cancelar.estadoPrestamo = Estado_prestamo
        #Trazabilidad
        idRazonCambio = razonCambio.objects.get(pk=11) #Razón de cambio 11: Préstamo cancelado por pasar más de 15 mins 
        prestamo_cancelar._change_reason = idRazonCambio            
        prestamo_cancelar.save()

        #Pasar el estado del implemento a 3 "DISPONIBLE"
        implemento_devolver = implemento.objects.get(idImplemento= id_implemento)
        Estado_Implemento = estadoImplemento.objects.get(idEstadoImplemento = 3)
        implemento_devolver.estadoImplementoId = Estado_Implemento
        #Trazabilidad
        idRazonCambio = razonCambio.objects.get(pk=10) #Razón de cambio 10: Implemento disponible al ser cancelado el préstamo
        implemento_devolver._change_reason = idRazonCambio
        implemento_devolver.save()

        #print("El prestamo fue cancelado y el implemento ahora esta disponible") 

        #Enviar correo
        #Recuperar los datos del estudiante de la base de datos para enviarlos por el correo electronico
        numeroDocumento = prestamo_cancelar.estudianteNumeroDocumento.numeroDocumento
        nombreImplemento = prestamo_cancelar.idImplemento.nombreImplemento
        fechaFinalizacionReserva = prestamo_cancelar.fechaHoraInicioPrestamo

        Proceso_enviarCorreo_cancelarPrestamo(
                numeroDocumento, 
                nombreImplemento, 
                fechaFinalizacionReserva, 
                fecha_actual)

# Metodo para enviar el correo electronico de que la reserva fue cancelada
def Proceso_enviarCorreo_cancelarPrestamo(numeroDocumento, nombreImplemento, fechaFinalizacionReserva,fechaActual):
    try: 
        # obtener el correo del usuario
        usuarioObject = usuario.objects.get(numeroDocumento = numeroDocumento)
        correoUsuario = usuarioObject.correoInstitucional
        # no se verifica si el correo ingresado existe pues para llamar a este metodo ya deberia haberse verificado esto    

        #El correo necesita un asunto, mensaje que se quiere enviar, quien lo envia, y los correos a los que se quiere enviar
        subject = "Tu prestamo a sido cancelado"
        message = ""
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [correoUsuario]

        #Generamos un html para que el correo que se envia sea más vistoso y no solo texto plano
        context = {
                    "nombreImplemento": nombreImplemento,
                    "nombreEstudiante": f"{usuarioObject.nombres.strip()} {usuarioObject.apellidos.strip()}",
                    "numeroDocumentoEstudiante":numeroDocumento,
                    "fechaFinalizacionReserva": fechaFinalizacionReserva,
                    "fechaActual": fechaActual
                }
        #Renderizamos el template html
        template = get_template("SendMessageEmailCancelarPrestamo.html")
        content = template.render(context)

        email = EmailMultiAlternatives(
                subject,
                message,
                email_from,
                recipient_list
            )

        email.attach_alternative(content, "text/html")
        email.send()
        
        return(True, "envio correo devolución exitoso")

    except Exception as e:
        return(False , f"no se pudo enviar correo devolución: {e}")
    
#Metodo para iniciar el trabajo en segundo plano
def generar_tareaSegundoPlano(request):
    #Funcion para llamar periodicamente la revisión de la reserva
    # Crea una instancia del planificador
    scheduler = BackgroundScheduler()

    hora_actual = timezone.now() #+ timedelta(hours=-5)
    # Agrega la tarea programada al planificador que se ejecuta 15 minutos despues de realizar la reserva
    scheduler.add_job(verificar_tiempoReserva, 'date', run_date=hora_actual + timedelta(minutes=15), args=[request])

    # Inicia el planificador
    scheduler.start()
    return render(request, 'PrincipalAdminMaster.html')

#Este método solo se encarga de mostrar la vista de solicitar Prestamo
def mostrar_solicitarPrestamo(request,implemento_id):

    # Obtener el usuario que ha iniciado sesión
    usuario_actual = request.user
    nombre_usuario = usuario_actual.nombres
    documento_usuario = usuario_actual.numeroDocumento
    #print("Nombre del usuario:", nombre_usuario)
    #print("Documento del usuario:", documento_usuario)

    # Obtener todos los préstamos activos del usuario
    prestamos_activos = prestamo.objects.filter(
    estudianteNumeroDocumento=usuario_actual,
    estadoPrestamo__nombreEstado__in=['PROCESO', 'ACTIVO']
    )
    #print("Prestamos activos del usuario:", prestamos_activos)
    # Verificar si el usuario tiene préstamos activos
    if prestamos_activos.exists():
        # Mostrar un mensaje de error al usuario
        #print("NO puedes reservar con prestamos activos")
        mensaje = "No puedes reservar si ya tienes un prestamo activo"
        # Redireccionar al usuario a la página de disponibilidad de implementos o a donde desees
        mensaje = "El usuario ya se encuentra registrado como Administrador de Bienestar."
        return mostrar_tabla_disponibilidad_implementos(request, mensaje=mensaje)
    else:
        # A partir del id del implemento pasado por URL se instancian los objetos de implemento y edificio para mostrarlos en pantalla
        implemento_obj = implemento.objects.get(pk=implemento_id)
        edificio_obj = edificio.objects.get(pk = implemento_obj.edificioId.idEdificio)
        implementoPrestamo = implemento_obj.nombreImplemento
        edificioPrestamo = edificio_obj.nombreEdificio

        #Como hay una sesión iniciada recuperamos los datos de la cooki del usuario logeado
        nombre_estudiante = f"{request.user.nombres.strip()} {request.user.apellidos.strip()}"
        correo_estudiante = request.user.correoInstitucional

        #Tomamos el tiempo actual y calculamos el tiempo de la reserva y el tiempo para devolver el implemento
        hora_inicio_reserva = timezone.now() + timedelta(hours=-5)
        hora_fin_reserva = hora_inicio_reserva + timedelta(minutes=15)
        hora_devolucion_implemento = hora_fin_reserva + timedelta(hours=2)

        # Pasar los datos al contexto para que puedan ser renderizados y mostrados en el html
        context = {
            'implemento': implementoPrestamo,
            'implemento_id': implemento_id,
            'edificio': edificioPrestamo,
            'nombre_estudiante': nombre_estudiante,
            'correo_estudiante': correo_estudiante,
            'inicio_reserva': hora_inicio_reserva,
            'fin_reserva': hora_fin_reserva,
            'devolucion_implemento': hora_devolucion_implemento
        }
        
        return render(request, 'LoanApply.html', context)

#Función para guardar la información del prestamo en la base de datos
def guardar_informacionPrestamo(request,implemento_id):

    # ver si alguien más ya reservo o pidio prestado el mismo objeto que el usuario
    if prestamo.objects.filter(idImplemento=implemento_id, estadoPrestamo_id="1") or prestamo.objects.filter(idImplemento=implemento_id, estadoPrestamo_id="2") : # En la BD 1 = RESERVADO 2 = PRESTADO
        
        mensaje = f"Parece que alguien más ya pidio este objeto, lo sentimos, puedes elegir otro implemento" # solo se le pasaria el mensaje en la URL 
        return redirect(reverse('paginaPrincipal_estudiante') + f'?mensaje={mensaje}')

    else:
        #llamar la funcion que verifica despues de 15 minutos si el prestamo ya fue tomado
        generar_tareaSegundoPlano(request)

        # Instanciar el objeto usuario para guardarlo en el prestamo
        estudiante = usuario.objects.get(numeroDocumento=request.user.numeroDocumento)  
        
        #Hay que cambiar el estado del implemento a 1 "RESERVA"
        Implemento = implemento.objects.get(idImplemento = implemento_id)
        Estado_Implemento = estadoImplemento.objects.get(idEstadoImplemento = 1)
        Implemento.estadoImplementoId = Estado_Implemento
        #Trazabilidad
        idRazonCambio = razonCambio.objects.get(pk=8) #Razón de cambio 8: Implemento en reserva al solicitar un préstamo
        Implemento._change_reason = idRazonCambio
        Implemento.save()

        #Instanciar el estado del prestamo 1 "PROCESO" para guardarlo en la información del prestamo
        Estado_Prestamo = estadoPrestamo.objects.get(idEstadoPrestamo = 1)

        #Obtener la hora en la cual el estudiante dio click en el boton realizar reserva

        hora_inicio_reserva = timezone.now() + timedelta(hours=-5)
        hora_fin_reserva = hora_inicio_reserva + timedelta(minutes=15)
        hora_devolucion_implemento = hora_fin_reserva + timedelta(hours=2)

        # Crear una nueva instancia de Prestamo y asignar valores a sus campos
        Prestamo = prestamo(
            estudianteNumeroDocumento=estudiante,
            fechaHoraCreacion=hora_inicio_reserva,
            fechaHoraInicioPrestamo=hora_fin_reserva,
            fechaHoraFinPrestamo=hora_devolucion_implemento,
            estadoPrestamo=Estado_Prestamo,
            idImplemento = Implemento,
            comentario=""
        )

        #Trazabilidad
        idRazonCambio = razonCambio.objects.get(pk=9) #Razón de cambio 9: Préstamo en proceso al crearlo
        Prestamo._change_reason = idRazonCambio
        
        Prestamo.save()
        
        return render(request, 'CheckLoan.html')


################# Funcionalidad Devolucion Prestamo AdministradorBienestar ################

def mostrar_devolucionImplementos_administradorBienestar(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    revision_datos = request.GET.get('revision_datos', '0')  # Obtener un parametro que nos dice si la persona reviso los datos , si está presente, sino poner 0 es dececir no reviso

    # pasarle el contexto de lo que haya
    contexto = {
                'mensaje': mensaje,
                'revision_datos':revision_datos,
                'numeroDocumento': 000000000 # necesario cargarlo al contexto para que corra el html devolucionImplementos
            }
    # retornar la URL
    return render(request, 'DevolucionImplementos.html', contexto)

# Metodo para procesar la información del prestamo pasando los datos a la URL 
def mostrar_informacionPrestamo_devolucionImplementos_administradorBienestar(request):
    try:
        if request.method == "POST":

            # Obtener los datos del formulario
            NumeroDocumento = request.POST.get('documentNumber')
            #print(type(NumeroDocumento))
            try:
                # ver si existe el prestamo
                if prestamo.objects.filter(estudianteNumeroDocumento=NumeroDocumento, estadoPrestamo_id="2"): # En la BD 2 = ACTIVO

                    ## Traer los objetos de la BD
                    objetoPrestamo = prestamo.objects.get(estudianteNumeroDocumento=NumeroDocumento, estadoPrestamo_id="2") # solo deberia ser uno 
                    objetoImplemento =  implemento.objects.get(idImplemento = objetoPrestamo.idImplemento.idImplemento)
                    objetoEdificio = edificio.objects.get(idEdificio = objetoImplemento.edificioId.idEdificio)
                    objetoEstudiante = usuario.objects.get(numeroDocumento= objetoPrestamo.estudianteNumeroDocumento.numeroDocumento)


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
                    return redirect(reverse("devolucionImplementosConParametroNumeroDocumento", args=[NumeroDocumento]) + cadenaURLParametros)   
                
                else: #si no hay ningun objetoPrestamo con ese numero de documento
                    mensaje = f"El estudiante con ese numero de documento no tiene ningun prestamo activo" # solo se le pasaria el mensaje en la URL 
                    return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')

            except Exception as e:
                mensaje = f"Ocurrió un error con la BD: {str(e)}" # solo se le pasaria el mensaje en la URL 
                print(mensaje)
                return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')
    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}" # solo se le pasaria el mensaje en la URL 
            return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')

# Metodo para mostrar la vista devolucionImplementos.html pero cogiendo los datos de la URL 
def mostrar_devolucionImplementosConParametroNumeroDocumento_administradorBienestar(request, numeroDocumento): 
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
                'revision_datos':revision_datos,
                'numeroDocumento': numeroDocumento # pasar el numero de documento al contexto el VERDADERO
            }
    
    # retornar la URL
    return render(request,'DevolucionImplementos.html', contexto)

# Metodo para procesar la devolucion de un implemento 
def procesar_devolucion_devolucionImplementos_administradorBienestar(request, numeroDocumento):
    try:
        if request.method == "POST":
            #print(numeroDocumento)
            # obtener el comentario del html
            comentarioBack= request.POST.get('comentario')

            # Obtener el objeto del prestamo  
            objetoPrestamo = prestamo.objects.get(estudianteNumeroDocumento=numeroDocumento, estadoPrestamo_id="2") 

            # Obtener el id del implemento 
            ImplementoIdBack = objetoPrestamo.idImplemento.idImplemento

            # Obtener el implemento 
            objetoImplemento = implemento.objects.get(idImplemento= f"{ImplementoIdBack}")


            # Crear le comentario del implemento y meterlo en la BD
            comentario = comentarioImplemento(
                comentario= comentarioBack,
                implementoId= objetoImplemento  # Asigna el objeto implemento existente al campo ForeignKey
            )

            ## cambiar el estado del implemento a DISPONIBLE (3) Y Cambiar el estado del prestamo a FINALIZADO(3)
            # cambiar el estado del prestamo 
            objetoEstadoPrestamoFinalizado = estadoPrestamo.objects.get(idEstadoPrestamo= "3")
            objetoPrestamo.estadoPrestamo = objetoEstadoPrestamoFinalizado  # FINALIZADO
            
          

            #cambiar el estado del implemento 
            objetoEstadoImplementoFinalizado = estadoImplemento.objects.get(idEstadoImplemento= "3") 
            objetoImplemento.estadoImplementoId = objetoEstadoImplementoFinalizado  # DISPONIBLE
    
            # cambiar el estado de finalizacion del prestamo
            objetoPrestamo.fechaHoraFinPrestamo =  timezone.now() + timedelta(hours=-5) 

            # Guardar los objetos cambiados o creados por si pasa algo y no se ejecuta bien por eso aqui
            comentario.save()

            idRazonCambio = razonCambio.objects.get(pk=15) #Razon de cambio 15: Préstamo finalizado
            objetoPrestamo._change_reason = idRazonCambio
            objetoPrestamo.save()

            idRazonCambio = razonCambio.objects.get(pk=14) #Razon de cambio 14: Implemento disponible tras finalizar el préstamo
            objetoImplemento._change_reason = idRazonCambio
            objetoImplemento.save()

            # link  para el login
            link_login = request.build_absolute_uri(reverse('loginUsuario'))

            # llamar a un metodo para enviar el correo de devolucion
            seEnvioCorreo, mensajeCorreo = Proceso_enviarCorreo_devolucionImplementos(
                numeroDocumento, 
                objetoImplemento.nombreImplemento, 
                objetoPrestamo.fechaHoraInicioPrestamo,
                objetoPrestamo.fechaHoraFinPrestamo,
                f"{request.user.nombres.strip()} {request.user.apellidos.strip()}", #datos de la cookie nombre adm. bienestar
                f"{request.user.correoInstitucional}", #datos de la cookie correo adm bienestar 
                link_login
            )

            if seEnvioCorreo:
                mensaje = f'Devolucion del implemento exitoso, {mensajeCorreo} '# solo se le pasaria el mensaje en la URL 
                return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')
            else:
                mensaje = f'Devolucion del implemento exitoso, {mensajeCorreo} '# solo se le pasaria el mensaje en la URL 
                return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')
        
    except Exception as e:
        mensaje = f"Ocurrió un error: {str(e)}" # solo se le pasaria el mensaje en la URL 
        return redirect(reverse('devolucionImplementos') + f'?mensaje={mensaje}')

# Metodo para enviar el correo electronico 
def Proceso_enviarCorreo_devolucionImplementos(numeroDocumento, nombreImplemento, fechaDevolucionInicial, fechaDevolucionFinal , nombreEncargadoBienestar,correoEncargadoBienestar,link_login):
    try: 
        # obtener el correo del usuario
        usuarioObject = usuario.objects.get(numeroDocumento = numeroDocumento)
        correoUsuario = usuarioObject.correoInstitucional
        # no se verifica si el correo ingresado existe pues para llamar a este metodo ya deberia haberse verificado esto    

        #El correo necesita un asunto, mensaje que se quiere enviar, quien lo envia, y los correos a los que se quiere enviar
        subject = "Resumen devolucion implemento ZenUN"
        message = ""
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [correoUsuario]

        #Generamos un html para que el correo que se envia sea más vistoso y no solo texto plano
        context = {
                    "nombreImplemento": nombreImplemento,
                    "nombreEstudiante": f"{usuarioObject.nombres.strip()} {usuarioObject.apellidos.strip()}",
                    "numeroDocumentoEstudiante":numeroDocumento,
                    "fechaDevolucionInicial": fechaDevolucionInicial,
                    "fechaDevolucionFinal": fechaDevolucionFinal,
                    "nombreEncargadoBienestar":nombreEncargadoBienestar,
                    "correoEncargadoBienestar": correoEncargadoBienestar,
                    "link_login": link_login
                }
        #Renderizamos el template html
        template = get_template("SendMessageEmailDevolucionImplementoExitosa.html")
        content = template.render(context)

        email = EmailMultiAlternatives(
                subject,
                message,
                email_from,
                recipient_list
            )

        email.attach_alternative(content, "text/html")
        email.send()
        
        return(True, "envio correo devolución exitoso")

    except Exception as e:
        return(False , f"no se pudo enviar correo devolución: {e}")


################# Funcionalidad Habilitar/Deshabilitar boton################
@role_required('Estudiante')
def mostrar_tabla_disponibilidad_implementos(request, mensaje=None):
    # Obtener todos los implementos
    implementos_con_ultimos_prestamos = implemento.objects.annotate(
        ultima_fecha_inicio_prestamo=Max('prestamo__fechaHoraCreacion'),
        ultima_fecha_fin_prestamo=Max('prestamo__fechaHoraFinPrestamo')
    )
    edificios = edificio.objects.all()
    correo_usuario = request.user.correoInstitucional
    return render(request, 'disponibilidad.html', {'implementos': implementos_con_ultimos_prestamos, 'edificios': edificios, 'correo': correo_usuario, 'mensaje': mensaje})
    
    # # Obtener la hora actual en UTC
    # hora_actual_utc = timezone.now()

    # # Ajustar la hora actual a la zona horaria de Bogotá (UTC-5)
    # diferencia_horaria = timedelta(hours=-5)
    # hora_actual_bogota = hora_actual_utc + diferencia_horaria

    # # Verificar y actualizar los préstamos en reserva
    # for implemento_obj in implementos:
    #     implemento_obj.prestamos = prestamo.objects.filter(idImplemento=implemento_obj)
    #     for prestamo_obj in implemento_obj.prestamos:
    #         #print("Prestamo:", prestamo_obj)
    #         #print("Estado del préstamo:", prestamo_obj.estadoPrestamo.nombreEstado)
    #         #print("Fecha y hora de finalización del préstamo:", prestamo_obj.fechaHoraFinPrestamo)
            
    #         # Verificar si el préstamo está en proceso y tiene una fecha de finalización
    #         if prestamo_obj.estadoPrestamo.nombreEstado == 'PROCESO' and prestamo_obj.fechaHoraFinPrestamo:
    #             print("Hora actual en Bogotá:", hora_actual_bogota.time())
    #             #print("Hora máxima de reserva:", prestamo_obj.fechaHoraFinPrestamo.time())
    #             if hora_actual_bogota.time() > prestamo_obj.fechaHoraFinPrestamo.time():
    #                 print("La hora actual es mayor que la hora máxima de reserva.")
    #                 prestamo_obj.estadoPrestamo = estadoPrestamo.objects.get(nombreEstado='FINALIZADO')
    #                 prestamo_obj.fechaHoraInicioPrestamo = None
    #                 prestamo_obj.fechaHoraFinPrestamo = None
    #                 prestamo_obj.save()

    #                 # Actualizar el estado del implemento a DISPONIBLE
    #                 implemento_obj.estadoImplementoId = estadoImplemento.objects.get(nombreEstadoImplemento='DISPONIBLE')
    #                 implemento_obj.save()
    
    

def solicitar_prestamo(request, implemento_id):
    # Obtener el implemento usando su ID
    implemento_obj = implemento.objects.get(pk=implemento_id)
    # Pasar el implemento a la plantilla de solicitud de préstamo, ejemplo:
    return render(request, 'principalAdminBienestar.html', {'implemento': implemento_obj})


 ################# Funcionalidad Aprobar Prestamo Estudiante ################
@role_required('Administrador Bienestar')
def mostrar_tabla_aprobar(request):
    prestamos = prestamo.objects.all().filter(estadoPrestamo_id=1)
    print(prestamos) # En la BD 1 = PROCESO
    return render(request, 'Aprobar_prestamo_tabla.html', {'Prestamos': prestamos})


################# Actualizamos la vista principal de aprobar prestamo individual################
def procesar_implemento_AdministradorBienestar(request, idImplemento, estudianteNumeroDocumento):
    usuario_actual = request.user
    nombre_usuario = usuario_actual.nombres
    documento_usuario = usuario_actual.numeroDocumento

    # Traemos la información del estudiante
    estudiente_obj = usuario.objects.get(pk=estudianteNumeroDocumento)
    implemento_obj = implemento.objects.get(pk = idImplemento)
            
    nombreEstudiante = estudiente_obj.nombres
    correoEstudiante = estudiente_obj.correoInstitucional
            
    nombreImplemento = implemento_obj.nombreImplemento

    hora = timezone.now()+timedelta(hours=-5)

    context = {
        "fecha_aprobacion": hora,
        "nombre_administrador": nombre_usuario,
        "documento_administrador": documento_usuario,
        "idImplemento": idImplemento,
        "nombreImplemento": nombreImplemento,
        "nombre_estudiante": nombreEstudiante,
        "correo_estudiante": correoEstudiante,
        "documento_estudiante": estudianteNumeroDocumento,
        }
    
    
    return render(request, 'Aprobar_prestamo_individual.html', context)

def procesar_aprobar_prestamo(request, idImplemento, estudianteNumeroDocumento, documento_usuario):
    try:
        if request.method == "POST":
            prestamo_obj = prestamo.objects.filter(estudianteNumeroDocumento=estudianteNumeroDocumento).order_by('-fechaHoraCreacion').first() 
            implemento_obj = implemento.objects.get(pk=idImplemento)
            # Obtenemos la información del estudiante
            estudiante_info = usuario.objects.get(numeroDocumento=estudianteNumeroDocumento)

            prestamo_obj.administradorBienestarNumeroDocumento_id = documento_usuario
            prestamo_obj.fechaHoraInicioPrestamo = timezone.now() + timedelta(hours=-5)

            # Cambiar el estado del prestamo a ACTIVO
            objetoEstadoPrestamoActivo = estadoPrestamo.objects.get(idEstadoPrestamo= "2")
            prestamo_obj.estadoPrestamo = objetoEstadoPrestamoActivo # ACTIVO

            # Cambiar el estado del implemento a PRESTADO
            obejtoEstadoImplementoPrestado = estadoImplemento.objects.get(idEstadoImplemento= "2")
            implemento_obj.estadoImplementoId = obejtoEstadoImplementoPrestado

            #Trazabilidad préstamo
            idRazonCambio = razonCambio.objects.get(pk=13) #Razón de cambio 13: Préstamo activo
            prestamo_obj._change_reason = idRazonCambio

            prestamo_obj.save()

            #Trazabilidad implemento
            idRazonCambio = razonCambio.objects.get(pk=12) #Razón de cambio 12: Implemento prestado
            implemento_obj._change_reason = idRazonCambio
            implemento_obj.save()

            ############## Envio de correo ############################     
            # Generación del resumen para enviarse por correo
            subject = "Resumen de aprobación de préstamo"
            message = ""
            email_form = settings.EMAIL_HOST_USER
            recipient_list = [estudiante_info.correoInstitucional]

            # Generar el contenido del correo
            context = {
                "nombreEstudiante": estudiante_info.nombres,
                "nombreImplemento": implemento_obj.nombreImplemento,
                "fechaCreacion": prestamo_obj.fechaHoraCreacion,
                "link_login": request.build_absolute_uri(reverse('loginUsuario'))
            }

            # Renderizar el template html
            template = get_template("CorreoResumenAprobar.html")
            content = template.render(context)

            # Armamos el correo a enviar

            email = EmailMultiAlternatives(
                subject,
                message,
                email_form,
                recipient_list
            )

            email.attach_alternative(content, "text/html")
            email.send()

            ###########################################################
            mensaje = f'Se ha realizado la transacción con exito.'
            return redirect(reverse("Mostrar_aprobarPrestamo_tabla") + f'?mensaje={mensaje}')

    except Exception as e:
        mensaje = f"Ocurrió un error: {str(e)}" # solo se le pasaria el mensaje en la URL 
        return redirect(reverse('Mostrar_aprobarPrestamo_tabla') + f'?mensaje={mensaje}')
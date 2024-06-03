from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse

from django.http import HttpResponse, HttpResponseBadRequest
# se va a utilizar la libreria reportLab para hacer los reportes
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm 
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, PageBreak, Image, Spacer,
Paragraph, Table, TableStyle, )
from reportlab.lib import colors

from django.shortcuts import render
from eventos.models import evento,tipoInforme,trazabilidadInformes
from usuarios.models import usuario
from usuarios.models import razonCambio

import base64

# llamar a los modelos de la BD
from eventos.models import evento, estadoEvento, categoriaEvento
from prestamos.models import prestamo, implemento, estadoPrestamo
from usuarios.models import usuario
from django.db.models import Count

# llamar a las librerias para obtener la fecha
from datetime import datetime, timedelta
from datetime import timezone as datetimeTimeZone
from django.utils import timezone
from django.utils import timezone as djangoTimeZone

#Importaciones para enviar el correo
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives

from prestamos.models import edificio
from usuarios.models import usuario
import base64
from functools import wraps

# Create your views here.
#######################LOGICA PARA CREAR EVENTOS#######################################

def mostrar_crear_evento(request):
    categorias = categoriaEvento.objects.all()
    edificios = edificio.objects.all()
    roles_count = request.user.roles.count()
    mensaje = request.GET.get('mensaje', '')
    datos_ingresados = request.session.pop('datos_ingresados', {})  # Obtener los datos ingresados por el usuario de la sesión
    return render(request, 'crearEvento.html', {'categorias': categorias, 'edificios':edificios, 'mensaje':mensaje, 'datos': datos_ingresados,'roles_count':roles_count})

def procesar_crear_evento(request):
    try:
        if request.method == "POST":
            #validar que el formato del archivo sea solamente de imágen
            if 'archivo' not in request.FILES:
                mensaje = 'No se ha subido ningún archivo.'
            else:
                archivo = request.FILES['archivo']
                max_size = 2 * 1024 * 1024  # 2MB
                
                # Verificar el tipo de archivo
                if not archivo.content_type.startswith('image/'):
                    mensaje = 'Solo se permiten archivos de imagen.'
                    #Verificar el tamaño del archivo
                elif archivo.size > max_size:
                    mensaje = 'El archivo es demasiado grande. El tamaño máximo permitido es 2MB.'
                else:
                    #crear el evento
                    fechaHoraCreacion = datetime.now().replace(second=0, microsecond=0)
                    administradorBienestarId =  usuario.objects.get(numeroDocumento=request.user.numeroDocumento)
                    nombreEvento = request.POST.get("nombreEvento")
                    categoriaEvento_ = int(request.POST.get("categoria"))
                    cat_Evento = categoriaEvento.objects.get(pk=categoriaEvento_)
                    organizador = request.POST.get("organizador")
                    fechaHoraEvento = request.POST.get("fechaHoraEvento")
                    fechaHoraFinEvento = request.POST.get("fechaHoraFinEvento")
                    edificioId_ = int(request.POST.get("edificio"))
                    edificio_ = edificio.objects.get(pk=edificioId_)
                    lugar = request.POST.get("lugar")
                    descripcion = request.POST.get("descripcion")
                    aforo = int(request.POST.get("aforo"))

                   
                    # Almacenar los datos ingresados por el usuario en la sesión
                    request.session['datos_ingresados'] = request.POST.dict()

                    
                     # Validar que la fechaHoraEventoFinal sea mayor que fechaHoraEvento
                    if fechaHoraFinEvento <= fechaHoraEvento:
                        mensaje = 'La fecha y hora de finalización debe ser mayor que la fecha y hora de inicio.'
                        return redirect(reverse("mostrar_crear_evento") + f'?mensaje={mensaje}')
                    
                    # Verificar si hay un evento programado en el mismo edificio, lugar y fechaHora
                    eventos_existentes = evento.objects.filter(
                        edificio_id=edificio_, lugar=lugar
                    ).filter(
                        fechaHoraEvento__lt=fechaHoraFinEvento,  # El evento existente comienza antes de que termine el nuevo evento
                        fechaHoraEventoFinal__gt=fechaHoraEvento    # El evento existente termina después de que comience el nuevo evento
                    )
                    if eventos_existentes.exists():
                        mensaje = 'Ya hay un evento programado en este lugar y fecha. Por favor, elige otro lugar o fecha.'
                    else:
                        # Leer los datos binarios del archivo
                        datos_binarios = archivo.read()

                        evento_ = evento(
                        fechaHoraCreacion=fechaHoraCreacion,
                        numeroDocumento_AdministradorBienestar=administradorBienestarId,
                        nombreEvento=nombreEvento,
                        categoriaEvento_id=cat_Evento,
                        organizador=organizador,
                        fechaHoraEvento=fechaHoraEvento,
                        fechaHoraEventoFinal=fechaHoraFinEvento,
                        edificio_id=edificio_,
                        lugar=lugar,
                        flyer=datos_binarios,
                        descripcion=descripcion,
                        aforo=aforo
                        )

                        #Trazabilidad eventos
                        idRazonCambio = razonCambio.objects.get(pk=16) #El admin bienestar crea un evento
                        evento_._change_reason = idRazonCambio
                        evento_.save()

                        #Asignación del estado PROGRAMADO
                        idRazonCambio = razonCambio.objects.get(pk=17) #Se le asigna el estado de PROGRAMADO
                        evento_._change_reason = idRazonCambio
                        evento_.estadoEvento.add(evento_.idEvento, 1)

                        mensaje = 'Evento creado exitosamente!'
                        request.session.pop('datos_ingresados', None)
                        return redirect(reverse("mostrar_crear_evento")+ f'?mensaje={mensaje}')

    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}"
            return redirect(reverse("mostrar_crear_evento")+ f'?mensaje={mensaje}')

    return redirect(reverse("mostrar_crear_evento")+ f'?mensaje={mensaje}')

#######################LOGICA PARA LISTA DE EVENTOS#######################################
#Muestra la lista de todos los eventos a los que el estudiante se puede inscribir
def mostrar_listaEventos(request):
    eventos = evento.objects.filter(estadoEvento = "1").order_by('fechaHoraEvento')
    roles_count = request.user.roles.count()
    for evento_ in eventos:
        evento_.imagen_base64 = base64.b64encode(evento_.flyer).decode('utf-8')  # Convertir la imagen a base64
    return render(request, 'listaEventos.html', {'eventos': eventos,'roles_count':roles_count})

#muestra el resumen del evento que el estudiante de click y al cual el estudiante puede inscribirse
def mostrar_asistirEvento(request, evento_id):
    evento_ = get_object_or_404(evento, idEvento=evento_id)
    imagen_base64 = base64.b64encode(evento_.flyer).decode('utf-8')
    context = {
        'evento_id': evento_id,
        'nombre_evento': evento_.nombreEvento,
        'organizador': evento_.organizador,
        'categoria': evento_.categoriaEvento_id.nombreCategoriaEvento,
        'fecha_hora_evento': evento_.fechaHoraEvento,
        'lugar': evento_.lugar,
        'descripcion_evento': evento_.descripcion,
        'imagen_base64': imagen_base64
    }
    return render(request, 'asistirEvento.html', context)

def guardar_informacionInscripcion(request,evento_id):
    numeroDocumentoUser = request.user.numeroDocumento
    usuario_ = usuario.objects.get(numeroDocumento=numeroDocumentoUser)
    evento_ = evento.objects.get(idEvento=evento_id)

    ###Logica para la validación de no poder inscribirse a otro evento en el mismo horario.
    fecha_evento = evento_.fechaHoraEvento
    evento1 = evento.objects.filter(fechaHoraEvento = fecha_evento, asistentes= numeroDocumentoUser).exclude(idEvento=evento_id)

    if evento1.exists(): 
        print("No se puede inscribir a este evento por que se cruza con otros eventos en el mismos horario")

        mensaje = f"No se puede inscribir a este evento por que se cruza con otro eventos en el mismo horario" # solo se le pasaria el mensaje en la URL 
        return redirect(reverse('paginaPrincipal_estudiante') + f'?mensaje={mensaje}')
    else:
 
        #Logica para verificar que el usuario no este inscrito ya en este evento
        if not evento_.asistentes.filter(numeroDocumento=numeroDocumentoUser).exists():
            #Trazabilidad Eventos
            idRazonCambio = razonCambio.objects.get(pk=20) #Estudiante se inscribe a un evento
            evento_._change_reason = idRazonCambio
            evento_.asistentes.add(usuario_)  # Establece los asistentes del evento como el usuario dado
            #evento_.save()  # Guarda el evento actualizado
            print("El usuario fue agregado")
            Proceso_enviarCorreo_inscripcionExitosa(numeroDocumentoUser,evento_id)
            return render(request, 'inscripcionExitosa.html')
        
        else:
            print("El usuario ya esta inscrito en este evento")
            mensaje = f"El usuario ya esta inscrito en este evento"
            return redirect(reverse('paginaPrincipal_estudiante') + f'?mensaje={mensaje}')
    
def Proceso_enviarCorreo_inscripcionExitosa(numeroDocumento,evento_id):
    try: 
        # obtener el correo del usuario
        usuarioObject = usuario.objects.get(numeroDocumento = numeroDocumento)
        correoUsuario = usuarioObject.correoInstitucional
        # no se verifica si el correo ingresado existe pues para llamar a este metodo ya deberia haberse verificado esto    

        #Datos del evento para enviar por correo
        evento_ = get_object_or_404(evento, idEvento=evento_id)
        imagen_base64 = base64.b64encode(evento_.flyer).decode('utf-8')
        nombreEvento = evento_.nombreEvento
        nombreLugar = evento_.lugar
        fechaEvento = evento_.fechaHoraEvento

        #El correo necesita un asunto, mensaje que se quiere enviar, quien lo envia, y los correos a los que se quiere enviar
        subject = "Tu inscripción fue un exito"
        message = ""
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [correoUsuario]

        #Generamos un html para que el correo que se envia sea más vistoso y no solo texto plano
        context = {
                    "nombreEstudiante": f"{usuarioObject.nombres.strip()} {usuarioObject.apellidos.strip()}",
                    "numeroDocumentoEstudiante":numeroDocumento,
                    "nombreEvento":nombreEvento,
                    "nombreLugar":nombreLugar ,
                    "fechaEvento":fechaEvento ,
                    "imagen_base64":imagen_base64

                }
        #Renderizamos el template html
        template = get_template("SendMessageEmailInscripcionEvento.html")
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

#######################LOGICA PARA GENERAR INFORMES#######################################

# Función para mostrar la vista principal de la sección de informes 
def mostrar_vista_informes(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    eventos = evento.objects.all()
    roles_count = request.user.roles.count()
    contexto = { # pasarle el contexto de lo que haya
                'mensaje': mensaje,
                'eventos': eventos,
                'roles_count':roles_count
            }
    # retornar la URL
    return render(request, 'vistaPrincipal_informes.html', contexto)

#----------------------- PROCESAR los formularios de reportes ------------------------------------------
# funcion para procesar informe prestamos 
def procesar_informe_prestamos(request):
    try:
        if request.method == "POST":
            # Obtener los datos del formulario
            fechaInicio = request.POST.get('fechaInicio')
            fechaFin = request.POST.get('fechaFin')
            nombreImplemento = request.POST.get('nombreImplemento', "")
            

            # LLamar a la URL que hace el informe 
            try:
                mensaje = "Se esta procesando el informe de prestamos "

                # pasar a la URL los parametros unos como argumentos y otros como cadena de mensaje 
                cadenaURLParametros = f'?mensaje={mensaje}&fechaInicio={fechaInicio}&fechaFin={fechaFin}&nombreImplemento={nombreImplemento}'
                return redirect(reverse("DescargarInforme_prueba", args=["Informe_prestamos", 1])+ f'{cadenaURLParametros}')   
            
            except Exception as e:

                mensaje = f"ERROR creando el informe {str(e)}" # solo se le pasaria el mensaje en la URL 
                return redirect(reverse("mostrar_vista_informes")+ f'?mensaje={mensaje}')  
    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}" # solo se le pasaria el mensaje en la URL 
            return redirect(reverse("mostrar_vista_informes")+ f'?mensaje={mensaje}')   


# funcion para procesar formulario informe eventos 
def procesar_informe_eventos(request):
    try:
        if request.method == "POST":
            # Obtener los datos del formulario
            fechaInicio = request.POST.get('fechaInicio')
            fechaFin = request.POST.get('fechaFin')
            lugarEvento = request.POST.get('lugarEvento', "")
            opciones_seleccionadas = request.POST.getlist('opciones', "")
        
            # LLamar a la URL que hace el informe 
            try:
                mensaje = "Se esta procesando el informe de eventos"

                # pasar a la URL los parametros unos como argumentos y otros como cadena de mensaje 
                cadenaURLParametros = f'?mensaje={mensaje}&fechaInicio={fechaInicio}&fechaFin={fechaFin}&lugarEvento={lugarEvento}&opciones_seleccionadas={opciones_seleccionadas}'
                return redirect(reverse("DescargarInforme_prueba", args=["Informe_eventos", 2])+ f'{cadenaURLParametros}')   
            
            except Exception as e:

                mensaje = f"ERROR creando el informe {str(e)}" # solo se le pasaria el mensaje en la URL 
                return redirect(reverse("mostrar_vista_informes")+ f'?mensaje={mensaje}')  
    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}" # solo se le pasaria el mensaje en la URL 
            return redirect(reverse("mostrar_vista_informes")+ f'?mensaje={mensaje}')   


# procesar formulario informe asistencia
def procesar_informe_asistencia(request):
    try:
        if request.method == "POST":
            # Obtener los datos del formulario
            idEvento = int(request.POST.get('selectEvento'))
            print(idEvento)
            #lugarEvento = request.POST.get('lugarEvento')
            #nombreEvento = request.POST.get('nombreEvento')

            # LLamar a la URL que hace el informe 
            try:
                mensaje = "Se esta procesando el informe de asistencia "

                # pasar a la URL los parametros unos como argumentos y otros como cadena de mensaje 
                cadenaURLParametros = f'?mensaje={mensaje}&idEvento={idEvento}'
                #&lugarEvento={lugarEvento}&nombreEvento={nombreEvento}
                return redirect(reverse("DescargarInforme_prueba", args=["Informe_asistencia", 3])+ f'{cadenaURLParametros}')   
            
            except Exception as e:

                mensaje = f"ERROR creando el informe {str(e)}" # solo se le pasaria el mensaje en la URL 
                return redirect(reverse("mostrar_vista_informes")+ f'?mensaje={mensaje}')  
    except Exception as e:
            mensaje = f"Ocurrió un error: {str(e)}" # solo se le pasaria el mensaje en la URL 
            return redirect(reverse("mostrar_vista_informes")+ f'?mensaje={mensaje}')   


#----------------------- PROCESAR LA descarga del PDF  ------------------------------------------

# Función para la descarga del PDF
def descarga_reportes(request,nombreArchivoReporte:str,numeroReporte:int ):
    """_summary_ 
    \n este metodo es para generar un responseHtml que sea un pdf y se descargue al ingresar a la URL. \n
    Args:
        nombreArchivoReporte (str): Pasado por la URL, es el nombre que se le dara al archivo pdf. \n
        numeroReporte (int): Pasado por la URL: 
        \n\t\t 1 <-- Reporte de prestamos. 
        \n\t\t 2 <-- Reporte de eventos. 
        \n\t\t 3 <-- Reporte de asistencia. \n

    """
    # crear la respuesta para que el sistema sepa que es un pd
    response = HttpResponse(content_type='application/pdf')

    # esto para que el archivo sea directamente descargado desde el navegador 
    response['Content-Disposition'] = f'attachment; filename= Reporte_ZenUN_{nombreArchivoReporte}.pdf'

    # Crear el Objeto PDF, usando BytesIO; buffer espacio temporal de memoria fisica
    buffer = BytesIO()
    lienzo = canvas.Canvas(buffer, pagesize=A4) # pagesize = (21cm, 29.7cm) or (595, 842)

    ## INICIO Contenido pdf con reportlab

    if numeroReporte == 1:
        # obtener lo que se paso como mensajes por la url 
        fechaInicio = request.GET.get('fechaInicio')
        fechaFin = request.GET.get('fechaFin')
        nombreImplemento = request.GET.get('nombreImplemento') 
        generarCanvas_Reporte_prestamo(lienzo, fechaInicio, fechaFin, nombreImplemento)  

    elif numeroReporte ==2:
        # obtener lo que se paso como mensajes por la url 
        fechaInicio = request.GET.get('fechaInicio')
        fechaFin = request.GET.get('fechaFin')
        lugarEvento = request.GET.get('lugarEvento')
        opciones_seleccionadas = request.GET.get("opciones_seleccionadas")
        # print(f"\n\n{fechaInicio}\n")
        generarCanvas_Reporte_Eventos(lienzo, fechaInicio, fechaFin, lugarEvento, opciones_seleccionadas)

    elif numeroReporte ==3:
        # obtener lo que se paso como mensajes por la url 
        idEvento = request.GET.get('idEvento')
        print(idEvento)
        #lugarEvento = request.POST.get('lugarEvento')
        #nombreEvento = request.POST.get('nombreEvento')
        generarCanvas_Reporte_Asistencia(lienzo, idEvento)

    else:
        buffer.close() # Cerrar buffer
        mensaje = f"El numero de reporte no es correcto, es 1, 2 o 3" 
        return redirect(reverse("mostrar_vista_informes")+ f'?mensaje={mensaje}')  
        

    ## FIN de de contenido pdf con reportlab

    # guardar pdf
    lienzo.save()
    # obtener el valor de BytesIO y escribirlo en la respuestaHttp
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return(response)


#----------------------- CREAR los REPORTES con reportlab ------------------------------------------
# Reporte prestamo 
def generarCanvas_Reporte_prestamo(lienzo:canvas.Canvas, fechaInicio, fechaFin, nombreImplemento=""):
    ##----------------HEADER ---------------------------------
        #header-titulo
    lienzo.setLineWidth(.3)
    lienzo.setFont('Helvetica', 22)
            # X desde el lad IZQ cuanto mover a la DER
            # y desde al lad ABJ cuanto mover ARRIBA
        # header-subtitulo
    lienzo.drawString(x=30, y=750,text='ZenUN')
    lienzo.setFont('Helvetica', 12)


    lienzo.drawString(30, 730, "Reporte PRESTAMOS")
        # header-hora
    hora_inicio_reserva = djangoTimeZone.now() + timedelta(hours=-5)
    fecha_formateada = hora_inicio_reserva.strftime('%Y-%m-%d %H:%M:%S') # Formatear la fecha y hora

    lienzo.setFont("Helvetica-Bold", 12)
    lienzo.drawString(350, 750, f"Fecha Reporte: {fecha_formateada}")
    
    ## --------------ARRAY DE DATOS PARA LAS TABLAS ----------------
    data = []   # Datos de la tabla se pasan mediante un array de arrays 

    ## ------------------ MODIFICAR OBJETOS FECHA -------------------
    # print(f"{fechaInicio}, {fechaFin}")
    # objeto_fechaInicio = datetime.strptime(fechaInicio, '%Y-%m-%d')   # Asi se crea un obj. datetime  pero sin zona horaria
    
    objeto_fechaInicio = datetime.strptime(fechaInicio, '%Y-%m-%d').replace(tzinfo=datetimeTimeZone.utc)                                            # pero la BD los objetos fecha tienen zona horario
    objeto_fechaFinal = (datetime.strptime(fechaFin, '%Y-%m-%d')  + timedelta(days=1) - timedelta(seconds=1)).replace(tzinfo=datetimeTimeZone.utc)  # para que quede en 23:59:59 de ese dia

    ## ------------------- PRIMERA TABLA------------------------------
    
    # SACAR DATOS BD 
    BDDatos = []                                                                                                          # es un array para guardar el contenido de la tabla sin estilo 
    prestamos_implemento = prestamo.objects.select_related('idImplemento', "estadoPrestamo", "estudianteNumeroDocumento") # consulta
    
    if nombreImplemento != "":
        for nuevaTabla in prestamos_implemento:
            # Ingresar los datos que cumplan los filtros NombreImp. y fechas
            if((nuevaTabla.idImplemento.nombreImplemento == nombreImplemento) and (objeto_fechaInicio <= nuevaTabla.fechaHoraCreacion <= objeto_fechaFinal)):
                row = [ 
                    nuevaTabla.idPrestamo,                                    #idPrestamo
                    nuevaTabla.estudianteNumeroDocumento.correoInstitucional, #estudianteCorreo
                    nuevaTabla.idImplemento.nombreImplemento,                 # nombreImplemento
                    nuevaTabla.fechaHoraCreacion,                             #fechaInicioPrestamo
                    nuevaTabla.estadoPrestamo.nombreEstado                    #estadoPrestamo
                ]
                BDDatos.append(row)
            else:
                pass
    else:
        for nuevaTabla in prestamos_implemento:
            # Ingresar los datos que cumplan el filtro de fecha 
            if((objeto_fechaInicio <= nuevaTabla.fechaHoraCreacion <= objeto_fechaFinal)):
                row = [ 
                    nuevaTabla.idPrestamo,                                    #idPrestamo
                    nuevaTabla.estudianteNumeroDocumento.correoInstitucional, #estudianteCorreo
                    nuevaTabla.idImplemento.nombreImplemento,                 #nombreImplemento
                    nuevaTabla.fechaHoraCreacion,                             #fechaInicioPrestamo
                    nuevaTabla.estadoPrestamo.nombreEstado                    #estadoPrestamo
                ]
                BDDatos.append(row)
            else:
                pass

    
    #----- CREACION ESTILOS---------
    # Llamar a los Estilos
    styles = getSampleStyleSheet() # nos da una lista de estilos a escoger de la biblioteca
    
    # Creacion estilo <-- header tabla
    styleHeaderTable = ParagraphStyle('styleHeaderTable',  
        parent= styles['Heading1'],
        fontSize=10, 
        alignment=1  # Center alignment
    )

    # Creacion estilo <-- contenido tabla   
    styleN = ParagraphStyle('p',  
        parent=styles["BodyText"],
        fontSize=7, 
        alignment=1  # Center alignment
    )


    # Títulos de las columnas (primera fila)
    # Paragraph <-- le da estilo a un texto 
    #                       texto           , estilo 
    idPrestamo      = Paragraph('idPrestamo', styleHeaderTable)
    alumnoCorreo    = Paragraph('alumnoCorreo', styleHeaderTable)
    nombreImplemento= Paragraph('nombreImplemento', styleHeaderTable)
    fechaPrestamo   = Paragraph('fechaPrestamo inicio', styleHeaderTable)
    estadoPrestamo  = Paragraph('estadoPrestamo', styleHeaderTable)

    # Pasar datos al (array data)
    data.append([idPrestamo, alumnoCorreo, nombreImplemento, fechaPrestamo, estadoPrestamo])


    # Variable HIGH para saber cuanto mover la tabla relativamente hacia arriba 
    high = 700

    # ¿Cuantos prestamos se hicieron en la consulta?
    prestamoTotalConsultaBD1 = len(BDDatos)


    # Agregar (datos BD) al (array data)
    for datoBd in BDDatos:
        row = []
        for item in datoBd:
            # Poner estilo a ese dato
            dato = Paragraph(str(item), styleN)
            row.append(dato)

        high -= 18
        data.append(row)

        # CAMBIAR PAGINA, si se pasa de un numero de datos o high especifico 
        if high < 360:
            # Poner tabla en el CANVAS
            crearTablaReportLab(data, lienzo, 5, valorHigh= 700, PonerDesdeLimiteAbajo = True, alturaRow= 18, anchoCol= 3.7)

            # Cambiar el high a 750, ya que alcanzo limite pagina 
            high = 750
            
            # Limpiar datos del array de datos de la tabla 
            data.clear() 

            # Agregar los (nombres Columnas) a la tabla otra vez 
            data.append([idPrestamo, alumnoCorreo, nombreImplemento, fechaPrestamo, estadoPrestamo])

    # PARA LOS DATOS RESTANTES, si falto dibujar una parte de la tabla
    crearTablaReportLab(data, lienzo, 5, valorHigh=600, PonerDesdeLimiteAbajo = False, alturaRow= 20, anchoCol= 3.7)

    ##------------------ CUANTOS PRESTAMOS ----------------------------------
    lienzo.setFont('Helvetica', 10)
    lienzo.drawString(x=30, y=750,text=f'''1.5  ¡TOTAL PRESTAMOS, CON FILTROS!, ¿Cuántos prestamos hay?:''')
    lienzo.setFont('Helvetica-Bold', 15)
    lienzo.drawString(x=370, y=750,text=f'''{prestamoTotalConsultaBD1} ''')
    lienzo.setFont('Helvetica', 10)
    lienzo.drawString(x=30, y=735,text='---------------------------------------------------------------------------------------------------------------------------')

    ##------------------ SEGUNDA TABLA ----------------------------------
    lienzo.drawString(x=30, y=720,text='2. ¡TOTAL, SIN FILTROS!, ¿Cuántas veces fueron prestados cada implemento TABLA?:')
    lienzo.setFont('Helvetica', 10)

    # resetear array de data
    data = []

    # resetar array
    BDDatos = []
    numeroTotalPrestamos = 0

    # CONSULTA  2 BD 
    resultadoTabla = prestamo.objects.values('idImplemento__nombreImplemento').annotate(contadorPrestamo=Count('idPrestamo')).order_by('idImplemento__nombreImplemento')
    
    for filaResultado in resultadoTabla:
        row = [ 
            filaResultado['idImplemento__nombreImplemento'],
            filaResultado['contadorPrestamo']
        ]
        numeroTotalPrestamos += filaResultado['contadorPrestamo']
        BDDatos.append(row)
        # print(row)

    # Títulos de las columnas (primera fila); los estilos ya estan creados entonces solo colocar la tabla
    nombreImplemento   = Paragraph('nombreImplemento', styleHeaderTable)
    contadorPrestamo   = Paragraph('contadorPrestamo', styleHeaderTable)

    # Pasar datos al (array data)
    data.append([nombreImplemento, contadorPrestamo])

    # poner un nuevo HIGH 
    high = 750
    numeroDatosContenidoRecorrido = 0

    # Agregar (datos BD) al (array data)
    for datoBd in BDDatos:
        row = []
        for item in datoBd:
            # Poner stilo al dato 
            dato = Paragraph(str(item), styleN)
            row.append(dato)

        high -= 12 # mas corto por que la altura de las filas es mas corta
        data.append(row)
        numeroDatosContenidoRecorrido += 1

        # PARA CAMBIAR DE PÁGINA SI YA HAY MUCHOS ELEMENTOS 
        if high < 360:
            # Poner tabla en el CANVAS
            crearTablaReportLab(data, lienzo, 2, valorHigh=650, PonerDesdeLimiteAbajo=False, alturaRow= 18, anchoCol= 6.5)

            # cambiar el high a 750, ya que alcanzo limite pagina 
            high = 750

            # resetear el (array data)
            data.clear()

            # agregar el header a la tabla otra vez 
            data.append([nombreImplemento, contadorPrestamo])

    # PARA LOS DATOS RESTANTES, si falto dibujar una parte de la tabla
    crearTablaReportLab(data, lienzo, 2, valorHigh=650,PonerDesdeLimiteAbajo=False, alturaRow= 15, anchoCol= 6.5)

    ##---------------------- NUMERO TOTAL DE TABLA 2  -------------------------------------
    lienzo.setLineWidth(.3)
    lienzo.drawString(x=30, y=750,text=f'3.  ¡TOTAL, SIN FILTROS!, ¿Cuántas veces fueron prestados los implemento VALOR?: ')
    lienzo.setFont('Helvetica-Bold', 15)
    lienzo.drawString(x=500, y=750,text=f'''{numeroTotalPrestamos} ''')
    #Trazabilidad informe de préstamos, idInforme 3
    tipo_informe = tipoInforme.objects.get(pk=3)
    nuevo_informe = trazabilidadInformes(
        fechaGeneracionInforme = fecha_formateada,
        tipoInforme = tipo_informe
    )
    nuevo_informe.save()
    return None


def crearTablaReportLab(data, lienzo:canvas.Canvas, numeroColumnas:int, valorHigh=650, PonerDesdeLimiteAbajo=True, alturaRow=18, anchoCol=3.7 ):
    """_summary_Este metodo es para crear una tabla pasando unos datos y si necesita pasar de pagina en el PDF \n

    Args:\n
        \n\t\t data (array): Array de arrays: cada sub array es una fila 
        \n\t\t lienzo (canvas.Canvas): lienzo canvas
        \n\t\t numeroColumnas (int): numero de columnas de la tabla
        \n\t\t valorHigh (int, optional): valor para desde abajo subir la tabla. Defaults to 650.
        \n\t\t PonerDesdeLimiteAbajo (bool, optional): se pone en 100 la altura de la tabla desde abajo. Defaults to True.
        \n\t\t alturaRow (int, optional): altura de la fila. Defaults to 18.
        \n\t\t anchoCol (float, optional): El ancho de la columna. Defaults to 3.7.\n
       
    """
    high = valorHigh - (len(data) * alturaRow)

    # crear la tabla  y estilizar la tabla
    anchoColumnas = [anchoCol * cm] * numeroColumnas
    table = Table(data, colWidths=anchoColumnas)
    table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    # Tamaño del PDF
    ancho, alto = A4

    # Ajuste de coordenadas para evitar que la tabla se dibuje fuera de los márgenes
    table.wrapOn(lienzo, ancho, alto)
    if(PonerDesdeLimiteAbajo):
        table.drawOn(lienzo, 30, 100) 
    else:
        table.drawOn(lienzo, 30, high) 
    
    # Cambiar de página si es necesario
    lienzo.showPage()
    return(None)



# Reporte Eventos 
def generarCanvas_Reporte_Eventos(lienzo:canvas.Canvas, fechaInicio, fechaFin, lugarEvento, opciones_seleccionadas):
    ## OJO opciones_seleccionadas ES UNA ARRAY 

    ## header
        #header-titulo
    lienzo.setLineWidth(.3)
    lienzo.setFont('Helvetica', 22)
            # X desde el lad IZQ cuanto mover a la DER
            # y desde al lad ABJ cuanto mover ARRIBA
        # header-subtitulo
    lienzo.drawString(x=30, y=750,text='ZenUN')
    lienzo.setFont('Helvetica', 12)
    lienzo.drawString(30, 730, "Reporte EVENTOS")
        # header-hora
    lienzo.setFont("Helvetica-Bold", 12)
    lienzo.drawString(480, 730, "fechaDeAhora")   
    #Trazabilidad informe de Eventos, idInforme 1 
    tipo_informe = tipoInforme.objects.get(pk=1)
    nuevo_informe = trazabilidadInformes(
        fechaGeneracionInforme = timezone.now(),
        tipoInforme = tipo_informe
    )
    nuevo_informe.save()
    return(None)

    

    
# Reporte Asistencia
def generarCanvas_Reporte_Asistencia(lienzo:canvas.Canvas, idEvento):

    ## header
        #header-titulo
    lienzo.setLineWidth(.3)
    lienzo.setFont('Helvetica', 22)
            # X desde el lad IZQ cuanto mover a la DER
            # y desde al lad ABJ cuanto mover ARRIBA
        # header-subtitulo
    lienzo.drawString(x=30, y=750,text='ZenUN')
    lienzo.setFont('Helvetica', 12)
    lienzo.drawString(30, 730, "Reporte ASISTENCIA")

        # header-hora
    hora_inicio_reserva = djangoTimeZone.now() + timedelta(hours=-5)
    fecha_formateada = hora_inicio_reserva.strftime('%Y-%m-%d %H:%M:%S') # Formatear la fecha y hora

    lienzo.setFont("Helvetica-Bold", 12)
    lienzo.drawString(350, 750, f"Fecha Reporte: {fecha_formateada}")
   

    ## --------------ARRAY DE DATOS PARA LAS TABLAS ----------------
    data = []   # Datos de la tabla se pasan mediante un array de arrays 
    # SACAR DATOS BD 
    BDDatos = []    
    eventoSeleccionado = evento.objects.get(pk=idEvento)
    inscritos = eventoSeleccionado.asistentes.all()
    for persona in inscritos:
        row = [
            persona.apellidos,
            persona.nombres,
            persona.correoInstitucional,
            persona.numeroDocumento,
            ""
        ]
        BDDatos.append(row)

    #Ordena la lista de inscritos por orden alfabético
    BDDatos.sort(key = lambda x: (x[0].lower(),x[1].lower(),x[3],x[4])) #Primero intenta ordenas por el apellido, si coincide, orden por nombre y así sucesivamente

     ## --------------DATOS DEL EVENTO QUE SE GENERA ----------------
   
    nombreEvento = eventoSeleccionado.nombreEvento
    organizador = eventoSeleccionado.organizador
    fechaEvento = eventoSeleccionado.fechaHoraEvento
    aforo = eventoSeleccionado.aforo
    asistentesInscritos = len(BDDatos)

    lienzo.setFont('Helvetica', 10)
    lienzo.drawString(30, 700, "Nombre evento: "+ nombreEvento)
    lienzo.drawString(30, 685, "Organizador: "+ organizador)
    lienzo.drawString(30, 670, "Fecha evento: "+ fechaEvento.strftime('%Y-%m-%d %H:%M:%S'))
    lienzo.drawString(30, 655, "Aforo: "+ str(aforo))
    lienzo.drawString(30, 640, "Inscritos: "+ str(asistentesInscritos))
    
    #----- CREACION ESTILOS---------
    # Llamar a los Estilos
    styles = getSampleStyleSheet() # nos da una lista de estilos a escoger de la biblioteca
    
    # Creacion estilo <-- header tabla
    styleHeaderTable = ParagraphStyle('styleHeaderTable',  
        parent= styles['Heading1'],
        fontSize=10, 
        alignment=1  # Center alignment
    )

    # Creacion estilo <-- contenido tabla   
    styleN = ParagraphStyle('p',  
        parent=styles["BodyText"],
        fontSize=7, 
        alignment=1  # Center alignment
    )

    # Títulos de las columnas (primera fila)
    # Paragraph <-- le da estilo a un texto 
    #                       texto           , estilo 
    apellidos           = Paragraph('Apellidos', styleHeaderTable)
    nombres             = Paragraph('Nombres', styleHeaderTable)
    correoInstitucional = Paragraph('Correo Institucional', styleHeaderTable)
    numeroDocumento     = Paragraph('Número Documento', styleHeaderTable) 
    firma               = Paragraph('Firma', styleHeaderTable) 

    # Pasar datos al (array data)
    data.append([apellidos, nombres, correoInstitucional, numeroDocumento, firma])

     # Variable HIGH para saber cuanto mover la tabla relativamente hacia arriba 
    high = 700    

    # Agregar (datos BD) al (array data)
    for datoBd in BDDatos:
        row = []
        for item in datoBd:
            # Poner estilo a ese dato
            dato = Paragraph(str(item), styleN)
            row.append(dato)

        high -= 18
        data.append(row)

        # CAMBIAR PAGINA, si se pasa de un numero de datos o high especifico 
        if high < 360:
            # Poner tabla en el CANVAS
            crearTablaReportLab(data, lienzo, 5, valorHigh= 700, PonerDesdeLimiteAbajo = True, alturaRow= 18, anchoCol= 3.7)

            # Cambiar el high a 750, ya que alcanzo limite pagina 
            high = 750
            
            # Limpiar datos del array de datos de la tabla 
            data.clear() 

            # Agregar los (nombres Columnas) a la tabla otra vez 
            data.append([apellidos, nombres, correoInstitucional, numeroDocumento, firma])

    # PARA LOS DATOS RESTANTES, si falto dibujar una parte de la tabla
    crearTablaReportLab(data, lienzo, 5, valorHigh=600, PonerDesdeLimiteAbajo = False, alturaRow= 20, anchoCol= 3.7)

    """
    lienzo.drawString(100,100, eventoSeleccionado.nombreEvento)
    
    for personas in inscritos:
        lienzo.drawString(100,150, personas.correoInstitucional)
        print(personas.correoInstitucional)
        
    # header-hora
    lienzo.setFont("Helvetica-Bold", 12)
    lienzo.drawString(480, 730, "fechaDeAhora")
    """
    #Trazabilidad informe de Asistencia a eventos, idInforme 2
    tipo_informe = tipoInforme.objects.get(pk=2)
    nuevo_informe = trazabilidadInformes(
        fechaGeneracionInforme = fecha_formateada,
        tipoInforme = tipo_informe
    )
    nuevo_informe.save()
    return(None)

#######################LOGICA PARA CREAR EVENTOS#######################################
#Logica para cancelar la inscripción a un evento
def cancelar_inscripcionEvento(request):
    return render(request, 'asistirEvento.html')

#Logica para cancelar el vento

# def mostrar_cancelar_evento(request):
#     eventos = evento.objects.all().select_related('categoriaEvento_id', 'edificio_id').prefetch_related('estadoEvento')
#     eventos_info = []
#     for e in eventos:
#         estado = e.estadoEvento.first()  # Obtener el primer estado del evento
#         eventos_info.append({
#             'nombre': e.nombreEvento,
#             'organizador': e.organizador,
#             'fecha_hora': e.fechaHoraEvento,
#             'lugar': e.lugar,
#             'estado': estado.nombreEstadoEvento if estado else '',  # Obtener el nombre del estado o cadena vacía si no hay estado
#         })
#     return render(request, 'cancelarEvento.html', {'eventos_info': eventos_info})

def mostrar_cancelar_evento(request):
    # Filtrar los eventos que tienen el estado "Programado"
    eventos = evento.objects.filter(estadoEvento__nombreEstadoEvento='Programado').select_related('categoriaEvento_id', 'edificio_id').prefetch_related('estadoEvento')
    roles_count = request.user.roles.count()
    eventos_info = []
    for e in eventos:
        estado = e.estadoEvento.first()  # Obtener el primer estado del evento
        if estado and estado.nombreEstadoEvento == 'Programado':  # Filtrar solo los que tienen estado "Programado"
            eventos_info.append({
                'id':e.idEvento,
                'nombre': e.nombreEvento,
                'organizador': e.organizador,
                'fecha_hora': e.fechaHoraEvento,
                'lugar': e.lugar,
                'estado': estado.nombreEstadoEvento,
            })
    
    return render(request, 'cancelarEvento.html', {'eventos_info': eventos_info,'roles_count':roles_count})

def cancelar_evento(request, evento_id):
    evento_a_cancelar = get_object_or_404(evento, idEvento=evento_id)
    
    estado_cancelado = get_object_or_404(estadoEvento, nombreEstadoEvento='Cancelado')

    idRazonCambio = razonCambio.objects.get(pk=19) #Se quita el estado de programado al evento
    evento_a_cancelar._change_reason = idRazonCambio

    evento_a_cancelar.estadoEvento.clear()

    idRazonCambio = razonCambio.objects.get(pk=18) #Se le asigna el estado de CANCELADO al evento   
    evento_a_cancelar._change_reason = idRazonCambio

    evento_a_cancelar.estadoEvento.add(estado_cancelado)
    
    return redirect('mostrar_cancelar_evento')
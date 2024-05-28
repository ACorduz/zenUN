from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
# se va a utilizar la libreria reportLab para hacer los reportes
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm 

from django.shortcuts import render
from eventos.models import evento
import base64
# Create your views here.
#######################LOGICA PARA LISTA DE EVENTOS#######################################



#######################LOGICA PARA EL CASO DE USO ASISTIR EVENTO#######################################
#Muestra la lista de todos los eventos a los que el estudiante se puede inscribir
def mostrar_listaEventos(request):
    eventos = evento.objects.filter(estadoEvento = "1")
    for evento_ in eventos:
        evento_.imagen_base64 = base64.b64encode(evento_.flyer).decode('utf-8')  # Convertir la imagen a base64
    return render(request, 'listaEventos.html', {'eventos': eventos})

#######################LOGICA PARA ASISTIR A EVENTO#######################################
#muestra el resumen del evento que el estudiante de click y al cual el estudiante puede inscribirse
def mostrar_asistirEvento(request,evento_id):

    # Pasar los datos al contexto para que puedan ser renderizados y mostrados en el html
    context = {
        'evento_id': evento_id
        }

    print(evento_id)
    return render(request, 'asistirEvento.html', context)
  

#######################LOGICA PARA GENERAR INFORMES#######################################

# Función para mostrar la vista principal de la sección de informes 
def mostrar_vista_informes(request):
    mensaje = request.GET.get('mensaje', '')  # Obtener el mensaje de la URL, si está presente
    contexto = { # pasarle el contexto de lo que haya
                'mensaje': mensaje,
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
            idImplemento = request.POST.get('idImplemento')
            documentoEncargado = request.POST.get('documentoEncargado')

            # LLamar a la URL que hace el informe 
            try:
                mensaje = "Se esta procesando el informe de prestamos "

                # pasar a la URL los parametros unos como argumentos y otros como cadena de mensaje 
                cadenaURLParametros = f'?mensaje={mensaje}&fechaInicio={fechaInicio}&fechaFin={fechaFin}&idImplemento={idImplemento}&documentoEncargado={documentoEncargado}'
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
            lugarEvento = request.POST.get('lugarEvento')

            # LLamar a la URL que hace el informe 
            try:
                mensaje = "Se esta procesando el informe de eventos"

                # pasar a la URL los parametros unos como argumentos y otros como cadena de mensaje 
                cadenaURLParametros = f'?mensaje={mensaje}&fechaInicio={fechaInicio}&fechaFin={fechaFin}&lugarEvento={lugarEvento}'
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
            idEvento = request.POST.get('idEvento')
            lugarEvento = request.POST.get('lugarEvento')
            nombreEvento = request.POST.get('nombreEvento')

            # LLamar a la URL que hace el informe 
            try:
                mensaje = "Se esta procesando el informe de asistencia "

                # pasar a la URL los parametros unos como argumentos y otros como cadena de mensaje 
                cadenaURLParametros = f'?mensaje={mensaje}&idEvento={idEvento}&lugarEvento={lugarEvento}&nombreEvento={nombreEvento}'
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
        idImplemento = request.GET.get('idImplemento')
        documentoEncargado = request.GET.get('documentoEncargado')
        generarCanvas_Reporte_prestamo(lienzo, fechaInicio, idImplemento, documentoEncargado)  

    elif numeroReporte ==2:
        # obtener lo que se paso como mensajes por la url 
        fechaInicio = request.GET.get('fechaInicio')
        fechaFin = request.GET.get('fechaFin')
        lugarEvento = request.GET.get('lugarEvento')
        # print(f"\n\n{fechaInicio}\n")
        generarCanvas_Reporte_Eventos(lienzo, fechaInicio, fechaFin, lugarEvento)

    elif numeroReporte ==3:
        # obtener lo que se paso como mensajes por la url 
        idEvento = request.POST.get('idEvento')
        lugarEvento = request.POST.get('lugarEvento')
        nombreEvento = request.POST.get('nombreEvento')
        generarCanvas_Reporte_Asistencia(lienzo, idEvento, lugarEvento, nombreEvento)

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
def generarCanvas_Reporte_prestamo(lienzo:canvas.Canvas, fechaInicio, idImplemento, documentoEncargado):
    ## header
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
    lienzo.setFont("Helvetica-Bold", 12)
    lienzo.drawString(480, 730, "fechaDeAhora")
    return(None)

# Reporte Eventos 
def generarCanvas_Reporte_Eventos(lienzo:canvas.Canvas, fechaInicio, fechaFin, lugarEvento):
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
    return(None)
    
# Reporte Asistencia
def generarCanvas_Reporte_Asistencia(lienzo:canvas.Canvas, idEvento, lugarEvento, nombreEvento):
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
    lienzo.setFont("Helvetica-Bold", 12)
    lienzo.drawString(480, 730, "fechaDeAhora")
    return(None)
#######################LOGICA PARA CREAR EVENTOS#######################################
def mostrar_crear_evento(request):
    return render(request, 'crearEvento.html')

    return render(request, 'asistirEvento.html')

#Logica para cancelar la inscripción a un evento
def cancelar_inscripcionEvento(request):
    return render(request, 'asistirEvento.html')
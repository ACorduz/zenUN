from django.shortcuts import render
from eventos.models import evento
import base64
# Create your views here.


#######################LOGICA PARA EL CASO DE USO ASISTIR EVENTO#######################################
#Muestra la lista de todos los eventos a los que el estudiante se puede inscribir
def mostrar_listaEventos(request):
    eventos = evento.objects.filter(estadoEvento = "1")
    for evento_ in eventos:
        evento_.imagen_base64 = base64.b64encode(evento_.flyer).decode('utf-8')  # Convertir la imagen a base64
    return render(request, 'listaEventos.html', {'eventos': eventos})

#muestra el resumen del evento que el estudiante de click y al cual el estudiante puede inscribirse
def mostrar_asistirevento(request):
    return render(request, 'asistirEvento.html')

#Logica para cancelar la inscripción a un evento
def cancelar_inscripcionEvento(request):
    return render(request, 'asistirEvento.html')
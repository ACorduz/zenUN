from django.shortcuts import render

# Create your views here.


#######################LOGICA PARA ASISTIR A EVENTO#######################################

def mostrar_asistirEvento(request):

    print("aja")
    
    return render(request, 'asistirEvento.html')
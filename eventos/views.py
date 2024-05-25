from django.shortcuts import render

# Create your views here.


#######################LOGICA PARA ASISTIR A EVENTO#######################################

#######################LOGICA PARA GENERAR INFORMES#######################################

""" Función que muestra la vista principal de la sección de informes """
def mostra_vista_informes(request):
    return render(request, 'vistaPrincipal_informes.html')
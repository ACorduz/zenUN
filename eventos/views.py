from django.shortcuts import render

# Create your views here.


#######################LOGICA PARA LISTA DE EVENTOS#######################################

def mostrar_listaEventos(request):
    eventos = [
        {
            "URL": "https://cdn.pixabay.com/photo/2024/02/26/19/39/monochrome-image-8598798_1280.jpg",
            "nombre": "Festival de Música",
            "descripción": "Un evento anual que reúne a artistas de todo el mundo para celebrar la música en todas sus formas."
        },
        {
            "URL": "https://cdn.pixabay.com/photo/2024/05/11/13/45/flowers-8754997_1280.jpg",
            "nombre": "Feria de Tecnología",
            "descripción": "Una exposición donde se presentan los últimos avances en tecnología y gadgets innovadores."
        },
        {
            "URL": "https://www.enjpg.com/img/2020/deadpool-1-500x281.png",
            "nombre": "Conferencia de Salud",
            "descripción": "Un evento dedicado a la promoción de la salud y el bienestar, con conferencias y talleres de expertos en la materia."
        }
    ]
    return render(request, 'listaEventos.html', {'eventos': eventos})

#######################LOGICA PARA ASISTIR A EVENTO#######################################

def mostrar_asistirevento(request):
    return render(request, 'listaEventos.html')
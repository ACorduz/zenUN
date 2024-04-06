from django import forms 

class FormularioContacto(forms.Form):

    email=forms.EmailField()

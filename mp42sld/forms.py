from django import forms

class linkform(forms.Form):
    link = forms.CharField(label='Link :', max_length=100)
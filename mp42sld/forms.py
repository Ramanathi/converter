from django import forms

class linkform(forms.Form):
    link = forms.CharField(label='Link :', max_length=100)
    bitrate = forms.DecimalField(min_value=20, max_value=120)
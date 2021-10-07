from django import forms

class linkform(forms.Form):
    link = forms.CharField(label='Link :', max_length=100)
    bitrate = forms.DecimalField(min_value=10, max_value=110)
    freq = forms.DecimalField(min_value=0.1, max_value=20)
    sensitivity = forms.DecimalField(min_value=1, max_value=100)
    intensity = forms.DecimalField(min_value=1, max_value=255)
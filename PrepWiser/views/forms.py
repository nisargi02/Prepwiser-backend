from django import forms
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result
    
class FileUploadForm(forms.Form):
    pdf_files=MultipleFileField()
    
    syllabus_file = forms.FileField(label="Upload Syllabus")

class MessageForm(forms.Form):
    message = forms.CharField(label='Your Message', max_length=1000)

class UploadFileForm(forms.Form):
    file = forms.FileField()


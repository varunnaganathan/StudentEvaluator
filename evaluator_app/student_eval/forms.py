# forms.py
from django import forms
from .models import University, UniversityCourse, UniversityCountry

class StudentForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    student_id = forms.CharField(max_length=20)
    documents = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    university = forms.ModelChoiceField(queryset=University.objects.all(), empty_label="Select a university")

    # These fields will be dynamically updated via JavaScript
    course = forms.ModelChoiceField(queryset=UniversityCourse.objects.none(), required=False, empty_label="Select a course")
    country = forms.ModelChoiceField(queryset=UniversityCountry.objects.none(), required=False, empty_label="Select a country")

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        if 'university' in self.data:
            try:
                university_id = int(self.data.get('university'))
                self.fields['course'].queryset = UniversityCourse.objects.filter(university_id=university_id).order_by('name')
                self.fields['country'].queryset = UniversityCountry.objects.filter(university_id=university_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['course'].queryset = UniversityCourse.objects.none()
                self.fields['country'].queryset = UniversityCountry.objects.none()
        
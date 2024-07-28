from django.forms import ModelForm
from student_eval.models import Application


class ApplicationForm(ModelForm):
    class Meta:
        model = Application
        fields = ['student', 'university', 'course']
        labels = {
            'student': 'Student',
            'university': 'University',
            'course': 'Course',
        }
        help_texts = {
            'student': 'Enter student',
            'university': 'Select the university',
            'course': 'Select the course',
        }
        error_messages = {
            'student': {
                'required': 'Please enter the student ID'
            },
            'university': {
                'required': 'Please select the university'
            },
            'course': {
                'required': 'Please select the course'
            }
        }
from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.template import loader

def index(request):
    context = {
        'title': 'Student Evaluation',
        'description': 'This is a simple student evaluation system.',
        'author': 'Django Team',
        'year' : 2021,
        'authenticated': False,
    }
    html_template = loader.get_template('index.html')
    return HttpResponse(html_template.render(context, request))


from django.shortcuts import render

def student_info(request):
    context = {
        "name": 'John Doe',
        'country': 'Nigeria',
        'age': 25,
        'course': 'Computer Science',
        'level': 300,
        'nationality': 'Nigerian',
        'email': 'john.doe@example.com',
        'phone': '+234-123-456-7890',
        'address': '123, Main Street, Lagos, Nigeria',
    }
    html_template = loader.get_template('components/student_info.html')
    return HttpResponse(html_template.render(context, request))


def academic(request):
    context = {
        "table": {
            "header": ["Requirement", "Qualification", "Review"],
            "data": 
            [
                ["GPA Score above 3.5", "3.8", "Pass"],
                ["Minimum 120 Credit Hours", "95", "Review Needed"],
                ["Coursework Completed", "Yes", "Pass"],
                ["Thesis Completed", "Not completed", "Fail"],
            ]
        },
        "documents": [
            {
                "title": "Transcript",
                "status": "Available"
            },
            {
                "title": "Course Registration",
                "status": "Available"
            },
            {
                "title": "Course Results",
                "status": "Available"
            },
            {
                "title": "Course Materials",
                "status": "Not Available"
            },
        ]
    }

    html_template = loader.get_template('components/academic.html')
    return HttpResponse(html_template.render(context, request))



def english(request):
    context = {}
    html_template = loader.get_template('components/english.html')
    return HttpResponse(html_template.render(context, request))
    

def visa(request):
    context = {}
    html_template = loader.get_template('components/visa.html')
    return HttpResponse(html_template.render(context, request))

def exceptions(request):
    context = {}
    html_template = loader.get_template('components/exceptions.html')
    return HttpResponse(html_template.render(context, request))


def app_notes(request):
    context = {}
    html_template = loader.get_template('components/app_notes.html')
    return HttpResponse(html_template.render(context, request))
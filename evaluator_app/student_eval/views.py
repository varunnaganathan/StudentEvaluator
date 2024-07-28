from django.http import HttpResponse, JsonResponse
from django.template import loader

from student_eval.forms import StudentForm
from student_eval.search_utils import (
    get_application_decision_table, 
    get_application_students_from_query,
    get_document_path
)
from student_eval.models import (
    Application,
    UniversityCountry,
    UniversityCourse
)

from django.shortcuts import get_object_or_404, redirect, render


def landing_page(request):
    context = {}
    html_template = loader.get_template('index.html')
    return HttpResponse(html_template.render(context, request))


def student_info(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    context = {
        'application': application,
    }
    html_template = loader.get_template('components/student_info.html')
    return HttpResponse(html_template.render(context, request))


def academic(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    context = get_application_decision_table(application, 'academic')
    html_template = loader.get_template('components/academic.html')
    return HttpResponse(html_template.render(context, request))


def english(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    context = get_application_decision_table(application, 'english')
    html_template = loader.get_template('components/english.html')
    return HttpResponse(html_template.render(context, request))
    

def work_experience(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    context = get_application_decision_table(application, 'work')
    html_template = loader.get_template('components/work_experience.html')
    return HttpResponse(html_template.render(context, request))


def approve_or_decline(request, application_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        page_name = request.POST.get('page_name')

        application = get_object_or_404(Application, id=application_id)

        context = get_application_decision_table(application, page_name)
        data = context['decision_data']
        if action == 'approve':
            if page_name == 'academic':
                application.academic_data = data
            elif page_name == 'english':
                application.english_data = data
            elif page_name == 'work':
                application.work_experience_data = data
            else:
                return JsonResponse({'error': 'Invalid request'}, status=400)

        elif action == 'decline':
            if page_name == 'academic':
                application.academic_data = data
            elif page_name == 'english':
                application.english_data = data
            elif page_name == 'work':
                application.work_experience_data = data
            else:
                return JsonResponse({'error': 'Invalid request'}, status=400)

        else:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        application.save()

        return redirect('student_info', application_id=application_id)

    return JsonResponse({'error': 'Invalid request'}, status=400)



def visa(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    context = {
        'application': application,
        'table': get_application_decision_table(application, 'work')
    }
    
    html_template = loader.get_template('components/visa.html')
    return HttpResponse(html_template.render(context, request))



def exceptions(request, application_id):
    context = {}
    html_template = loader.get_template('components/exceptions.html')
    return HttpResponse(html_template.render(context, request))


def app_notes(request, application_id):
    context = {}
    html_template = loader.get_template('components/app_notes.html')
    return HttpResponse(html_template.render(context, request))


def student_search(request):
    query = request.GET.get('query', '')
    if len(query) >= 3:
        results = get_application_students_from_query(query)
    else:
        results = []
    return JsonResponse(results, safe=False)


def search_result(request):
    if request.method == 'POST':
        student_str = request.POST.get('query', '')
        print(student_str)
        if student_str and ' | ' in student_str and student_str.split(' | ')[1].strip().isdigit():
            student_id = int(student_str.split(' | ')[1].strip())
            application = Application.objects.filter(student__student_id=student_id).first()
            context = {
                'application': application,
            }
            return render(request, 'student_application.html', context)        
    
    return JsonResponse({'error': 'Invalid request'}, status=400)



def create_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            # Process the form data
            # save student data and handle file uploads as needed
            return redirect('success')
    else:
        form = StudentForm()
    
    return render(request, 'create_student.html', {'form': form})


def load_courses_and_countries(request):
    university_id = request.GET.get('university')
    courses = UniversityCourse.objects.filter(university_id=university_id).order_by('name')
    countries = UniversityCountry.objects.filter(university_id=university_id).order_by('name')
    return JsonResponse({
        'courses': list(courses.values('id', 'name')), 
        'countries': list(countries.values('id', 'name'))
    })

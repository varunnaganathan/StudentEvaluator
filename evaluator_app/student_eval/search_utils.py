import ast
import os
from student_eval.models import *
from llm_evaluator import add_student_qualifications_decisions
from django.conf import settings

def get_application_students_from_query(query: str):
    applications = Application.objects.filter(
        models.Q(student__first_name__icontains=query) |
        models.Q(student__last_name__icontains=query) |
        models.Q(student__email__icontains=query) |
        models.Q(student__student_id__icontains=query)
    )
    students = [application.student for application in applications]
    results = [
        {
            'first_name': student.first_name, 
            'last_name': student.last_name,
            'email': student.email, 
            'student_id': student.student_id
        } 
        for student in students
    ]
    return results

def get_application_decision_table(application: Application, column_name):
    assert column_name in ['academic', 'english', 'work']
    if not application.decision_data:
        add_student_qualifications_decisions(application)

    decisions_data: dict = ast.literal_eval(application.decision_data)
    decision_keys_map = {k.split()[0].lower(): k for k in decisions_data.keys()}
    decision_table = decisions_data[decision_keys_map[column_name]]

    f_name, pth = get_document_path(decision_table['doc_id'])
    print("Application data: ", application.academic_data == '')

    if column_name == 'academic':
        approve_or_decline = application.academic_data == ''
    elif column_name == 'english':
        approve_or_decline = application.english_data == ''
    elif column_name == 'work':
        approve_or_decline = application.work_experience_data == ''
    else:
        approve_or_decline = False

    context = {
        'application': application,
        'decision_data': decision_table,
        "requirement": decision_table['requirement'],
        'qualification': decision_table['qualification'],
        'qualification_result': decision_table['qualification_result'],
        'supporting_text': decision_table['supporting_text'],
        'reasoning': decision_table['reasoning'],
        'decision': decision_table['decision'],
        'document_path': pth,
        'file_name': f_name,
        'approve_or_decline': approve_or_decline
    }
    
    return context


def get_document_path(doc_id):
    doc = StudentDocument.objects.get(id=doc_id)
    file_name = doc.file_name
    student_id = doc.student.student_id
    f_name = file_name.split('.txt')[0] + '.pdf'
    pth = os.path.join(
        settings.MEDIA_URL, 
        str(student_id), 
        file_name.split('.txt')[0] + '.pdf'
    )

    print("Document path: ", pth)
    
    return f_name, pth

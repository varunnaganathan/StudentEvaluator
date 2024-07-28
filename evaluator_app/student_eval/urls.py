from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing_page, name="index"),
    path('student-search/', views.student_search, name='student-search'),
    path('student-application/', views.search_result, name='search-result'),
    path('student_info/<int:application_id>/', views.student_info, name='student_info'),
    path('academic/<int:application_id>/', views.academic, name='academic'),
    path('approve_or_decline/<int:application_id>/', views.approve_or_decline, name='approve_or_decline'),
    path('english/<int:application_id>/', views.english, name='english'),
    path('work_experience/<int:application_id>/', views.work_experience, name='work_experience'),
    path('visa/<int:application_id>/', views.visa, name='visa'),
    path('exceptions/<int:application_id>/', views.exceptions, name='exceptions'),
    path('app_notes/<int:application_id>/', views.app_notes, name='app_notes'),
]
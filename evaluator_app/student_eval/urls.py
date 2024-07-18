from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('student_info/', views.student_info, name='student_info'),
    path('academic/', views.academic, name='academic'),
    path('english/', views.english, name='english'),
    path('visa/', views.visa, name='visa'),
    path('exceptions/', views.exceptions, name='exceptions'),
    path('app_notes/', views.app_notes, name='app_notes'),
]
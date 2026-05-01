from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('marks/', views.marks_list, name='marks_list'),
    path('marks/add/', views.add_marks, name='add_marks'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('assessments/', views.assessment_list, name='assessment_list'),
    path('assessments/create/', views.create_assessment, name='create_assessment'),
    path('assessments/<int:pk>/', views.assessment_detail, name='assessment_detail'),
    path('reports/subject/<int:pk>/', views.subject_report, name='subject_report'),
    path('notifications/', views.notifications_view, name='notifications'),
    # API
    path('api/student/<int:pk>/trend/', views.api_student_trend, name='api_student_trend'),
    path('api/class-performance/', views.api_class_performance, name='api_class_performance'),
]

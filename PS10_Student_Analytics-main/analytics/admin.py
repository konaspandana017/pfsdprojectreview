from django.contrib import admin
from .models import (
    Subject, ClassRoom, StudentProfile, ExamType,
    Marks, Attendance, Assessment, AssessmentSubmission, Notification
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'max_marks']
    search_fields = ['code', 'name']
    filter_horizontal = ['teachers']


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'section', 'academic_year', 'class_teacher']
    list_filter = ['academic_year']
    filter_horizontal = ['students', 'subjects']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'roll_number', 'parent_name']
    search_fields = ['roll_number', 'user__username', 'user__first_name']


@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'weightage']


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'exam_type', 'marks_obtained', 'date']
    list_filter = ['subject', 'exam_type', 'date']
    search_fields = ['student__username', 'student__first_name']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'date', 'status']
    list_filter = ['subject', 'status', 'date']
    search_fields = ['student__username']


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'classroom', 'due_date', 'max_score']
    list_filter = ['subject', 'assessment_type']


@admin.register(AssessmentSubmission)
class AssessmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assessment', 'score', 'status']
    list_filter = ['status']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'title', 'notif_type', 'is_read', 'created_at']
    list_filter = ['notif_type', 'is_read']

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count, Max, Min, Q
from django.utils import timezone
from datetime import timedelta, date
import json

from accounts.models import User
from .models import (
    Subject, ClassRoom, Marks, Attendance, Assessment,
    AssessmentSubmission, StudentProfile, ExamType, Notification
)
from .forms import MarksForm, AttendanceForm, AssessmentForm, SubmissionGradeForm


def role_required(*roles):
    """Decorator to restrict views by role."""
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role in roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return wrapper
    return decorator


@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}

    if user.is_admin_user():
        context.update(_admin_dashboard_data())
    elif user.is_teacher():
        context.update(_teacher_dashboard_data(user))
    else:
        context.update(_student_dashboard_data(user))

    return render(request, 'analytics/dashboard.html', context)


def _admin_dashboard_data():
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_subjects = Subject.objects.count()
    total_classes = ClassRoom.objects.count()

    # Recent marks distribution
    all_marks = Marks.objects.all()
    grade_dist = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    for m in all_marks:
        grade_dist[m.get_grade()] += 1

    # Subject-wise average
    subject_avgs = []
    for subj in Subject.objects.all():
        avg = subj.marks.aggregate(avg=Avg('marks_obtained'))['avg']
        if avg:
            subject_avgs.append({'name': subj.name, 'avg': round(avg, 1)})

    # Attendance overview
    today = date.today()
    week_ago = today - timedelta(days=7)
    recent_attendance = Attendance.objects.filter(date__gte=week_ago)
    total_att = recent_attendance.count()
    present_att = recent_attendance.filter(status='present').count()
    att_rate = round((present_att / total_att) * 100, 1) if total_att else 0

    # Top performers
    top_students = []
    for student in User.objects.filter(role='student')[:20]:
        marks = student.marks.all()
        if marks:
            avg = sum((m.marks_obtained / m.subject.max_marks) * 100 for m in marks) / marks.count()
            top_students.append({'student': student, 'avg': round(avg, 1)})
    top_students = sorted(top_students, key=lambda x: x['avg'], reverse=True)[:5]

    return {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_subjects': total_subjects,
        'total_classes': total_classes,
        'grade_dist': json.dumps(grade_dist, default=float),
        'subject_avgs': json.dumps(subject_avgs, default=float),        'att_rate': att_rate,
        'top_students': top_students,
        'recent_marks': Marks.objects.select_related('student', 'subject')[:10],
    }


def _teacher_dashboard_data(user):
    subjects = user.teaching_subjects.all()
    classes = ClassRoom.objects.filter(
        Q(class_teacher=user) | Q(subjects__in=subjects)
    ).distinct()

    # Students in teacher's classes
    student_ids = set()
    for cls in classes:
        for s in cls.students.all():
            student_ids.add(s.id)
    students = User.objects.filter(id__in=student_ids)

    # Recent marks entered by teacher
    recent_marks = Marks.objects.filter(
        recorded_by=user
    ).select_related('student', 'subject').order_by('-created_at')[:10]

    # Subject performance
    subject_data = []
    for subj in subjects:
        avg = subj.marks.aggregate(avg=Avg('marks_obtained'))['avg']
        subject_data.append({
            'name': subj.name,
            'avg': round(avg, 1) if avg else 0,
            'students': subj.marks.values('student').distinct().count()
        })

    # Pending assessments
    pending_assessments = Assessment.objects.filter(
        created_by=user
    ).annotate(
        submission_count=Count('submissions')
    ).order_by('-due_date')[:5]

    return {
        'subjects': subjects,
        'classes': classes,
        'student_count': len(student_ids),
        'recent_marks': recent_marks,
        'subject_data': json.dumps(subject_data, default=float),
        'pending_assessments': pending_assessments,
    }


def _student_dashboard_data(user):
    marks = user.marks.select_related('subject', 'exam_type').all()

    # Calculate overall average
    overall_avg = 0
    if marks:
        overall_avg = sum((m.marks_obtained / m.subject.max_marks) * 100 for m in marks) / marks.count()
        overall_avg = round(overall_avg, 1)

    # Subject-wise performance for chart
    subject_perf = {}
    for m in marks:
        if m.subject.name not in subject_perf:
            subject_perf[m.subject.name] = []
        subject_perf[m.subject.name].append(float((m.marks_obtained / m.subject.max_marks) * 100))

    subject_chart = [
        {'subject': s, 'avg': round(sum(v) / len(v), 1)}
        for s, v in subject_perf.items()
    ]

    # Attendance
    attendance = user.attendance_records.all()
    total_att = attendance.count()
    present_att = attendance.filter(status='present').count()
    att_pct = round((present_att / total_att) * 100, 1) if total_att else 0

    # Attendance by subject for chart
    att_by_subject = []
    for subj in Subject.objects.filter(attendance__student=user).distinct():
        subj_att = attendance.filter(subject=subj)
        total = subj_att.count()
        present = subj_att.filter(status='present').count()
        att_by_subject.append({
            'subject': subj.name,
            'pct': round((present / total) * 100, 1) if total else 0
        })

    # Grade trend over time
    recent_marks = marks.order_by('date')[:12]
    trend_data = [
        {'date': str(m.date), 'pct': float(m.get_percentage()), 'subject': m.subject.name}
        for m in recent_marks
    ]

    # Pending submissions
    pending_subs = AssessmentSubmission.objects.filter(
        student=user, status__in=['pending', 'submitted']
    ).select_related('assessment', 'assessment__subject')[:5]

    # Generate improvement suggestions
    suggestions = _generate_suggestions(user, marks, att_pct)

    return {
        'overall_avg': overall_avg,
        'att_pct': att_pct,
        'total_att': total_att,
        'present_att': present_att,
        'subject_chart': json.dumps(subject_chart, default=float),
        'att_by_subject': json.dumps(att_by_subject, default=float),
        'trend_data': json.dumps(trend_data, default=float),
        'recent_marks': marks[:5],
        'pending_submissions': pending_subs,
        'suggestions': suggestions,
    }


def _generate_suggestions(user, marks, att_pct):
    suggestions = []

    # Attendance suggestions
    if att_pct < 75:
        suggestions.append({
            'type': 'danger',
            'icon': 'exclamation-triangle',
            'title': 'Critical Attendance',
            'text': f'Your attendance is {att_pct}%, which is below 75%. You may be barred from exams.'
        })
    elif att_pct < 85:
        suggestions.append({
            'type': 'warning',
            'icon': 'calendar-x',
            'title': 'Improve Attendance',
            'text': f'Your attendance is {att_pct}%. Aim for at least 85% for better performance.'
        })

    # Subject-wise suggestions
    subject_avgs = {}
    for m in marks:
        if m.subject.name not in subject_avgs:
            subject_avgs[m.subject.name] = []
        subject_avgs[m.subject.name].append(float(m.get_percentage()))

    for subj, percs in subject_avgs.items():
        avg = sum(percs) / len(percs)
        if avg < 50:
            suggestions.append({
                'type': 'danger',
                'icon': 'book-x',
                'title': f'Focus on {subj}',
                'text': f'Your average in {subj} is {avg:.1f}%. Consider extra study or seeking help.'
            })
        elif avg >= 90:
            suggestions.append({
                'type': 'success',
                'icon': 'star',
                'title': f'Excellent in {subj}',
                'text': f'Great work! Your {subj} average is {avg:.1f}%. Keep it up!'
            })

    if not suggestions:
        suggestions.append({
            'type': 'info',
            'icon': 'check-circle',
            'title': 'Good Progress',
            'text': 'You are performing well. Maintain consistency to achieve top grades.'
        })

    return suggestions[:4]  # Max 4 suggestions


@login_required
def student_list(request):
    if request.user.is_student_user():
        return redirect('dashboard')

    students = User.objects.filter(role='student').select_related('student_profile')
    classroom_filter = request.GET.get('classroom')

    if classroom_filter:
        students = students.filter(enrolled_classes__id=classroom_filter)

    classrooms = ClassRoom.objects.all()

    # Add computed stats
    student_data = []
    for student in students:
        marks = student.marks.all()
        avg = 0
        if marks:
            avg = sum((m.marks_obtained / m.subject.max_marks) * 100 for m in marks) / marks.count()
        att = student.attendance_records.all()
        att_pct = 0
        if att:
            att_pct = (att.filter(status='present').count() / att.count()) * 100
        student_data.append({
            'student': student,
            'avg': round(avg, 1),
            'att_pct': round(att_pct, 1),
        })

    return render(request, 'analytics/student_list.html', {
        'student_data': student_data,
        'classrooms': classrooms,
        'classroom_filter': classroom_filter,
    })


@login_required
def student_detail(request, pk):
    student = get_object_or_404(User, pk=pk, role='student')

    # Access control: students can only see their own details
    if request.user.is_student_user() and request.user.pk != pk:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    marks = student.marks.select_related('subject', 'exam_type').order_by('-date')
    attendance = student.attendance_records.select_related('subject').order_by('-date')
    submissions = student.submissions.select_related('assessment', 'assessment__subject')

    # Per-subject analysis
    subject_analysis = {}
    for m in marks:
        sn = m.subject.name
        if sn not in subject_analysis:
            subject_analysis[sn] = {'marks': [], 'subject': m.subject}
        subject_analysis[sn]['marks'].append(m)

    for sn, data in subject_analysis.items():
        ms = data['marks']
        percs = [(m.marks_obtained / m.subject.max_marks) * 100 for m in ms]
        data['avg'] = round(sum(percs) / len(percs), 1)
        data['max'] = round(max(percs), 1)
        data['min'] = round(min(percs), 1)
        data['grade'] = ms[0].get_grade() if ms else 'N/A'

    # Attendance by subject
    att_analysis = {}
    for a in attendance:
        sn = a.subject.name
        if sn not in att_analysis:
            att_analysis[sn] = {'total': 0, 'present': 0}
        att_analysis[sn]['total'] += 1
        if a.status == 'present':
            att_analysis[sn]['present'] += 1

    for sn in att_analysis:
        d = att_analysis[sn]
        d['pct'] = round((d['present'] / d['total']) * 100, 1) if d['total'] else 0

    # Chart data
    trend_data = [
        {'date': str(m.date), 'pct': float(m.get_percentage()), 'subject': m.subject.name}
        for m in marks.order_by('date')[:20]
    ]

    overall_avg = 0
    if marks:
        overall_avg = sum((m.marks_obtained / m.subject.max_marks) * 100 for m in marks) / marks.count()
        overall_avg = round(overall_avg, 1)

    total_att = attendance.count()
    att_pct = 0
    if total_att:
        att_pct = round((attendance.filter(status='present').count() / total_att) * 100, 1)

    suggestions = _generate_suggestions(student, marks, att_pct)

    return render(request, 'analytics/student_detail.html', {
        'student': student,
        'marks': marks[:20],
        'attendance': attendance[:20],
        'submissions': submissions,
        'subject_analysis': subject_analysis,
        'att_analysis': att_analysis,
        'trend_data': json.dumps(trend_data, default=float),
        'overall_avg': overall_avg,
        'att_pct': att_pct,
        'suggestions': suggestions,
    })


@login_required
@role_required('admin', 'teacher')
def add_marks(request):
    form = MarksForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        marks = form.save(commit=False)
        marks.recorded_by = request.user
        marks.save()
        messages.success(request, f'Marks added for {marks.student.get_full_name()}!')
        return redirect('marks_list')
    return render(request, 'analytics/marks_form.html', {'form': form, 'title': 'Add Marks'})


@login_required
@role_required('admin', 'teacher')
def marks_list(request):
    marks = Marks.objects.select_related('student', 'subject', 'exam_type').order_by('-date')
    subject_filter = request.GET.get('subject')
    student_filter = request.GET.get('student')
    if subject_filter:
        marks = marks.filter(subject_id=subject_filter)
    if student_filter:
        marks = marks.filter(student_id=student_filter)

    return render(request, 'analytics/marks_list.html', {
        'marks': marks[:50],
        'subjects': Subject.objects.all(),
        'students': User.objects.filter(role='student'),
        'subject_filter': subject_filter,
        'student_filter': student_filter,
    })


@login_required
@role_required('admin', 'teacher')
def mark_attendance(request):
    form = AttendanceForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        att = form.save(commit=False)
        att.marked_by = request.user
        att.save()
        messages.success(request, 'Attendance recorded!')
        return redirect('attendance_list')
    return render(request, 'analytics/attendance_form.html', {'form': form, 'title': 'Mark Attendance'})


@login_required
def attendance_list(request):
    if request.user.is_student_user():
        attendance = request.user.attendance_records.select_related('subject').order_by('-date')
    else:
        attendance = Attendance.objects.select_related('student', 'subject').order_by('-date')

    return render(request, 'analytics/attendance_list.html', {'attendance': attendance[:50]})


@login_required
def assessment_list(request):
    if request.user.is_student_user():
        assessments = Assessment.objects.filter(
            classroom__students=request.user
        ).select_related('subject', 'classroom')
    elif request.user.is_teacher():
        assessments = Assessment.objects.filter(
            created_by=request.user
        ).select_related('subject', 'classroom')
    else:
        assessments = Assessment.objects.select_related('subject', 'classroom').all()

    return render(request, 'analytics/assessment_list.html', {'assessments': assessments})


@login_required
@role_required('admin', 'teacher')
def create_assessment(request):
    form = AssessmentForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        assessment = form.save(commit=False)
        assessment.created_by = request.user
        assessment.save()
        messages.success(request, 'Assessment created!')
        return redirect('assessment_list')
    return render(request, 'analytics/assessment_form.html', {'form': form})


@login_required
def assessment_detail(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    submissions = assessment.submissions.select_related('student').all()
    return render(request, 'analytics/assessment_detail.html', {
        'assessment': assessment,
        'submissions': submissions,
    })


@login_required
def subject_report(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    marks = subject.marks.select_related('student', 'exam_type').order_by('-date')

    # Grade distribution
    grade_dist = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    for m in marks:
        grade_dist[m.get_grade()] += 1

    # Student-wise averages
    student_avgs = {}
    for m in marks:
        sid = m.student.id
        if sid not in student_avgs:
            student_avgs[sid] = {'student': m.student, 'marks': []}
        student_avgs[sid]['marks'].append(float(m.get_percentage()))

    student_summary = []
    for sid, data in student_avgs.items():
        avg = sum(data['marks']) / len(data['marks'])
        student_summary.append({'student': data['student'], 'avg': round(avg, 1)})
    student_summary.sort(key=lambda x: x['avg'], reverse=True)

    overall_avg = marks.aggregate(avg=Avg('marks_obtained'))['avg']

    return render(request, 'analytics/subject_report.html', {
        'subject': subject,
        'marks': marks[:20],
        'grade_dist': json.dumps(grade_dist, default=float),
        'student_summary': student_summary,
        'overall_avg': round(overall_avg, 1) if overall_avg else 0,
    })


@login_required
def notifications_view(request):
    notifs = request.user.notifications.all()
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'analytics/notifications.html', {'notifications': notifs})


# API Views for AJAX chart data
@login_required
def api_student_trend(request, pk):
    student = get_object_or_404(User, pk=pk, role='student')
    marks = student.marks.select_related('subject').order_by('date')
    data = [
        {'date': str(m.date), 'pct': float(m.get_percentage()), 'subject': m.subject.name}
        for m in marks
    ]
    return JsonResponse({'data': data})


@login_required
def api_class_performance(request):
    classroom_id = request.GET.get('classroom_id')
    if classroom_id:
        classroom = get_object_or_404(ClassRoom, pk=classroom_id)
        data = []
        for student in classroom.students.all():
            marks = student.marks.all()
            if marks:
                avg = sum(float(m.get_percentage()) for m in marks) / marks.count()
                data.append({'name': student.get_full_name(), 'avg': round(avg, 1)})
        return JsonResponse({'data': data})
    return JsonResponse({'data': []})

"""
Management command to seed demo data for PS10 Student Analytics.
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Seeds the database with demo data for testing'

    def handle(self, *args, **kwargs):
        from accounts.models import User
        from analytics.models import (
            Subject, ClassRoom, StudentProfile, ExamType,
            Marks, Attendance, Assessment, AssessmentSubmission, Notification
        )

        self.stdout.write('🌱 Seeding demo data...')

        # Create Superuser / Admin
        admin, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@ps10.edu', 'role': 'admin', 'first_name': 'Admin', 'last_name': 'User',
            'is_staff': True, 'is_superuser': True
        })
        # Always update these fields and password
        admin.role = 'admin'
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.first_name = 'Admin'
        admin.last_name = 'User'
        admin.set_password('admin123')
        admin.save()

        # Create Teachers
        teachers = []
        teacher_data = [
            ('teacher1', 'Rajesh', 'Kumar', 'rajesh@ps10.edu'),
            ('teacher2', 'Priya', 'Sharma', 'priya@ps10.edu'),
            ('teacher3', 'Suresh', 'Rao', 'suresh@ps10.edu'),
        ]
        for uname, fn, ln, email in teacher_data:
            t, _ = User.objects.get_or_create(username=uname, defaults={
                'email': email, 'role': 'teacher', 'first_name': fn, 'last_name': ln
            })
            t.role = 'teacher'
            t.is_active = True
            t.first_name = fn
            t.last_name = ln
            t.set_password('teacher123')
            t.save()
            teachers.append(t)

        # Create Students
        students = []
        student_data = [
            ('student1', 'Arjun', 'Patel', 'arjun@ps10.edu'),
            ('student2', 'Ananya', 'Singh', 'ananya@ps10.edu'),
            ('student3', 'Vikram', 'Nair', 'vikram@ps10.edu'),
            ('student4', 'Kavya', 'Reddy', 'kavya@ps10.edu'),
            ('student5', 'Rahul', 'Verma', 'rahul@ps10.edu'),
            ('student6', 'Deepa', 'Iyer', 'deepa@ps10.edu'),
        ]
        for uname, fn, ln, email in student_data:
            s, _ = User.objects.get_or_create(username=uname, defaults={
                'email': email, 'role': 'student', 'first_name': fn, 'last_name': ln
            })
            s.set_password('student123')
            s.save()
            students.append(s)
            # Create student profile
            StudentProfile.objects.get_or_create(user=s, defaults={
                'roll_number': f'2024{str(students.index(s)+1).zfill(3)}',
                'parent_name': f'Parent of {fn}',
                'parent_phone': f'98765{random.randint(10000, 99999)}',
            })

        # Create Subjects
        subject_data = [
            ('Mathematics', 'MATH101', 100),
            ('Physics', 'PHY102', 100),
            ('Chemistry', 'CHEM103', 100),
            ('Computer Science', 'CS104', 100),
            ('English', 'ENG105', 100),
        ]
        subjects = []
        for name, code, max_marks in subject_data:
            subj, _ = Subject.objects.get_or_create(code=code, defaults={
                'name': name, 'max_marks': max_marks
            })
            subjects.append(subj)

        # Assign teachers to subjects
        subjects[0].teachers.set([teachers[0]])
        subjects[1].teachers.set([teachers[1]])
        subjects[2].teachers.set([teachers[1]])
        subjects[3].teachers.set([teachers[2]])
        subjects[4].teachers.set([teachers[0]])

        # Create Classroom
        classroom, _ = ClassRoom.objects.get_or_create(
            name='12th Grade', section='A', academic_year='2024-2025',
            defaults={'class_teacher': teachers[0]}
        )
        classroom.students.set(students)
        classroom.subjects.set(subjects)

        # Create Exam Types
        exam_types = []
        for name, weightage in [('Unit Test 1', 20), ('Mid Term', 30), ('Unit Test 2', 20), ('Final Exam', 50)]:
            et, _ = ExamType.objects.get_or_create(name=name, defaults={'weightage': weightage})
            exam_types.append(et)

        # Create Marks
        base_date = date.today() - timedelta(days=90)
        for student in students:
            base_score = random.randint(50, 95)  # Different base for each student
            for subj in subjects:
                for i, et in enumerate(exam_types):
                    score = min(100, max(20, base_score + random.randint(-15, 15)))
                    marks_date = base_date + timedelta(days=i * 21 + random.randint(0, 5))
                    Marks.objects.get_or_create(
                        student=student, subject=subj, exam_type=et, date=marks_date,
                        defaults={'marks_obtained': score, 'recorded_by': teachers[0]}
                    )

        # Create Attendance
        today = date.today()
        for i in range(60):
            att_date = today - timedelta(days=i)
            if att_date.weekday() < 5:  # Weekdays only
                for student in students:
                    for subj in subjects:
                        # 85-95% attendance probability per student
                        threshold = random.randint(85, 95)
                        status = 'present' if random.randint(1, 100) <= threshold else 'absent'
                        Attendance.objects.get_or_create(
                            student=student, subject=subj, date=att_date,
                            defaults={'status': status, 'marked_by': teachers[0]}
                        )

        # Create Assessments
        assessment_data = [
            ('Python Assignment', 'assignment', subjects[3], 50),
            ('Physics Lab Report', 'lab', subjects[1], 30),
            ('Math Quiz', 'quiz', subjects[0], 20),
            ('Chemistry Project', 'project', subjects[2], 100),
        ]
        assessments = []
        for title, atype, subj, max_score in assessment_data:
            a, _ = Assessment.objects.get_or_create(
                title=title, defaults={
                    'assessment_type': atype, 'subject': subj, 'classroom': classroom,
                    'max_score': max_score, 'due_date': today + timedelta(days=random.randint(1, 30)),
                    'created_by': teachers[0]
                }
            )
            assessments.append(a)

        # Create Assessment Submissions
        for assessment in assessments:
            for student in students[:4]:
                AssessmentSubmission.objects.get_or_create(
                    assessment=assessment, student=student,
                    defaults={
                        'score': random.randint(int(assessment.max_score * 0.5), assessment.max_score),
                        'status': 'graded',
                        'submitted_at': timezone.now() - timedelta(days=random.randint(1, 10)),
                        'graded_at': timezone.now(),
                        'feedback': 'Good work! Keep it up.'
                    }
                )

        # Create Notifications
        for student in students:
            Notification.objects.get_or_create(
                recipient=student,
                title='Welcome to PS10 Analytics',
                defaults={
                    'message': 'Your academic performance dashboard is ready. Track your marks, attendance, and get personalized improvement tips.',
                    'notif_type': 'info'
                }
            )

        self.stdout.write(self.style.SUCCESS(f'''
✅ Demo data seeded successfully!

Demo Credentials:
━━━━━━━━━━━━━━━━━━━━━━━━
👤 Admin:   admin / admin123
👨‍🏫 Teacher: teacher1 / teacher123
👨‍🎓 Student: student1 / student123
━━━━━━━━━━━━━━━━━━━━━━━━

Data Created:
 • {len(students)} students, {len(teachers)} teachers
 • {len(subjects)} subjects, 1 classroom
 • {len(exam_types)} exam types
 • Marks, attendance, assessments, notifications
        '''))

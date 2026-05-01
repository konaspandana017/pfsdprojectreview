from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    max_marks = models.PositiveIntegerField(default=100)
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'role': 'teacher'},
        related_name='teaching_subjects',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']


class ClassRoom(models.Model):
    name = models.CharField(max_length=50)
    section = models.CharField(max_length=5)
    academic_year = models.CharField(max_length=9)  # e.g. "2024-2025"
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        limit_choices_to={'role': 'teacher'},
        on_delete=models.SET_NULL,
        related_name='class_rooms'
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'role': 'student'},
        related_name='enrolled_classes',
        blank=True
    )
    subjects = models.ManyToManyField(Subject, related_name='classrooms', blank=True)

    def __str__(self):
        return f"{self.name}-{self.section} ({self.academic_year})"

    class Meta:
        unique_together = ['name', 'section', 'academic_year']
        ordering = ['academic_year', 'name', 'section']


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        limit_choices_to={'role': 'student'}
    )
    roll_number = models.CharField(max_length=20, unique=True)
    parent_name = models.CharField(max_length=100, blank=True)
    parent_phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    admission_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.roll_number})"

    def get_overall_average(self):
        marks = self.user.marks.all()
        if not marks:
            return 0
        total = sum((m.marks_obtained / m.subject.max_marks) * 100 for m in marks)
        return round(total / marks.count(), 2)

    def get_attendance_percentage(self):
        records = self.user.attendance_records.all()
        if not records:
            return 0
        present = records.filter(status='present').count()
        return round((present / records.count()) * 100, 2)

    class Meta:
        verbose_name = 'Student Profile'


class ExamType(models.Model):
    name = models.CharField(max_length=50)  # Mid-term, Final, Unit Test, etc.
    weightage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100
    )

    def __str__(self):
        return self.name


class Marks(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='marks',
        limit_choices_to={'role': 'student'}
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='marks')
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name='marks')
    marks_obtained = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    date = models.DateField()
    remarks = models.CharField(max_length=200, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_marks'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def get_percentage(self):
        return round((self.marks_obtained / self.subject.max_marks) * 100, 2)

    def get_grade(self):
        pct = self.get_percentage()
        if pct >= 90: return 'A+'
        elif pct >= 80: return 'A'
        elif pct >= 70: return 'B+'
        elif pct >= 60: return 'B'
        elif pct >= 50: return 'C'
        elif pct >= 40: return 'D'
        return 'F'

    def __str__(self):
        return f"{self.student.username} - {self.subject.name} - {self.marks_obtained}"

    class Meta:
        unique_together = ['student', 'subject', 'exam_type', 'date']
        ordering = ['-date']
        verbose_name_plural = 'Marks'


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        limit_choices_to={'role': 'student'}
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='marked_attendance'
    )
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.subject.name} - {self.date} - {self.status}"

    class Meta:
        unique_together = ['student', 'subject', 'date']
        ordering = ['-date']
        verbose_name_plural = 'Attendance Records'


class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('quiz', 'Quiz'),
        ('lab', 'Lab Work'),
        ('presentation', 'Presentation'),
    ]
    title = models.CharField(max_length=200)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assessments')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='assessments')
    max_score = models.PositiveIntegerField(default=100)
    due_date = models.DateField()
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assessments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.subject.name})"

    class Meta:
        ordering = ['-due_date']


class AssessmentSubmission(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
        limit_choices_to={'role': 'student'}
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True, blank=True
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('late', 'Late Submission'),
    ], default='pending')

    def get_percentage(self):
        if self.score is None:
            return 0
        return round((self.score / self.assessment.max_score) * 100, 2)

    def __str__(self):
        return f"{self.student.username} - {self.assessment.title}"

    class Meta:
        unique_together = ['assessment', 'student']


class Notification(models.Model):
    NOTIF_TYPES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('danger', 'Danger'),
    ]
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notif_type = models.CharField(max_length=10, choices=NOTIF_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"

    class Meta:
        ordering = ['-created_at']

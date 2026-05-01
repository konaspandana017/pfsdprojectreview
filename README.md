# PS10 – Student Performance Analytics System
## Django + PostgreSQL Project

---

## 🚀 Quick Setup in PyCharm

### Step 1: Install Dependencies
Open PyCharm Terminal and run:
```bash
pip install -r requirements.txt
```

### Step 2: Setup PostgreSQL Database
Open pgAdmin or psql and run:
```sql
CREATE DATABASE student_analytics_db;
CREATE USER postgres WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE student_analytics_db TO postgres;
```

### Step 3: Configure Database
Open `student_analytics/settings.py` and update:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'student_analytics_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',  # ← Change this
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Step 4: Run Migrations
```bash
python manage.py makemigrations accounts
python manage.py makemigrations analytics
python manage.py migrate
```

### Step 5: Seed Demo Data
```bash
python manage.py seed_data
```

### Step 6: Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### Step 7: Run Server
```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000**

---

## 🔐 Demo Login Credentials

| Role    | Username  | Password    |
|---------|-----------|-------------|
| Admin   | admin     | admin123    |
| Teacher | teacher1  | teacher123  |
| Student | student1  | student123  |

---

## 📁 Project Structure

```
student_analytics/
├── manage.py
├── requirements.txt
├── student_analytics/         # Project config
│   ├── settings.py
│   └── urls.py
├── accounts/                  # Custom User model
│   ├── models.py             # User with role field
│   ├── views.py              # Login, Register, Profile
│   ├── forms.py
│   └── admin.py
├── analytics/                 # Core analytics app
│   ├── models.py             # Subject, Marks, Attendance, Assessment...
│   ├── views.py              # All dashboards + reports
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   └── management/commands/
│       └── seed_data.py      # Demo data seeder
├── templates/
│   ├── base.html             # Master layout with sidebar
│   ├── accounts/             # Login, Register, Profile
│   └── analytics/            # Dashboard, Reports, Forms
└── static/
```

---

## 🎯 Features by Role

### Admin
- System-wide statistics (students, teachers, subjects)
- Grade distribution charts (doughnut)
- Subject performance bar charts
- Top performers leaderboard
- Manage all data via Django Admin `/admin/`

### Teacher
- Subject performance overview
- Student marks entry and management
- Attendance marking
- Assessment creation and grading
- Subject-specific reports with grade distribution

### Student
- Personal performance dashboard
- Trend chart (performance over time)
- Radar chart (subject comparison)
- Attendance tracking per subject
- Smart improvement suggestions
- Pending submission tracker

---

## 🗄️ Database Models

| Model | Description |
|-------|-------------|
| User | Custom user with Admin/Teacher/Student roles |
| Subject | Academic subjects with max marks |
| ClassRoom | Class sections with students and subjects |
| StudentProfile | Roll number, parent info |
| ExamType | Mid-term, Final, Quiz etc. |
| Marks | Student marks per subject per exam |
| Attendance | Daily attendance per subject |
| Assessment | Assignments, Projects, Labs |
| AssessmentSubmission | Student submissions with grades |
| Notification | In-app notifications |

---

## 🛠️ PyCharm Configuration

1. Set Python Interpreter: `File > Settings > Project > Python Interpreter`
2. Set Django: `Settings > Languages > Django` → Enable Django support → Set manage.py path
3. Run Config: `Edit Configurations > Add Django Server`

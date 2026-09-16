from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# ── User ──────────────────────────────────────────────────────────────────────
class UserManager(BaseUserManager):
    def create_user(self, email, name, phone, password=None, **extra):
        if not email:
            raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, phone, password=None, **extra):
        extra.setdefault('role', 'admin')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, name, phone, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [('student', 'Student'), ('admin', 'Admin'), ('trainer', 'Trainer'), ('faculty', 'Faculty')]
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    avatar = models.URLField(default='https://ui-avatars.com/api/?name=User&background=FF6B35&color=fff')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    trainer_permissions = models.TextField(default='', blank=True, help_text='Comma-separated box keys allowed for trainer')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone']
    objects = UserManager()

    def __str__(self):
        return self.email


# ── Category ──────────────────────────────────────────────────────────────────
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=10, default='📚')
    color = models.CharField(max_length=20, default='#FF6B35')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_allowed_email_list(self):
        if not self.allowed_emails:
            return []
        import re
        emails = [e.strip().lower() for e in re.split(r'[\s,;]+', self.allowed_emails) if e.strip()]
        return list(dict.fromkeys(emails))


# ── Section ───────────────────────────────────────────────────────────────────
class Section(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='sections', null=True, blank=True)
    batch = models.ForeignKey('Batch', on_delete=models.CASCADE, related_name='sections', null=True, blank=True)
    title = models.CharField(max_length=300)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


# ── Course ────────────────────────────────────────────────────────────────────
class Course(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField()
    thumbnail = models.URLField(default='https://via.placeholder.com/400x200')
    category = models.CharField(max_length=100)
    language = models.CharField(max_length=50, default='Hindi + English')
    instructor_name = models.CharField(max_length=200, blank=True)
    instructor_avatar = models.URLField(blank=True)
    instructor_bio = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_free = models.BooleanField(default=False)
    allowed_emails = models.TextField(blank=True, default='', help_text='Comma-separated student email IDs allowed in this batch')
    rating = models.FloatField(default=4.5)
    total_students = models.IntegerField(default=0)
    total_lectures = models.IntegerField(default=0)
    duration = models.CharField(max_length=50, default='0 hours')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CourseEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrolled_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')


# ── Batch ─────────────────────────────────────────────────────────────────────
class Batch(models.Model):
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    thumbnail = models.URLField(default='https://via.placeholder.com/400x200')
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_free = models.BooleanField(default=False)
    allowed_emails = models.TextField(blank=True, default='', help_text='Comma-separated student email IDs allowed in this batch')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    instructor_name = models.CharField(max_length=200, blank=True)
    instructor_avatar = models.URLField(blank=True)
    total_students = models.IntegerField(default=0)
    is_live = models.BooleanField(default=False)
    live_stream_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_allowed_email_list(self):
        if not self.allowed_emails:
            return []
        import re
        emails = [e.strip().lower() for e in re.split(r'[\s,;]+', self.allowed_emails) if e.strip()]
        return list(dict.fromkeys(emails))


class BatchEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrolled_batches')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'batch')


# ── Lecture ───────────────────────────────────────────────────────────────────
class Lecture(models.Model):
    VIDEO_TYPES = [('youtube', 'YouTube'), ('vimeo', 'Vimeo'), ('direct', 'Direct')]
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    video_url = models.URLField(max_length=1000)
    video_type = models.CharField(max_length=10, choices=VIDEO_TYPES, default='youtube')
    duration = models.CharField(max_length=20, default='0:00')
    thumbnail = models.URLField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lectures', null=True)
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name='lectures')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name='batch_lectures')
    subject = models.CharField(max_length=100, blank=True)
    chapter = models.CharField(max_length=100, blank=True)
    is_free = models.BooleanField(default=False)
    allowed_emails = models.TextField(blank=True, default='', help_text='Comma-separated student email IDs allowed in this batch')
    is_published = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


# ── Note ──────────────────────────────────────────────────────────────────────
class Note(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    pdf_url = models.CharField(max_length=500)
    subject = models.CharField(max_length=100, blank=True)
    chapter = models.CharField(max_length=100, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='notes', null=True)
    is_free = models.BooleanField(default=False)
    allowed_emails = models.TextField(blank=True, default='', help_text='Comma-separated student email IDs allowed in this batch')
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ── Assignment ────────────────────────────────────────────────────────────────
class Assignment(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    total_marks = models.IntegerField(default=100)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('reviewed', 'Reviewed')]
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    file_url = models.CharField(max_length=500, blank=True)
    file_name = models.CharField(max_length=200, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')


# ── Attendance ────────────────────────────────────────────────────────────────
class Attendance(models.Model):
    STATUS_CHOICES = [('present', 'Present'), ('absent', 'Absent'), ('late', 'Late')]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'batch', 'date')


# ── Progress ──────────────────────────────────────────────────────────────────
class Progress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    completed_lectures = models.ManyToManyField(Lecture, blank=True)
    completion_percent = models.FloatField(default=0)
    last_watched = models.ForeignKey(Lecture, on_delete=models.SET_NULL, null=True, blank=True, related_name='last_watched_by')
    certificate_issued = models.BooleanField(default=False)
    certificate_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course')


# ── Notification ──────────────────────────────────────────────────────────────
class Notification(models.Model):
    TYPE_CHOICES = [('lecture', 'Lecture'), ('assignment', 'Assignment'), ('batch', 'Batch'), ('payment', 'Payment'), ('general', 'General')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ── Doubt ─────────────────────────────────────────────────────────────────────
class Doubt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    lecture = models.ForeignKey(Lecture, on_delete=models.SET_NULL, null=True, blank=True)
    question = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class DoubtReply(models.Model):
    doubt = models.ForeignKey(Doubt, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# ── Payment ───────────────────────────────────────────────────────────────────
class Payment(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed'), ('refunded', 'Refunded')]
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='INR')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    razorpay_order_id = models.CharField(max_length=200, blank=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True)
    razorpay_signature = models.CharField(max_length=500, blank=True)
    method = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ── FeeReceipt ────────────────────────────────────────────────────────────────
class FeeReceipt(models.Model):
    STATUS_CHOICES = [('paid', 'Paid'), ('pending', 'Pending'), ('cancelled', 'Cancelled')]
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    receipt_number = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    payment_id = models.CharField(max_length=200, blank=True)
    payment_method = models.CharField(max_length=50, default='Direct')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='paid')
    institute_name = models.CharField(max_length=200, default='Learn More Technologies')
    paid_date = models.DateTimeField(auto_now_add=True)


# ── ExamResult ────────────────────────────────────────────────────────────────
class ExamResult(models.Model):
    RESULT_CHOICES = [('pass', 'Pass'), ('fail', 'Fail'), ('absent', 'Absent')]
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    exam_name = models.CharField(max_length=200)
    subject = models.CharField(max_length=100, blank=True)
    total_marks = models.IntegerField(null=True)
    obtained_marks = models.IntegerField(null=True)
    percentage = models.FloatField(null=True)
    grade = models.CharField(max_length=5, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    exam_date = models.DateField(null=True, blank=True)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default='pass')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ── CodingQuestion ────────────────────────────────────────────────────────────
class CodingQuestion(models.Model):
    DIFFICULTY_CHOICES = [('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')]
    LANG_CHOICES = [('python', 'Python'), ('javascript', 'JavaScript'), ('java', 'Java'), ('c', 'C'), ('cpp', 'C++')]
    title = models.CharField(max_length=300)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='Easy')
    language = models.CharField(max_length=15, choices=LANG_CHOICES, default='python')
    starter_code = models.TextField(blank=True)
    solution_code = models.TextField(blank=True)
    expected_output = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)


# ── Schedule ──────────────────────────────────────────────────────────────────
class Schedule(models.Model):
    TYPE_CHOICES = [('live_class', 'Live Class'), ('recorded', 'Recorded'), ('test', 'Test'), ('doubt_session', 'Doubt Session'), ('assignment', 'Assignment')]
    PLATFORM_CHOICES = [('zoom', 'Zoom'), ('meet', 'Google Meet'), ('teams', 'Teams'), ('other', 'Other')]
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=300)
    subject = models.CharField(max_length=100, blank=True)
    instructor = models.CharField(max_length=200, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='live_class')
    days = models.JSONField(default=list)
    start_time = models.CharField(max_length=5)
    end_time = models.CharField(max_length=5)
    meeting_url = models.URLField(blank=True)
    meeting_id = models.CharField(max_length=100, blank=True)
    meeting_password = models.CharField(max_length=100, blank=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='zoom')
    date = models.DateField(null=True, blank=True)
    is_recurring = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ── ChatMessage ───────────────────────────────────────────────────────────────
class ChatMessage(models.Model):
    TYPE_CHOICES = [('text', 'Text'), ('image', 'Image'), ('file', 'File')]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='text')
    file_url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ── Poll ──────────────────────────────────────────────────────────────────────
class Poll(models.Model):
    question = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    voters = models.ManyToManyField(User, blank=True, related_name='voted_polls')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)


# ── Review ────────────────────────────────────────────────────────────────────
class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)  # 1-5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student')

    def __str__(self):
        return f'{self.student.name} - {self.course.title} ({self.rating}★)'


# ── Quiz ──────────────────────────────────────────────────────────────────────
class Quiz(models.Model):
    title = models.CharField(max_length=300)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    duration = models.IntegerField(default=30)
    total_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=40)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    options = models.JSONField(default=list)
    correct_answer = models.IntegerField(default=0)
    marks = models.IntegerField(default=1)
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    answers = models.JSONField(default=list)
    score = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    time_taken = models.IntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)


# ── Banner ────────────────────────────────────────────────────────────────────
class Banner(models.Model):
    ACTION_CHOICES = [
        ('none', 'No Action'),
        ('course', 'Navigate to Course'),
        ('batch', 'Navigate to Batch'),
    ]
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='banners/', blank=True, null=True)
    image_url = models.URLField(blank=True, help_text="Or paste image URL instead of upload")
    action_type = models.CharField(max_length=50, default='none', choices=ACTION_CHOICES)
    action_id = models.IntegerField(blank=True, null=True, help_text="ID of course or batch to open")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

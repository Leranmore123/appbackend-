from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import (
    User, Category, Course, CourseEnrollment, Batch, BatchEnrollment,
    Lecture, Note, Assignment, AssignmentSubmission, Attendance,
    Progress, Notification, Doubt, DoubtReply, Payment, FeeReceipt,
    ExamResult, CodingQuestion, Schedule, ChatMessage, Poll, PollOption,
    Quiz, QuizQuestion, QuizAttempt, Section, Review, Banner,
)


# ── Auth ──────────────────────────────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.CharField(required=False, default='student')

    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'password', 'role']

    def create(self, validated_data):
        role = validated_data.pop('role', 'student')
        user = User.objects.create_user(**validated_data)
        if role in ('admin', 'trainer'):
            user.role = 'admin'
            user.is_staff = True
            user.save(update_fields=['role', 'is_staff'])
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password')
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()
    _id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['_id', 'name', 'email', 'phone', 'avatar', 'role', 'token']

    def get_token(self, obj):
        if self.context.get('include_token', True):
            refresh = RefreshToken.for_user(obj)
            return str(refresh.access_token)
        return None

    def get__id(self, obj):
        return str(obj.id)


class UserProfileSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['_id', 'name', 'email', 'phone', 'avatar', 'role']

    def get__id(self, obj):
        return str(obj.id)


# ── Category ──────────────────────────────────────────────────────────────────
class CategorySerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['_id', 'name', 'icon', 'color', 'description', 'is_active', 'order', 'created_at']

    def get__id(self, obj):
        return str(obj.id)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['isActive'] = data.pop('is_active')
        return data


# ── Course ────────────────────────────────────────────────────────────────────
class CourseSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    instructor = serializers.SerializerMethodField()
    isFree = serializers.BooleanField(source='is_free', required=False)
    isActive = serializers.BooleanField(source='is_active', required=False)
    totalStudents = serializers.IntegerField(source='total_students', read_only=True)
    totalLectures = serializers.IntegerField(source='total_lectures', read_only=True)

    class Meta:
        model = Course
        fields = ['_id', 'title', 'description', 'thumbnail', 'category', 'language',
                  'instructor', 'price', 'isFree', 'rating', 'totalStudents',
                  'totalLectures', 'duration', 'isActive', 'created_at']

    def get__id(self, obj):
        return str(obj.id)

    def get_instructor(self, obj):
        return {'name': obj.instructor_name, 'avatar': obj.instructor_avatar, 'bio': obj.instructor_bio}

    def create(self, validated_data):
        # Extract nested instructor from initial_data
        instructor = self.initial_data.get('instructor', {})
        validated_data['instructor_name'] = instructor.get('name', '') if isinstance(instructor, dict) else ''
        validated_data['instructor_avatar'] = instructor.get('avatar', '') if isinstance(instructor, dict) else ''
        validated_data['instructor_bio'] = instructor.get('bio', '') if isinstance(instructor, dict) else ''
        return Course.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instructor = self.initial_data.get('instructor', {})
        if isinstance(instructor, dict):
            instance.instructor_name = instructor.get('name', instance.instructor_name)
            instance.instructor_avatar = instructor.get('avatar', instance.instructor_avatar)
            instance.instructor_bio = instructor.get('bio', instance.instructor_bio)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        thumbnail = data.get('thumbnail')
        if thumbnail and not (thumbnail.startswith('http://') or thumbnail.startswith('https://')):
            request = self.context.get('request')
            if request:
                data['thumbnail'] = request.build_absolute_uri(thumbnail)
            else:
                data['thumbnail'] = f"http://192.168.1.13:8000{thumbnail}"
        return data


# ── Batch ─────────────────────────────────────────────────────────────────────
class BatchSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    instructor = serializers.SerializerMethodField()
    isFree = serializers.BooleanField(source='is_free', required=False)
    isActive = serializers.BooleanField(source='is_active', required=False)
    isLive = serializers.BooleanField(source='is_live', required=False)
    totalStudents = serializers.IntegerField(source='total_students', read_only=True)
    allowed_emails = serializers.CharField(required=False, allow_blank=True)
    allowedEmails = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    isEnrolled = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = ['_id', 'name', 'description', 'thumbnail', 'category',
                  'price', 'isFree', 'allowed_emails', 'allowedEmails', 'sections', 'isEnrolled',
                  'start_date', 'end_date', 'instructor',
                  'totalStudents', 'isLive', 'live_stream_url', 'isActive', 'created_at']

    def get__id(self, obj):
        return str(obj.id)

    def get_instructor(self, obj):
        return {'name': obj.instructor_name, 'avatar': obj.instructor_avatar}

    def get_allowedEmails(self, obj):
        if hasattr(obj, 'get_allowed_email_list'):
            return obj.get_allowed_email_list()
        if not obj.allowed_emails:
            return []
        import re
        return [e.strip().lower() for e in re.split(r'[\s,;]+', obj.allowed_emails) if e.strip()]

    def get_sections(self, obj):
        # Return sections with their lectures
        qs = obj.sections.all().prefetch_related('lectures').order_by('order', 'id')
        return SectionSerializer(qs, many=True).data

    def get_isEnrolled(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        if getattr(request.user, 'role', '') == 'admin':
            return True
        user_email = (getattr(request.user, 'email', '') or '').strip().lower()
        username = (getattr(request.user, 'username', '') or '').strip().lower()
        allowed = self.get_allowedEmails(obj)
        if user_email in allowed or username in allowed:
            return True
        return obj.enrollments.filter(user=request.user).exists()

    def sync_enrollments(self, batch):
        if hasattr(batch, 'get_allowed_email_list'):
            allowed_list = batch.get_allowed_email_list()
        else:
            raw = getattr(batch, 'allowed_emails', '') or ''
            import re
            allowed_list = [e.strip().lower() for e in re.split(r'[\s,;]+', raw) if e.strip()]
        from .models import User, BatchEnrollment
        for email in allowed_list:
            users = User.objects.filter(email__iexact=email)
            for u in users:
                BatchEnrollment.objects.get_or_create(user=u, batch=batch)
        if allowed_list:
            batch.total_students = len(allowed_list)
            batch.save(update_fields=['total_students'])

    def create(self, validated_data):
        instructor = self.initial_data.get('instructor', {})
        validated_data['instructor_name'] = instructor.get('name', '') if isinstance(instructor, dict) else ''
        validated_data['instructor_avatar'] = instructor.get('avatar', '') if isinstance(instructor, dict) else ''
        batch = Batch.objects.create(**validated_data)
        self.sync_enrollments(batch)
        return batch

    def update(self, instance, validated_data):
        instructor = self.initial_data.get('instructor', {})
        if isinstance(instructor, dict):
            instance.instructor_name = instructor.get('name', instance.instructor_name)
            instance.instructor_avatar = instructor.get('avatar', instance.instructor_avatar)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        self.sync_enrollments(instance)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        thumbnail = data.get('thumbnail')
        if thumbnail and not (thumbnail.startswith('http://') or thumbnail.startswith('https://')):
            request = self.context.get('request')
            if request:
                data['thumbnail'] = request.build_absolute_uri(thumbnail)
            else:
                data['thumbnail'] = f"http://192.168.1.13:8000{thumbnail}"
        return data


# ── Lecture ───────────────────────────────────────────────────────────────────
class LectureSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    isFree = serializers.BooleanField(source='is_free', required=False)
    isPublished = serializers.BooleanField(source='is_published', required=False)
    videoUrl = serializers.CharField(source='video_url')
    videoType = serializers.CharField(source='video_type', required=False)
    sectionId = serializers.SerializerMethodField()
    batchId = serializers.SerializerMethodField()

    class Meta:
        model = Lecture
        fields = ['_id', 'title', 'description', 'videoUrl', 'videoType',
                  'duration', 'thumbnail', 'course', 'section', 'sectionId',
                  'batch', 'batchId', 'subject', 'chapter',
                  'isFree', 'isPublished', 'order', 'created_at']

    def get__id(self, obj):
        return str(obj.id)

    def get_sectionId(self, obj):
        return str(obj.section_id) if obj.section_id else None

    def get_batchId(self, obj):
        return str(obj.batch_id) if obj.batch_id else None


# ── Note ──────────────────────────────────────────────────────────────────────
class NoteSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    pdfUrl = serializers.CharField(source='pdf_url')
    isFree = serializers.BooleanField(source='is_free')
    downloadCount = serializers.IntegerField(source='download_count')

    class Meta:
        model = Note
        fields = ['_id', 'title', 'description', 'pdfUrl', 'subject',
                  'chapter', 'course', 'isFree', 'downloadCount', 'created_at']

    def get__id(self, obj):
        return str(obj.id)


# ── Assignment ────────────────────────────────────────────────────────────────
class AssignmentSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    dueDate = serializers.DateTimeField(source='due_date')
    totalMarks = serializers.IntegerField(source='total_marks')

    class Meta:
        model = Assignment
        fields = ['_id', 'title', 'description', 'course', 'batch',
                  'dueDate', 'totalMarks', 'created_at']

    def get__id(self, obj):
        return str(obj.id)


# ── Attendance ────────────────────────────────────────────────────────────────
class AttendanceSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ['_id', 'student', 'batch', 'date', 'status', 'marked_by', 'created_at']

    def get__id(self, obj):
        return str(obj.id)


# ── Notification ──────────────────────────────────────────────────────────────
class NotificationSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    isRead = serializers.BooleanField(source='is_read')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Notification
        fields = ['_id', 'title', 'message', 'type', 'isRead', 'link', 'createdAt']

    def get__id(self, obj):
        return str(obj.id)


# ── Doubt ─────────────────────────────────────────────────────────────────────
class DoubtReplySerializer(serializers.ModelSerializer):
    userName = serializers.CharField(source='user.name', read_only=True)
    userRole = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = DoubtReply
        fields = ['id', 'userName', 'userRole', 'message', 'created_at']


class DoubtSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    replies = DoubtReplySerializer(many=True, read_only=True)
    isResolved = serializers.BooleanField(source='is_resolved')
    studentName = serializers.CharField(source='student.name', read_only=True)

    class Meta:
        model = Doubt
        fields = ['_id', 'student', 'studentName', 'course', 'lecture', 'question', 'isResolved', 'replies', 'created_at']

    def get__id(self, obj):
        return str(obj.id)


# ── Payment ───────────────────────────────────────────────────────────────────
class PaymentSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['_id', 'student', 'course', 'batch', 'amount', 'currency',
                  'status', 'razorpay_order_id', 'razorpay_payment_id', 'created_at']

    def get__id(self, obj):
        return str(obj.id)


class AdminPaymentSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    student = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    razorpayPaymentId = serializers.CharField(source='razorpay_payment_id', read_only=True)

    class Meta:
        model = Payment
        fields = ['_id', 'student', 'course', 'batch', 'amount', 'currency',
                  'status', 'razorpayPaymentId', 'createdAt']

    def get__id(self, obj):
        return str(obj.id)

    def get_student(self, obj):
        if obj.student:
            return {'_id': str(obj.student.id), 'name': obj.student.name, 'email': obj.student.email, 'phone': obj.student.phone}
        return None

    def get_course(self, obj):
        if obj.course:
            return {'_id': str(obj.course.id), 'title': obj.course.title, 'thumbnail': obj.course.thumbnail}
        return None

    def get_batch(self, obj):
        if obj.batch:
            return {'_id': str(obj.batch.id), 'name': obj.batch.name, 'thumbnail': obj.batch.thumbnail}
        return None


# ── FeeReceipt ────────────────────────────────────────────────────────────────
class FeeReceiptSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    receiptNumber = serializers.CharField(source='receipt_number')
    paymentMethod = serializers.CharField(source='payment_method')
    instituteName = serializers.CharField(source='institute_name')
    paidDate = serializers.DateTimeField(source='paid_date')

    class Meta:
        model = FeeReceipt
        fields = ['_id', 'student', 'receiptNumber', 'amount', 'course', 'batch',
                  'payment_id', 'paymentMethod', 'status', 'instituteName', 'paidDate']

    def get__id(self, obj):
        return str(obj.id)


# ── ExamResult ────────────────────────────────────────────────────────────────
class ExamResultSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    examName = serializers.CharField(source='exam_name')
    totalMarks = serializers.IntegerField(source='total_marks')
    obtainedMarks = serializers.IntegerField(source='obtained_marks')
    examDate = serializers.DateField(source='exam_date')

    class Meta:
        model = ExamResult
        fields = ['_id', 'student', 'course', 'examName', 'subject',
                  'totalMarks', 'obtainedMarks', 'percentage', 'grade',
                  'rank', 'examDate', 'result', 'remarks', 'created_at']

    def get__id(self, obj):
        return str(obj.id)


# ── CodingQuestion ────────────────────────────────────────────────────────────
class CodingQuestionSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    starterCode = serializers.CharField(source='starter_code')
    solutionCode = serializers.CharField(source='solution_code')
    expectedOutput = serializers.CharField(source='expected_output')

    class Meta:
        model = CodingQuestion
        fields = ['_id', 'title', 'description', 'difficulty', 'language',
                  'starterCode', 'solutionCode', 'expectedOutput', 'course',
                  'tags', 'created_at']

    def get__id(self, obj):
        return str(obj.id)


# ── Schedule ──────────────────────────────────────────────────────────────────
class ScheduleSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    startTime = serializers.CharField(source='start_time')
    endTime = serializers.CharField(source='end_time')
    meetingUrl = serializers.CharField(source='meeting_url', required=False, allow_blank=True, default='')
    isRecurring = serializers.BooleanField(source='is_recurring', required=False, default=True)
    isActive = serializers.BooleanField(source='is_active', required=False, default=True)
    meetingId = serializers.CharField(source='meeting_id', required=False, allow_blank=True, default='')
    meetingPassword = serializers.CharField(source='meeting_password', required=False, allow_blank=True, default='')

    class Meta:
        model = Schedule
        fields = ['_id', 'course', 'batch', 'title', 'subject', 'instructor',
                  'type', 'days', 'startTime', 'endTime', 'meetingUrl',
                  'meetingId', 'meetingPassword', 'platform', 'date',
                  'isRecurring', 'isActive', 'created_at']

    def get__id(self, obj):
        return str(obj.id)


# ── Chat ──────────────────────────────────────────────────────────────────────
class ChatMessageSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    sender_name = serializers.CharField(source='sender.name', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['_id', 'course', 'sender', 'sender_name', 'message',
                  'type', 'file_url', 'is_read', 'reply_to', 'created_at']

    def get__id(self, obj):
        return str(obj.id)


# ── Poll ──────────────────────────────────────────────────────────────────────
class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = ['id', 'text', 'votes']


class PollSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    options = PollOptionSerializer(many=True, read_only=True)
    isActive = serializers.BooleanField(source='is_active')

    class Meta:
        model = Poll
        fields = ['_id', 'question', 'options', 'course', 'created_by',
                  'isActive', 'expires_at', 'created_at']

    def get__id(self, obj):
        return str(obj.id)


# ── Quiz ──────────────────────────────────────────────────────────────────────
class QuizQuestionSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    correctAnswer = serializers.IntegerField(source='correct_answer')

    class Meta:
        model = QuizQuestion
        fields = ['_id', 'question', 'options', 'correctAnswer', 'marks', 'explanation']

    def get__id(self, obj):
        return str(obj.id)


class QuizSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    questions = QuizQuestionSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    totalMarks = serializers.IntegerField(source='total_marks')
    passingMarks = serializers.IntegerField(source='passing_marks')
    isActive = serializers.BooleanField(source='is_active')

    class Meta:
        model = Quiz
        fields = ['_id', 'title', 'category', 'category_id', 'course', 'batch',
                  'duration', 'totalMarks', 'passingMarks', 'isActive',
                  'questions', 'created_at', 'updated_at']

    def get__id(self, obj):
        return str(obj.id)

    def create(self, validated_data):
        questions_data = self.initial_data.get('questions', [])
        quiz = Quiz.objects.create(**validated_data)
        for i, q in enumerate(questions_data):
            QuizQuestion.objects.create(
                quiz=quiz,
                question=q.get('question', ''),
                options=q.get('options', []),
                correct_answer=q.get('correctAnswer', 0),
                marks=q.get('marks', 1),
                explanation=q.get('explanation', ''),
                order=i,
            )
        return quiz

    def update(self, instance, validated_data):
        questions_data = self.initial_data.get('questions', [])
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if questions_data:
            instance.questions.all().delete()
            for i, q in enumerate(questions_data):
                QuizQuestion.objects.create(
                    quiz=instance,
                    question=q.get('question', ''),
                    options=q.get('options', []),
                    correct_answer=q.get('correctAnswer', 0),
                    marks=q.get('marks', 1),
                    explanation=q.get('explanation', ''),
                    order=i,
                )
        return instance


# ── Section ───────────────────────────────────────────────────────────────────
class SectionSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    lectures = serializers.SerializerMethodField()
    courseId = serializers.SerializerMethodField()
    batchId = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ['_id', 'title', 'order', 'courseId', 'batchId', 'lectures', 'created_at']

    def get__id(self, obj):
        return str(obj.id)

    def get_courseId(self, obj):
        return str(obj.course_id) if obj.course_id else None

    def get_batchId(self, obj):
        return str(obj.batch_id) if obj.batch_id else None

    def get_lectures(self, obj):
        qs = obj.lectures.all().order_by('order', 'id')
        return LectureSerializer(qs, many=True).data


# ── Review ────────────────────────────────────────────────────────────────────
class ReviewSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    studentName = serializers.CharField(source='student.name', read_only=True)
    studentAvatar = serializers.CharField(source='student.avatar', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Review
        fields = ['_id', 'rating', 'comment', 'studentName', 'studentAvatar', 'createdAt']

    def get__id(self, obj):
        return str(obj.id)


# ── Banner ────────────────────────────────────────────────────────────────────
class BannerSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField()
    imageUrl = serializers.SerializerMethodField()
    actionType = serializers.CharField(source='action_type')
    actionId = serializers.IntegerField(source='action_id', required=False, allow_null=True)
    isActive = serializers.BooleanField(source='is_active', required=False)

    class Meta:
        model = Banner
        fields = ['_id', 'title', 'subtitle', 'imageUrl', 'actionType', 'actionId', 'isActive', 'created_at']

    def get__id(self, obj):
        return str(obj.id)

    def get_imageUrl(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return f"http://192.168.1.13:8000{obj.image.url}"
        elif obj.image_url:
            return obj.image_url
        return None

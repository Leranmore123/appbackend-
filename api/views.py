import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.db import models

from .models import (
    User, Category, Course, CourseEnrollment, Batch, BatchEnrollment,
    Lecture, Note, Assignment, AssignmentSubmission, Attendance,
    Notification, Doubt, DoubtReply, Payment, FeeReceipt,
    ExamResult, Schedule, ChatMessage, Quiz, QuizAttempt, Section, Review, Banner,
)
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer, UserProfileSerializer,
    CategorySerializer, CourseSerializer, BatchSerializer, LectureSerializer,
    NoteSerializer, AssignmentSerializer, AttendanceSerializer,
    NotificationSerializer, DoubtSerializer, PaymentSerializer,
    SectionSerializer, ReviewSerializer,
    FeeReceiptSerializer, ExamResultSerializer, ScheduleSerializer,
    ChatMessageSerializer, QuizSerializer, BannerSerializer,
)
from .permissions import IsAdmin


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user, context={'include_token': True}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            return Response(UserSerializer(user, context={'include_token': True}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)


# ── Categories ────────────────────────────────────────────────────────────────

class CategoryListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdmin()]

    def get(self, request):
        # Admin sees all, students see only active
        if request.user and request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'admin':
            cats = Category.objects.all()
        else:
            cats = Category.objects.filter(is_active=True)
        return Response(CategorySerializer(cats, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    permission_classes = [IsAdmin]

    def _get_obj(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def put(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': 'Deleted'})


# ── Quiz ──────────────────────────────────────────────────────────────────────

class QuizListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAdmin()]
        return [IsAdmin()]

    def get(self, request):
        qs = Quiz.objects.all()
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category__id=category)
        return Response(QuizSerializer(qs, many=True).data)

    def post(self, request):
        serializer = QuizSerializer(data=request.data)
        if serializer.is_valid():
            quiz = serializer.save()
            return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdmin()]

    def _get_obj(self, pk):
        try:
            return Quiz.objects.get(pk=pk)
        except Quiz.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(QuizSerializer(obj).data)

    def put(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = QuizSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(QuizSerializer(obj).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': 'Deleted'})


class QuizByCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        qs = Quiz.objects.filter(course__id=course_id)
        return Response(QuizSerializer(qs, many=True).data)


class QuizByCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, category_id):
        qs = Quiz.objects.filter(category__id=category_id, is_active=True)
        return Response(QuizSerializer(qs, many=True).data)


class QuizAllStudentView(APIView):
    """All active quizzes for students."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Quiz.objects.filter(is_active=True).select_related('category')
        return Response(QuizSerializer(qs, many=True).data)


class QuizSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            quiz = Quiz.objects.get(pk=pk)
        except Quiz.DoesNotExist:
            return Response({'message': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)

        answers = request.data.get('answers', [])
        questions = list(quiz.questions.all())
        score = 0
        results = []

        for i, q in enumerate(questions):
            user_answer = answers[i] if i < len(answers) else -1
            correct = q.correct_answer
            is_correct = user_answer == correct
            if is_correct:
                score += q.marks
            results.append({
                'question': q.question,
                'userAnswer': user_answer,
                'correctAnswer': correct,
                'isCorrect': is_correct,
                'explanation': q.explanation,
            })

        percentage = (score / quiz.total_marks * 100) if quiz.total_marks else 0
        passed = score >= quiz.passing_marks

        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            answers=answers,
            score=score,
            percentage=percentage,
            passed=passed,
            time_taken=request.data.get('timeTaken'),
        )

        return Response({
            'score': score,
            'totalMarks': quiz.total_marks,
            'percentage': round(percentage, 2),
            'passed': passed,
            'results': results,
            'attemptId': str(attempt.id),
        })


# ── Courses ───────────────────────────────────────────────────────────────────

class CourseListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdmin()]

    def get(self, request):
        qs = Course.objects.filter(is_active=True)
        # Search by title
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(title__icontains=search)
        # Filter by category
        category = request.query_params.get('category')
        if category and category != 'All':
            qs = qs.filter(category=category)
        return Response(CourseSerializer(qs, many=True, context={'request': request}).data)

    def post(self, request):
        serializer = CourseSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseFeaturedView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Course.objects.filter(is_active=True).order_by('-total_students')[:6]
        return Response(CourseSerializer(qs, many=True, context={'request': request}).data)


class CourseDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdmin()]

    def _get_obj(self, pk):
        try:
            return Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CourseSerializer(obj, context={'request': request}).data)

    def put(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CourseSerializer(obj, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': 'Deleted'})


class CourseEnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        enrollment, created = CourseEnrollment.objects.get_or_create(
            user=request.user, course=course
        )
        if created:
            course.total_students += 1
            course.save(update_fields=['total_students'])
        return Response({'message': 'Enrolled successfully', 'enrolled': True})


# ── Batches ───────────────────────────────────────────────────────────────────

class BatchListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdmin()]

    def get(self, request):
        qs = Batch.objects.filter(is_active=True)
        return Response(BatchSerializer(qs, many=True, context={'request': request}).data)

    def post(self, request):
        serializer = BatchSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BatchDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdmin()]

    def _get_obj(self, pk):
        try:
            return Batch.objects.get(pk=pk)
        except Batch.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(BatchSerializer(obj, context={'request': request}).data)

    def put(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BatchSerializer(obj, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': 'Deleted'})


class BatchEnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            batch = Batch.objects.get(pk=pk)
        except Batch.DoesNotExist:
            return Response({'message': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)
        enrollment, created = BatchEnrollment.objects.get_or_create(
            user=request.user, batch=batch
        )
        if created:
            batch.total_students += 1
            batch.save(update_fields=['total_students'])
        return Response({'message': 'Enrolled successfully', 'enrolled': True})


class MyBatchesView(APIView):
    """Return all batches the logged-in student is enrolled in."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        enrolled_batch_ids = BatchEnrollment.objects.filter(
            user=request.user
        ).values_list('batch_id', flat=True)
        batches = Batch.objects.filter(id__in=enrolled_batch_ids, is_active=True)
        return Response(BatchSerializer(batches, many=True, context={'request': request}).data)


# ── Lectures ──────────────────────────────────────────────────────────────────

class LectureByCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        qs = Lecture.objects.filter(course__id=course_id)
        return Response(LectureSerializer(qs, many=True).data)


class LectureDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            obj = Lecture.objects.get(pk=pk)
        except Lecture.DoesNotExist:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(LectureSerializer(obj).data)

    def delete(self, request, pk):
        if not (request.user.role == 'admin'):
            return Response({'message': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        try:
            obj = Lecture.objects.get(pk=pk)
            # Update course lecture count
            if obj.course:
                Course.objects.filter(pk=obj.course.pk).update(
                    total_lectures=models.F('total_lectures') - 1
                )
            obj.delete()
            return Response({'message': 'Deleted'})
        except Lecture.DoesNotExist:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        if not (request.user.role == 'admin'):
            return Response({'message': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        try:
            obj = Lecture.objects.get(pk=pk)
            # Allow updating section, title, order etc.
            section_id = request.data.get('section')
            if 'section' in request.data:
                obj.section_id = section_id  # None clears the section
            if 'title' in request.data:
                obj.title = request.data['title']
            if 'order' in request.data:
                obj.order = int(request.data['order'])
            if 'isFree' in request.data:
                obj.is_free = str(request.data['isFree']).lower() == 'true'
            obj.save()
            from .serializers import LectureSerializer
            return Response(LectureSerializer(obj).data)
        except Lecture.DoesNotExist:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


class LectureCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        data = request.data.copy()
        # Handle sectionId → section field mapping from frontend
        if 'sectionId' in data and data['sectionId']:
            data['section'] = data['sectionId']
        serializer = LectureSerializer(data=data)
        if serializer.is_valid():
            lecture = serializer.save()
            # Update course total_lectures count
            if lecture.course:
                Course.objects.filter(pk=lecture.course.pk).update(
                    total_lectures=models.F('total_lectures') + 1
                )
            return Response(LectureSerializer(lecture).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Notes ─────────────────────────────────────────────────────────────────────

class NotesByCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        qs = Note.objects.filter(course__id=course_id)
        return Response(NoteSerializer(qs, many=True).data)


class NoteCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── User ──────────────────────────────────────────────────────────────────────

class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.all()
        return Response(UserProfileSerializer(users, many=True).data)


class UserRoleUpdateView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        role = request.data.get('role')
        if role not in ['student', 'admin']:
            return Response({'message': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)
        user.role = role
        user.save(update_fields=['role'])
        return Response(UserProfileSerializer(user).data)


# ── Attendance ────────────────────────────────────────────────────────────────

class AttendanceCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = AttendanceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttendanceByBatchView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, batch_id):
        qs = Attendance.objects.filter(batch__id=batch_id).select_related('student')
        return Response(AttendanceSerializer(qs, many=True).data)


class MyAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Attendance.objects.filter(student=request.user)
        return Response(AttendanceSerializer(qs, many=True).data)


# ── Assignments ───────────────────────────────────────────────────────────────

class AssignmentListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get(self, request):
        qs = Assignment.objects.all()
        return Response(AssignmentSerializer(qs, many=True).data)

    def post(self, request):
        serializer = AssignmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            assignment = Assignment.objects.get(pk=pk)
        except Assignment.DoesNotExist:
            return Response({'message': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)
        submission = AssignmentSubmission.objects.create(
            assignment=assignment,
            student=request.user,
            file_url=request.data.get('fileUrl', ''),
            file_name=request.data.get('fileName', ''),
        )
        return Response({'message': 'Submitted', 'id': submission.id}, status=status.HTTP_201_CREATED)


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(user=request.user).order_by('-created_at')
        return Response(NotificationSerializer(qs, many=True).data)


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'})


class NotificationBroadcastView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        title = request.data.get('title', '')
        message = request.data.get('message', '')
        notif_type = request.data.get('type', 'general')
        users = User.objects.filter(is_active=True)
        notifications = [
            Notification(user=u, title=title, message=message, type=notif_type)
            for u in users
        ]
        Notification.objects.bulk_create(notifications)
        return Response({'message': f'Broadcast sent to {len(notifications)} users'})


# ── Doubts ────────────────────────────────────────────────────────────────────

class DoubtCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        serializer = DoubtSerializer(data=data)
        if serializer.is_valid():
            serializer.save(student=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyDoubtsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Doubt.objects.filter(student=request.user).prefetch_related('replies__user').order_by('-created_at')
        return Response(DoubtSerializer(qs, many=True).data)


class AllDoubtsAdminView(APIView):
    """Admin can see all doubts from all students."""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Doubt.objects.all().select_related('student').prefetch_related('replies__user').order_by('-created_at')
        return Response(DoubtSerializer(qs, many=True).data)


class DoubtReplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            doubt = Doubt.objects.get(pk=pk)
        except Doubt.DoesNotExist:
            return Response({'message': 'Doubt not found'}, status=status.HTTP_404_NOT_FOUND)
        reply = DoubtReply.objects.create(
            doubt=doubt,
            user=request.user,
            message=request.data.get('message', ''),
        )
        return Response({'message': 'Reply added', 'id': reply.id}, status=status.HTTP_201_CREATED)


# ── Payments ──────────────────────────────────────────────────────────────────

class PaymentHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Payment.objects.filter(student=request.user).order_by('-created_at')
        return Response(PaymentSerializer(qs, many=True).data)


class AllPaymentsAdminView(APIView):
    """Admin: get all payments with optional status filter."""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Payment.objects.all().select_related('student', 'course', 'batch').order_by('-created_at')
        status_filter = request.query_params.get('status')
        if status_filter and status_filter != 'all':
            qs = qs.filter(status=status_filter)
        from .serializers import AdminPaymentSerializer
        try:
            data = AdminPaymentSerializer(qs, many=True).data
        except Exception:
            data = PaymentSerializer(qs, many=True).data
        return Response(data)


class StudentPaymentsAdminView(APIView):
    """Admin: get payments for a specific student."""
    permission_classes = [IsAdmin]

    def get(self, request, student_id):
        qs = Payment.objects.filter(student_id=student_id).select_related('student', 'course', 'batch').order_by('-created_at')
        from .serializers import AdminPaymentSerializer
        try:
            data = AdminPaymentSerializer(qs, many=True).data
        except Exception:
            data = PaymentSerializer(qs, many=True).data
        return Response(data)


# ── Exam Results ──────────────────────────────────────────────────────────────

class MyExamResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ExamResult.objects.filter(student=request.user)
        return Response(ExamResultSerializer(qs, many=True).data)


class ExamResultCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = ExamResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Schedule ──────────────────────────────────────────────────────────────────

class MyScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        enrolled_course_ids = CourseEnrollment.objects.filter(
            user=request.user
        ).values_list('course_id', flat=True)
        qs = Schedule.objects.filter(course__id__in=enrolled_course_ids, is_active=True)
        return Response(ScheduleSerializer(qs, many=True).data)


class ScheduleByCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        qs = Schedule.objects.filter(course__id=course_id, is_active=True)
        return Response(ScheduleSerializer(qs, many=True).data)


class ScheduleCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = ScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleDetailView(APIView):
    permission_classes = [IsAdmin]

    def _get_obj(self, pk):
        try:
            return Schedule.objects.get(pk=pk)
        except Schedule.DoesNotExist:
            return None

    def put(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ScheduleSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self._get_obj(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': 'Deleted'})


# ── Fee Receipts ──────────────────────────────────────────────────────────────

class MyFeeReceiptsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = FeeReceipt.objects.filter(student=request.user)
        return Response(FeeReceiptSerializer(qs, many=True).data)


class AllFeeReceiptsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = FeeReceipt.objects.all()
        return Response(FeeReceiptSerializer(qs, many=True).data)


class FeeReceiptCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = FeeReceiptSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatByCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        qs = ChatMessage.objects.filter(course__id=course_id).order_by('created_at')
        return Response(ChatMessageSerializer(qs, many=True).data)


class ChatCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Leaderboard ───────────────────────────────────────────────────────────────

class MyCourseProgressView(APIView):
    """Returns enrolled courses with lecture completion info."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        enrollments = CourseEnrollment.objects.filter(
            user=request.user
        ).select_related('course').prefetch_related('course__lectures')

        result = []
        for enrollment in enrollments:
            course = enrollment.course
            total = course.lectures.count()
            result.append({
                '_id': str(enrollment.id),
                'course': {
                    '_id': str(course.id),
                    'title': course.title,
                    'thumbnail': course.thumbnail,
                    'totalLectures': total,
                },
                'completionPercent': 0,
                'completedLectures': [],
                'enrolledAt': enrollment.enrolled_at.isoformat(),
            })
        return Response(result)


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum, Count, Avg
        leaderboard = (
            QuizAttempt.objects
            .values('student__id', 'student__name', 'student__avatar')
            .annotate(
                totalScore=Sum('score'),
                totalAttempts=Count('id'),
                avgPercentage=Avg('percentage'),
            )
            .order_by('-totalScore')[:20]
        )
        data = [
            {
                '_id': str(entry['student__id']),
                'name': entry['student__name'],
                'avatar': entry['student__avatar'],
                'totalScore': entry['totalScore'] or 0,
                'totalAttempts': entry['totalAttempts'],
                'avgPercentage': round(entry['avgPercentage'] or 0, 2),
            }
            for entry in leaderboard
        ]
        return Response(data)


# ── Sections ──────────────────────────────────────────────────────────────────

class SectionListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        # Auto-assign any unsectioned lectures so they always display in mobile app
        unassigned = Lecture.objects.filter(course=course, section__isnull=True)
        if unassigned.exists():
            default_sec = Section.objects.filter(course=course).first()
            if not default_sec:
                default_sec = Section.objects.create(course=course, title='Course Lectures', order=0)
            unassigned.update(section=default_sec)

        qs = Section.objects.filter(course=course).prefetch_related('lectures').order_by('order', 'id')
        return Response(SectionSerializer(qs, many=True).data)

    def post(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        section = Section.objects.create(
            course=course,
            title=request.data.get('title', 'New Section'),
            order=request.data.get('order', 0),
        )
        return Response(SectionSerializer(section).data, status=status.HTTP_201_CREATED)


class SectionDetailView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, pk):
        try:
            obj = Section.objects.get(pk=pk)
        except Section.DoesNotExist:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.title = request.data.get('title', obj.title)
        obj.order = request.data.get('order', obj.order)
        obj.save()
        return Response(SectionSerializer(obj).data)

    def delete(self, request, pk):
        try:
            obj = Section.objects.get(pk=pk)
            obj.delete()
            return Response({'message': 'Deleted'})
        except Section.DoesNotExist:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


# ── Reviews ───────────────────────────────────────────────────────────────────

class ReviewListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, course_id):
        qs = Review.objects.filter(course__id=course_id).select_related('student').order_by('-created_at')
        return Response(ReviewSerializer(qs, many=True).data)

    def post(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        rating = int(request.data.get('rating', 5))
        comment = request.data.get('comment', '')
        review, created = Review.objects.update_or_create(
            course=course, student=request.user,
            defaults={'rating': rating, 'comment': comment}
        )
        # Update course average rating
        from django.db.models import Avg
        avg = Review.objects.filter(course=course).aggregate(Avg('rating'))['rating__avg']
        course.rating = round(avg or 5.0, 1)
        course.save(update_fields=['rating'])
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadImageView(APIView):
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('image') or request.FILES.get('file')
        if not file:
            return Response({'message': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(upload_dir, exist_ok=True)

        safe_name = f"{int(time.time())}_{file.name.replace(' ', '_')}"
        file_path = os.path.join(upload_dir, safe_name)
        with open(file_path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        file_url = f"{request.scheme}://{request.get_host()}{settings.MEDIA_URL}thumbnails/{safe_name}"
        return Response({
            'url': file_url,
            'fileName': safe_name,
            'message': 'Image uploaded successfully'
        }, status=status.HTTP_201_CREATED)


class UploadPDFView(APIView):
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, course_id):
        file = request.FILES.get('file') or request.FILES.get('pdf')
        if not file:
            return Response({'message': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'notes', str(course_id))
        os.makedirs(upload_dir, exist_ok=True)

        # Sanitize filename
        safe_name = file.name.replace(' ', '_')
        file_path = os.path.join(upload_dir, safe_name)
        with open(file_path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        file_url = f"{request.scheme}://{request.get_host()}{settings.MEDIA_URL}notes/{course_id}/{safe_name}"

        # Create Note object in DB so it appears in student view
        title = request.data.get('title', safe_name)
        note = Note.objects.create(
            title=title,
            subject=request.data.get('subject', ''),
            chapter=request.data.get('chapter', ''),
            pdf_url=file_url,
            is_free=request.data.get('isFree', 'false').lower() == 'true',
            course_id=course_id,
        )
        from .serializers import NoteSerializer
        return Response({
            'url': file_url,
            'fileName': safe_name,
            'note': NoteSerializer(note).data,
        }, status=status.HTTP_201_CREATED)


# ── Course Enrollment Check ───────────────────────────────────────────────────

class CourseEnrollCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        enrolled = CourseEnrollment.objects.filter(user=request.user, course_id=pk).exists()
        return Response({'enrolled': enrolled})


# ── Course Doubts ─────────────────────────────────────────────────────────────

class CourseDoubtListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        qs = Doubt.objects.filter(course_id=course_id).select_related('student').prefetch_related('replies__user').order_by('-created_at')
        return Response(DoubtSerializer(qs, many=True).data)

    def post(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        doubt = Doubt.objects.create(
            student=request.user,
            course=course,
            question=request.data.get('question', ''),
        )
        return Response(DoubtSerializer(doubt).data, status=status.HTTP_201_CREATED)


class CreateOrderView(APIView):
    """Create Razorpay order for paid course/batch enrollment."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import razorpay
        from django.conf import settings as django_settings

        course_id = request.data.get('courseId')
        batch_id = request.data.get('batchId')
        amount = 0
        title = ''
        item_type = ''

        if course_id:
            try:
                course = Course.objects.get(pk=course_id)
            except Course.DoesNotExist:
                return Response({'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
            amount = float(course.price)
            title = course.title
            item_type = 'course'
        elif batch_id:
            try:
                batch = Batch.objects.get(pk=batch_id)
            except Batch.DoesNotExist:
                return Response({'message': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)
            amount = float(batch.price)
            title = batch.name
            item_type = 'batch'
        else:
            return Response({'message': 'courseId or batchId required'}, status=status.HTTP_400_BAD_REQUEST)

        # Free item — enroll directly
        if amount == 0:
            if course_id:
                course = Course.objects.get(pk=course_id)
                enrollment, created = CourseEnrollment.objects.get_or_create(user=request.user, course=course)
                if created:
                    Course.objects.filter(pk=course_id).update(total_students=models.F('total_students') + 1)
            if batch_id:
                batch = Batch.objects.get(pk=batch_id)
                enrollment, created = BatchEnrollment.objects.get_or_create(user=request.user, batch=batch)
                if created:
                    Batch.objects.filter(pk=batch_id).update(total_students=models.F('total_students') + 1)
            return Response({'free': True, 'message': f'Enrolled in "{title}" for free!'})

        # Create Razorpay order
        try:
            client = razorpay.Client(
                auth=(django_settings.RAZORPAY_KEY_ID, django_settings.RAZORPAY_KEY_SECRET)
            )
            order = client.order.create({
                'amount': int(amount * 100),  # paise
                'currency': 'INR',
                'receipt': f'rcpt_{request.user.id}_{course_id or batch_id}',
                'notes': {
                    'userId': str(request.user.id),
                    'courseId': str(course_id) if course_id else '',
                    'batchId': str(batch_id) if batch_id else '',
                    'itemType': item_type,
                },
            })

            # Save pending payment
            Payment.objects.create(
                student=request.user,
                course_id=course_id if course_id else None,
                batch_id=batch_id if batch_id else None,
                amount=amount,
                razorpay_order_id=order['id'],
                status='pending',
            )

            return Response({
                'orderId': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'keyId': django_settings.RAZORPAY_KEY_ID,
                'name': 'Learn More Technologies',
                'description': title,
                'prefill': {
                    'name': request.user.name,
                    'email': request.user.email,
                    'contact': request.user.phone,
                },
                'notes': {
                    'website': 'https://learnmoretech.in',
                },
            })
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyPaymentView(APIView):
    """Verify Razorpay payment signature and enroll student."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import razorpay
        import hmac
        import hashlib
        from django.conf import settings as django_settings

        razorpay_order_id = request.data.get('razorpayOrderId')
        razorpay_payment_id = request.data.get('razorpayPaymentId')
        razorpay_signature = request.data.get('razorpaySignature')
        course_id = request.data.get('courseId')
        batch_id = request.data.get('batchId')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({'message': 'Missing payment data'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify signature
        body = f'{razorpay_order_id}|{razorpay_payment_id}'
        mac = hmac.new(
            django_settings.RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        )
        expected = mac.hexdigest()

        if expected != razorpay_signature:
            Payment.objects.filter(razorpay_order_id=razorpay_order_id).update(status='failed')
            return Response({'message': 'Invalid payment signature'}, status=status.HTTP_400_BAD_REQUEST)

        # Update payment record
        Payment.objects.filter(razorpay_order_id=razorpay_order_id).update(
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            status='success',
        )

        # Enroll student
        enrolled_title = ''
        if course_id:
            try:
                course = Course.objects.get(pk=course_id)
                enrollment, created = CourseEnrollment.objects.get_or_create(user=request.user, course=course)
                if created:
                    Course.objects.filter(pk=course_id).update(total_students=models.F('total_students') + 1)
                enrolled_title = course.title
            except Course.DoesNotExist:
                pass
        if batch_id:
            try:
                batch = Batch.objects.get(pk=batch_id)
                enrollment, created = BatchEnrollment.objects.get_or_create(user=request.user, batch=batch)
                if created:
                    Batch.objects.filter(pk=batch_id).update(total_students=models.F('total_students') + 1)
                enrolled_title = batch.name
            except Batch.DoesNotExist:
                pass

        # Send notification
        Notification.objects.create(
            user=request.user,
            title='Payment Successful! 🎉',
            message=f'You have been enrolled in "{enrolled_title}". Start learning now!',
            type='payment',
        )

        return Response({'success': True, 'message': 'Payment verified & enrolled successfully!'})


class UploadVideoView(APIView):
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, course_id):
        file = request.FILES.get('video')

        # If a file is provided, save to local disk
        if file:
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(course_id))
            os.makedirs(upload_dir, exist_ok=True)

            # Sanitize filename
            safe_name = file.name.replace(' ', '_')
            file_path = os.path.join(upload_dir, safe_name)
            with open(file_path, 'wb+') as dest:
                for chunk in file.chunks():
                    dest.write(chunk)

            video_url = f"{request.scheme}://{request.get_host()}{settings.MEDIA_URL}videos/{course_id}/{safe_name}"

            # Create lecture
            title = request.data.get('title', safe_name)
            section_id = request.data.get('sectionId') or request.data.get('section_id')
            lecture = Lecture.objects.create(
                title=title,
                description=request.data.get('description', ''),
                video_url=video_url,
                video_type='direct',
                duration=request.data.get('duration', ''),
                subject=request.data.get('subject', ''),
                chapter=request.data.get('chapter', ''),
                is_free=request.data.get('isFree', 'false').lower() == 'true',
                order=int(request.data.get('order', 0)),
                course_id=course_id,
                section_id=section_id if section_id else None,
            )
            # Update course lecture count
            Course.objects.filter(pk=course_id).update(
                total_lectures=models.F('total_lectures') + 1
            )
            from .serializers import LectureSerializer
            return Response({
                'message': 'Video uploaded successfully!',
                'lecture': LectureSerializer(lecture).data,
                'videoUrl': video_url,
            }, status=status.HTTP_201_CREATED)

        # No file — just save URL (YouTube/Drive link)
        video_url = request.data.get('videoUrl') or request.data.get('url')
        if not video_url:
            return Response({'message': 'No video file or URL provided'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'url': video_url, 'courseId': str(course_id)})


# ── Coding Questions ──────────────────────────────────────────────────────────

class CodingQuestionListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get(self, request):
        from .serializers import CodingQuestionSerializer
        qs = CodingQuestion.objects.all()
        language = request.query_params.get('language')
        difficulty = request.query_params.get('difficulty')
        if language:
            qs = qs.filter(language=language)
        if difficulty and difficulty != 'All':
            qs = qs.filter(difficulty=difficulty)
        return Response(CodingQuestionSerializer(qs, many=True).data)

    def post(self, request):
        from .serializers import CodingQuestionSerializer
        serializer = CodingQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CodingQuestionDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdmin()]

    def _get(self, pk):
        try:
            return CodingQuestion.objects.get(pk=pk)
        except CodingQuestion.DoesNotExist:
            return None

    def get(self, request, pk):
        from .serializers import CodingQuestionSerializer
        obj = self._get(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CodingQuestionSerializer(obj).data)

    def delete(self, request, pk):
        obj = self._get(pk)
        if not obj:
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': 'Deleted'})


# ── Polls ─────────────────────────────────────────────────────────────────────

class PollListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get(self, request):
        from .serializers import PollSerializer
        course_id = request.query_params.get('course')
        qs = Poll.objects.filter(is_active=True).prefetch_related('options')
        if course_id:
            qs = qs.filter(course__id=course_id)
        return Response(PollSerializer(qs, many=True).data)

    def post(self, request):
        from .serializers import PollSerializer
        options = request.data.get('options', [])
        poll = Poll.objects.create(
            question=request.data.get('question', ''),
            course_id=request.data.get('course'),
            created_by=request.user,
            is_active=True,
        )
        for opt_text in options:
            PollOption.objects.create(poll=poll, text=opt_text)
        return Response(PollSerializer(poll).data, status=status.HTTP_201_CREATED)


class PollVoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        option_id = request.data.get('optionId')
        try:
            poll = Poll.objects.get(pk=pk)
            option = PollOption.objects.get(pk=option_id, poll=poll)
        except (Poll.DoesNotExist, PollOption.DoesNotExist):
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user in poll.voters.all():
            return Response({'message': 'Already voted'}, status=status.HTTP_400_BAD_REQUEST)

        option.votes += 1
        option.save()
        poll.voters.add(request.user)
        return Response({'message': 'Vote recorded', 'votes': option.votes})


# ── Banner ────────────────────────────────────────────────────────────────────
class BannerListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdmin()]

    def get(self, request):
        if request.user and request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'admin':
            qs = Banner.objects.all()
        else:
            qs = Banner.objects.filter(is_active=True)
        return Response(BannerSerializer(qs, many=True, context={'request': request}).data)

    def post(self, request):
        serializer = BannerSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

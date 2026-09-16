from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path('auth/register', views.RegisterView.as_view(), name='register'),
    path('auth/login', views.LoginView.as_view(), name='login'),
    path('auth/google/', views.GoogleAuthView.as_view(), name='auth-google'),
    path('auth/google', views.GoogleAuthView.as_view(), name='auth-google-noslash'),
    path('auth/profile', views.ProfileView.as_view(), name='auth-profile'),

    # ── Categories ────────────────────────────────────────────────────────────
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),

    # ── Quiz ──────────────────────────────────────────────────────────────────
    path('quiz/', views.QuizListView.as_view(), name='quiz-list'),
    path('quiz/course/<int:course_id>/', views.QuizByCourseView.as_view(), name='quiz-by-course'),
    path('quiz/category/all/', views.QuizAllStudentView.as_view(), name='quiz-all-student'),
    path('quiz/category/<int:category_id>/', views.QuizByCategoryView.as_view(), name='quiz-by-category'),
    path('quiz/<int:pk>/', views.QuizDetailView.as_view(), name='quiz-detail'),
    path('quiz/<int:pk>/submit/', views.QuizSubmitView.as_view(), name='quiz-submit'),

    # ── Courses ───────────────────────────────────────────────────────────────
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/featured/', views.CourseFeaturedView.as_view(), name='course-featured'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('courses/<int:pk>/enroll/', views.CourseEnrollView.as_view(), name='course-enroll'),
    path('courses/<int:pk>/enrolled/', views.CourseEnrollCheckView.as_view(), name='course-enrolled-check'),
    path('courses/<int:course_id>/doubts/', views.CourseDoubtListView.as_view(), name='course-doubts'),
    path('courses/<int:course_id>/sections/', views.SectionListView.as_view(), name='section-list'),
    path('courses/<int:course_id>/reviews/', views.ReviewListView.as_view(), name='review-list'),
    path('sections/<int:pk>/', views.SectionDetailView.as_view(), name='section-detail'),

        # ── Batches ───────────────────────────────────────────────────────────────────
    path('batches/', views.BatchListView.as_view(), name='batch-list'),
    path('batches/my/', views.MyBatchesView.as_view(), name='my-batches'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch-detail'),
    path('batches/<int:pk>/enroll/', views.BatchEnrollView.as_view(), name='batch-enroll'),
    path('batches/<int:batch_id>/sections/', views.BatchSectionListView.as_view(), name='batch-sections'),
    path('batches/<int:batch_id>/lectures/', views.LectureByBatchView.as_view(), name='batch-lectures'),
    path('batches/<int:pk>/students/', views.BatchStudentManageView.as_view(), name='batch-students'),



    # ── Lectures ──────────────────────────────────────────────────────────────
    path('lectures/course/<int:course_id>/', views.LectureByCourseView.as_view(), name='lectures-by-course'),
    path('lectures/<int:pk>/', views.LectureDetailView.as_view(), name='lecture-detail'),
    path('lectures/', views.LectureCreateView.as_view(), name='lecture-create'),
    # ── Notes ─────────────────────────────────────────────────────────────────
    path('notes/course/<int:course_id>/', views.NotesByCourseView.as_view(), name='notes-by-course'),
    path('notes/', views.NoteCreateView.as_view(), name='note-create'),

    # ── User ──────────────────────────────────────────────────────────────────
    path('user/profile/', views.UserProfileUpdateView.as_view(), name='user-profile'),
    path('user/all/', views.UserListView.as_view(), name='user-list'),
    path('user/<int:pk>/role/', views.UserRoleUpdateView.as_view(), name='user-role'),
    path('user/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user-delete'),
    path('progress/me/', views.MyCourseProgressView.as_view(), name='my-progress'),

    # ── Attendance ────────────────────────────────────────────────────────────
    path('attendance/', views.AttendanceCreateView.as_view(), name='attendance-create'),
    path('attendance/batch/<int:batch_id>/', views.AttendanceByBatchView.as_view(), name='attendance-by-batch'),
    path('attendance/me/', views.MyAttendanceView.as_view(), name='my-attendance'),

    # ── Assignments ───────────────────────────────────────────────────────────
    path('assignments/', views.AssignmentListView.as_view(), name='assignment-list'),
    path('assignments/<int:pk>/submit/', views.AssignmentSubmitView.as_view(), name='assignment-submit'),

    # ── Notifications ─────────────────────────────────────────────────────────
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/read-all/', views.NotificationReadAllView.as_view(), name='notification-read-all'),
    path('notifications/broadcast/', views.NotificationBroadcastView.as_view(), name='notification-broadcast'),

    # ── Doubts ────────────────────────────────────────────────────────────────
    path('doubts/', views.DoubtCreateView.as_view(), name='doubt-create'),
    path('doubts/all/', views.AllDoubtsAdminView.as_view(), name='all-doubts'),
    path('doubts/me/', views.MyDoubtsView.as_view(), name='my-doubts'),
    path('doubts/<int:pk>/reply/', views.DoubtReplyView.as_view(), name='doubt-reply'),

    # ── Payments ──────────────────────────────────────────────────────────────
    path('payments/all/', views.AllPaymentsAdminView.as_view(), name='all-payments'),
    path('payments/student/<int:student_id>/', views.StudentPaymentsAdminView.as_view(), name='student-payments'),
    path('payments/history/', views.PaymentHistoryView.as_view(), name='payment-history'),
    path('payments/create-order/', views.CreateOrderView.as_view(), name='payment-create-order'),
    path('payments/verify/', views.VerifyPaymentView.as_view(), name='payment-verify'),

    # ── Exam ──────────────────────────────────────────────────────────────────
    path('exam/my/', views.MyExamResultsView.as_view(), name='my-exams'),
    path('exam/', views.ExamResultCreateView.as_view(), name='exam-create'),

    # ── Schedule ──────────────────────────────────────────────────────────────
    path('schedule/my/', views.MyScheduleView.as_view(), name='my-schedule'),
    path('schedule/course/<int:course_id>/', views.ScheduleByCourseView.as_view(), name='schedule-by-course'),
    path('schedule/', views.ScheduleCreateView.as_view(), name='schedule-create'),
    path('schedule/<int:pk>/', views.ScheduleDetailView.as_view(), name='schedule-detail'),

    # ── Fee ───────────────────────────────────────────────────────────────────
    path('fee/my/', views.MyFeeReceiptsView.as_view(), name='my-fee'),
    path('fee/all/', views.AllFeeReceiptsView.as_view(), name='all-fee'),
    path('fee/', views.FeeReceiptCreateView.as_view(), name='fee-create'),

    # ── Chat ──────────────────────────────────────────────────────────────────
    path('chat/course/<int:course_id>/', views.ChatByCourseView.as_view(), name='chat-by-course'),
    path('chat/', views.ChatCreateView.as_view(), name='chat-create'),

    # ── Leaderboard ───────────────────────────────────────────────────────────
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),

    # ── Upload ────────────────────────────────────────────────────────────────
    path('upload/image/', views.UploadImageView.as_view(), name='upload-image'),
    path('upload/pdf/<int:course_id>/', views.UploadPDFView.as_view(), name='upload-pdf'),
    path('upload/video/<int:course_id>/', views.UploadVideoView.as_view(), name='upload-video'),

    # ── Coding ────────────────────────────────────────────────────────────────
    path('coding/', views.CodingQuestionListView.as_view(), name='coding-list'),
    path('coding/<int:pk>/', views.CodingQuestionDetailView.as_view(), name='coding-detail'),

    # ── Polls ─────────────────────────────────────────────────────────────────
    path('poll/', views.PollListView.as_view(), name='poll-list'),
    path('poll/<int:pk>/vote/', views.PollVoteView.as_view(), name='poll-vote'),

    # ── Banners ───────────────────────────────────────────────────────────────
    path('banners/', views.BannerListView.as_view(), name='banner-list'),
]

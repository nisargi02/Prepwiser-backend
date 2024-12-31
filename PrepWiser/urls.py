"""
URL configuration for PrepWiser project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    #path("", include("Prepwiser_app.urls"))
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("uploadPDF",views.FileUploadView.as_view()),
    path('upload/', views.DocumentUploadView.as_view(), name='upload'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('video_summarizer/', views.SummarizerView.as_view(), name='video_summarizer'),
    path('discussions/', views.PostList.as_view(), name='post-list'),
    path('discussions/<int:pk>/', views.PostDetail.as_view(), name='post-detail'),
    path('discussions/<int:post_pk>/comments/', views.CommentList.as_view(), name='comment-list'),
    path('discussions/<int:post_pk>/comments/<int:pk>/', views.CommentDetail.as_view(), name='comment-detail'),
    path('discussions/<int:pk>/vote/', views.PostVoteUpdate.as_view(), name='post-vote-update'),
    path('roadmap/', views.SkillRoadmapView.as_view()),
    path('roadmap/save/', views.SaveRoadmapProgressView.as_view()),
    path("signUp/",views.SignUpView.as_view()),
    path("login/",views.LoginView.as_view()),
    # path('questionBankGenerate2/',views.QuestionBankGenerate2.as_view()),
]

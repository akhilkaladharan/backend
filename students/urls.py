from django.urls import path

from . import views

urlpatterns = [
    # auth
    path("auth/register/", views.register),
    path("auth/login/", views.login_view),
    path("auth/me/", views.me),
    path("courses/", views.courses),
    # student
    path("applications/mine/", views.my_application),
    path("applications/<int:pk>/messages/", views.messages_view),
    # teacher
    path("teacher/applications/", views.teacher_list),
    path("teacher/applications/<int:pk>/", views.teacher_detail),
]

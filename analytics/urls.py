
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("upload/", views.upload_csv, name="upload"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("library/", views.library_view, name="library"),

    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]

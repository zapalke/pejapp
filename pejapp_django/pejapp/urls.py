from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='pejapp/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='pejapp/logout.html'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('post/new/', views.post_create, name='post-create'),
    path('post/<int:pk>/', views.post_detail, name='post-detail'),
    path('post/<int:pk>/update/', views.post_update, name='post-update'),
    path('post/<int:pk>/delete/', views.post_delete, name='post-delete'),
    path('user/<str:username>/', views.user_posts, name='user-posts'),
]
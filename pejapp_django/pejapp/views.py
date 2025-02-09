from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, PostForm
from django.contrib.auth.decorators import login_required
from .models import Post
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'pejapp/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'pejapp/profile.html', context)

def home(request):
    posts = Post.objects.all().order_by('-date_posted')
    return render(request, 'pejapp/home.html', {'posts': posts})

def search_users(request):
    query = request.GET.get('q', '')
    users = []
    if query:
        users = User.objects.filter(Q(username__icontains=query) | Q(email__icontains(query)))
    return render(request, 'pejapp/search_users.html', {'users': users, 'query': query})

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.display_name = request.user.profile.display_name
            post.save()
            return redirect('post-list')
    else:
        form = PostForm()
    return render(request, 'pejapp/create_post.html', {'form': form})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'pejapp/post_detail.html', {'post': post})

@login_required
def post_update(request, pk):
    post = Post.objects.get(pk=pk)
    prev_content = post.content
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post.modified_flag = True
            post.last_modified = timezone.now()
            post.original_content = prev_content
            post.display_name = request.user.profile.display_name
            form.save()
            return redirect('profile')
    else:
        form = PostForm(instance=post)
    return render(request, 'pejapp/create_post.html', {'form': form})

@login_required
def post_delete(request, pk):
    post = Post.objects.get(pk=pk)
    post.delete()
    return redirect('profile')

def user_posts(request, username):
    user = User.objects.get(username=username)
    posts = Post.objects.filter(author=user)
    return render(request, 'pejapp/user_posts.html', {'posts': posts, 'user': user})

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'You have been logged in successfully.')
                return redirect('post-list')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'pejapp/login.html', {'form': form})

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('post-list')


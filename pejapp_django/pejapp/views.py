from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, PostForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Post
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import datetime, timedelta
from django.http import JsonResponse

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

def user_profile(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user

    if request.user.is_authenticated and request.method == 'POST' and user == request.user:
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('user-profile', username=request.user.username)
    else:
        u_form = UserUpdateForm(instance=request.user) if request.user.is_authenticated else None
        p_form = ProfileUpdateForm(instance=request.user.profile) if request.user.is_authenticated else None

    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    sort_order = request.GET.get('sort', 'desc')

    posts = user.post_set.all()

    if search_query:
        posts = posts.filter(content__icontains=search_query)

    if start_date:
        posts = posts.filter(date_posted__gte=start_date)

    if end_date:
        posts = posts.filter(date_posted__lte=end_date)

    if sort_order == 'asc':
        posts = posts.order_by('date_posted')
    else:
        posts = posts.order_by('-date_posted')

    paginator = Paginator(posts, 5)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    context = {
        'profile_user': user,
        'u_form': u_form,
        'p_form': p_form,
        'posts': posts,
        'sort_order': sort_order,
    }

    return render(request, 'pejapp/user_profile.html', context)

def home(request):
    posts = Post.objects.all().order_by('-date_posted')
    paginator = Paginator(posts, 5)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'pejapp/post_list.html', {'posts': posts})
    return render(request, 'pejapp/home.html', {'posts': posts})

def search(request):
    query = request.GET.get('q', '')
    post_page = request.GET.get('post_page', 1)
    user_page = request.GET.get('user_page', 1)

    posts = Post.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)).order_by('-date_posted')
    users = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query))

    post_paginator = Paginator(posts, 5)
    user_paginator = Paginator(users, 5)

    try:
        posts = post_paginator.page(post_page)
    except PageNotAnInteger:
        posts = post_paginator.page(1)
    except EmptyPage:
        posts = post_paginator.page(post_paginator.num_pages)

    try:
        users = user_paginator.page(user_page)
    except PageNotAnInteger:
        users = user_paginator.page(1)
    except EmptyPage:
        users = user_paginator.page(user_paginator.num_pages)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if 'post_page' in request.GET:
            return render(request, 'pejapp/post_search_results.html', {'posts': posts, 'query': query})
        elif 'user_page' in request.GET:
            return render(request, 'pejapp/user_search_results.html', {'users': users, 'query': query})

    context = {
        'query': query,
        'posts': posts,
        'users': users,
    }

    return render(request, 'pejapp/search_results.html', context)

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
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
            form.save()
            return redirect('user-profile', username=request.user.username)
    else:
        form = PostForm(instance=post)
    return render(request, 'pejapp/create_post.html', {'form': form})

@login_required
def post_delete(request, pk):
    post = Post.objects.get(pk=pk)
    post.delete()
    return redirect('user-profile', username=request.user.username)

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

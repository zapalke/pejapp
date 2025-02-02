from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, PostForm
from django.contrib.auth.decorators import login_required
from .models import Post
from django.contrib.auth.models import User
from django.db.models import Q

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
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
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
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'pejapp/post_list.html', {'posts': posts})

def search_users(request):
    query = request.GET.get('q', '')
    users = []
    if query:
        users = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query))
    return render(request, 'pejapp/search_users.html', {'users': users, 'query': query})

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'pejapp/create_post.html', {'form': form})

def post_detail(request, pk):
    post = Post.objects.get(pk=pk)
    return render(request, 'pejapp/post_detail.html', {'post': post})

@login_required
def post_update(request, pk):
    post = Post.objects.get(pk=pk)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post-detail', pk=pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'pejapp/create_post.html', {'form': form})

@login_required
def post_delete(request, pk):
    post = Post.objects.get(pk=pk)
    post.delete()
    return redirect('home')

def user_posts(request, username):
    user = User.objects.get(username=username)
    posts = Post.objects.filter(author=user)
    return render(request, 'pejapp/user_posts.html', {'posts': posts, 'user': user})


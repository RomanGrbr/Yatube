from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


@require_http_methods(['GET'])
def index(request):
    posts = cache.get('index_page')
    if posts is None:
        posts = Post.objects.all()
        cache.set('index_page', posts, timeout=20)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page}
    return render(request, 'posts/index.html', context)


@require_http_methods(['GET'])
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'group': group, 'page': page}
    return render(request, 'posts/group.html', context)


@require_http_methods(['GET'])
def profile(request, username):
    user = get_object_or_404(User, username=username)
    following = user.following.all().exists()
    following_list = user.following.count()
    follower_list = user.follower.count()
    posts = user.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'user_name': user,
               'page': page,
               'following': following,
               'following_list': following_list,
               'follower_list': follower_list
               }
    return render(request, 'posts/profile.html', context)


@require_http_methods(['GET'])
def post_view(request, username, post_id):
    user = get_object_or_404(User, username=username)
    following_list = user.following.count()
    follower_list = user.follower.count()
    post = get_object_or_404(Post, id=post_id, author=user)
    form = CommentForm(request.POST or None)
    comment = Comment.objects.all().filter(post_id=post_id)
    context = {
        'user_name': user,
        'post': post,
        'form': form,
        'comment': comment,
        'following_list': following_list,
        'follower_list': follower_list
    }
    return render(request, 'posts/post.html', context)


@require_http_methods(['GET', 'POST'])
@csrf_exempt
@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    context = {'form': form}
    return render(request, 'posts/newpost.html', context)


@require_http_methods(['GET', 'POST'])
@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if post.author != request.user:
        return redirect('post', username, post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('post', username, post_id)
    context = {'post': post, 'form': form}
    return render(request, 'posts/newpost.html', context)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@require_http_methods(['GET', 'POST'])
@csrf_exempt
@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comments = form.save(commit=False)
        comments.post = post
        comments.author = request.user
        comments.save()
        return redirect("post", username, post_id)
    context = {"form": form}
    return render(request, "posts/comments.html", context)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if Follow.objects.filter(user=request.user).exists():
        context = {'page': page}
        return render(request, 'posts/follow.html', context)
    return render(request, 'posts/follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user)
    if user != author:
        if not Follow.objects.filter(author=author, user=user).exists():
            Follow.objects.create(author_id=author.id, user_id=request.user.id)
    return redirect("profile", username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('profile', username)

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

from .forms import PostForm, CommentForm, UserEditForm
from .models import Post, Category, Comment

User = get_user_model()


def get_published_posts(queryset=None, use_select_related=True, use_annotate=True):
    """Получить опубликованные посты с фильтрацией."""
    if queryset is None:
        queryset = Post.objects.all()
    
    if use_select_related:
        queryset = queryset.select_related('author', 'location', 'category')
    
    queryset = queryset.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )
    
    if use_annotate:
        queryset = queryset.annotate(comment_count=Count('comments'))
    
    return queryset.order_by('-pub_date')


class IndexListView(ListView):
    """Главная страница со списком публикаций."""

    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        return get_published_posts()


class PostDetailView(DetailView):
    """Страница отдельной публикации."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        
        # Если пост автора или это опубликованный пост
        if post.author == self.request.user:
            return post
        
        # Иначе проверяем публикацию
        return get_object_or_404(
            get_published_posts(use_select_related=False, use_annotate=False),
            pk=self.kwargs['post_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class CategoryPostsListView(ListView):
    """Страница категории с публикациями."""

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return get_published_posts(queryset=self.category.posts.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileListView(ListView):
    """Страница профиля пользователя."""

    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        self.profile_user = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        
        # Если это автор, показываем все его посты
        if self.profile_user == self.request.user:
            return self.profile_user.posts.select_related(
                'category', 'location'
            ).annotate(comment_count=Count('comments')).order_by('-pub_date')
        
        # Иначе только опубликованные
        return self.profile_user.posts.select_related(
            'category', 'location'
        ).filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile_user
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Страница редактирования профиля."""

    model = User
    form_class = UserEditForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class PostCreateView(LoginRequiredMixin, CreateView):
    """Страница создания публикации."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Страница редактирования публикации."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Страница удаления публикации."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментария."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование комментария."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление комментария."""

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


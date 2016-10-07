from django.shortcuts import render, get_object_or_404, render_to_response, Http404
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.views.generic import TemplateView
from django.views.generic import View, ListView, CreateView, DeleteView, DetailView
from django.views.generic.edit import ContextMixin
from django.views.generic.detail import SingleObjectMixin
from django.core.exceptions import PermissionDenied

from .models import Blog, Comment, User, Music
from .forms import CommentForm, BlogForm, ForwardForm, LoginForm, RegisterForm, ImageUploadForm, MusicUploadForm
from django.views.generic import ListView


# Create your views here.
def get_music_information(music):
    information = music.content_type.split('-')
    return information


class BaseMixin(ContextMixin):
    def get_context_data(self, *args, **kwargs):
        context = super(BaseMixin, self).get_context_data(**kwargs)
        if self.request.user.is_active:
            user = User.objects.get(pk=self.request.user.id)
            context['log_user'] = user
        else:
            context['log_user'] = None

        return context


class IndexView(BaseMixin, ListView):
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        blog = Blog.objects.none()

        if self.request.user.is_active:
            user = context['log_user']
            context['follow_list'] = user.follow.all()

            for user in user.follow.all():
                blog = blog | Blog.objects.filter(blog_author=user, blog_private=False)

        context['blog_list'] = blog
        return context

    def get_queryset(self):
        return User.objects.all()


class UserControl(View, BaseMixin):
    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        if slug == 'register':
            return render(self.request, 'blog/register.html')
        elif slug == 'manage':
            return render(self.request, 'blog/upload_profile.html')

        raise PermissionDenied

    def post(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'login':
            return self.login()
        elif slug == 'logout':
            return self.logout()
        elif slug == 'register':
            return self.register()
        elif slug == 'search':
            return self.search()
        elif slug == 'manage':
            return self.manage()

        raise PermissionDenied

    def login(self):
        form = LoginForm(self.request.POST)

        if form.is_valid():
            name = form.cleaned_data['username']
            pwd = form.cleaned_data['password']
            user = authenticate(username=name, password=pwd)

            if user is not None:
                self.request.session.set_expiry(0)
                login(self.request, user)

        return HttpResponseRedirect(reverse('blog:index'))

    def logout(self):
        logout(self.request)
        user_list = User.objects.order_by('date_joined')
        context = {
            'user_list': user_list,
        }

        return render(self.request, 'blog/index.html', context)

    def register(self):
        form = RegisterForm(self.request.POST)

        if form.is_valid():
            user_name = form.cleaned_data['username']
            firstname = form.cleaned_data['firstname']
            lastname = form.cleaned_data['lastname']
            pwd = form.cleaned_data['password']
            e_mail = form.cleaned_data['email']
            user = User.objects.create(username=user_name, first_name=firstname, last_name=lastname, email=e_mail)
            user.set_password(pwd)
        try:
            user.save()
            user = authenticate(username=user_name, password=pwd)
            login(self.request, user)
        except Exception:
            return render(self.request, 'blog/register.html')
        else:
            return HttpResponseRedirect(reverse('blog:index'))

    def manage(self):
        form = ImageUploadForm(self.request.POST, self.request.FILES)
        context = dict()

        if form.is_valid():
            if form.clean_file():
                log_user = User.objects.get(pk=self.request.user.id)
                log_user.profile_photo = form.cleaned_data['profile']
                log_user.save()
            else:
                context['error_message'] = 'Image too large'
                return render(self.request, 'blog/upload_profile.html', context)
        else:
            context['error_message'] = 'Submit file is nor an image.'
            return render(self.request, 'blog/upload_profile.html', context)

        return HttpResponseRedirect(reverse('blog:index'))

    def search(self):
        context = self.get_context_data()
        keyword = self.request.POST['keyword']
        blog = Blog.objects.filter(blog_title__contains=keyword, blog_private=False)
        user = User.objects.filter(username__contains=keyword)

        context['result_blog'] = blog
        context['result_user'] = user

        return render(self.request, 'blog/searchresult.html', context)


class UserView(BaseMixin, View):
    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'homepage':
            return self.homepage(request)

    def post(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'follow':
            return self.follow(request)

    def get_context_data(self, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        log_user = context['log_user']
        home_id = self.kwargs.get('u_id')
        user = get_object_or_404(User, pk=home_id)
        blog_list = Blog.objects.filter(blog_author=user)

        if type(log_user) is User:
            context['follow'] = user in log_user.follow.all()

            if home_id == str(log_user.id):
                is_self = True
            else:
                is_self = False
                blog_list = blog_list.filter(blog_private=False)

        else:
            is_self = False
            context['follow'] = False
            blog_list = blog_list.filter(blog_private=False)

        context['User'] = user
        context['Blog_list'] = blog_list
        context['self'] = is_self

        return context

    def homepage(self, request):
        context = self.get_context_data()

        return render(self.request, 'blog/personalhomepage.html', context)

    def follow(self, request):
        context = self.get_context_data()
        log_user = context['log_user']
        user = context['User']
        home_id = self.kwargs.get('u_id')

        if type(log_user) is User:
            follow = User.objects.get(pk=home_id)

            if log_user.follow.filter(pk=home_id).exists():
                log_user.follow.remove(follow)
            else:
                log_user.follow.add(follow)
            context['follow'] = user in log_user.follow.all()
        else:
            context['follow'] = False

        return render(self.request, 'blog/personalhomepage.html', context)


class WriteBlogView(BaseMixin, CreateView):
    model = Blog
    fields = [
        'title',
        'content',
        'private',
    ]

    def get(self, request, *args, **kwargs):
        form = BlogForm()
        return render(request, 'blog/blog_form.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = BlogForm(self.request.POST, self.request.FILES)
        context = dict()

        if form.is_valid():
            if form.clean_file():
                title = form.cleaned_data['title']
                content = form.cleaned_data['content']
                private = form.cleaned_data['private']
                music = form.cleaned_data['music']
                # info = get_music_information(music)[0]
                # singer = info[0].strip()
                # song = info[1].strip()
                m = Music.objects.create()
                m.music = music
                m.save()
                post_date = timezone.now()
                author = request.user.id
                blog = Blog.objects.create(blog_title=title, blog_content=content, blog_postdate=post_date,
                                           blog_author_id=author, blog_private=private)
                blog.relate_music = m
                try:
                    blog.save()
                except Exception:
                    return render(reverse('blog:writeblog'))
                else:
                    context = {
                        'blog': blog,
                    }
                    return render(request, 'blog/viewblog.html', context)
            else:
                context['error_message'] = 'Music file too large.'
                return render(reverse('blog:writeblog'), context)
        else:
            return render(reverse('blog:writeblog'))


class BlogView(BaseMixin, View):
    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        if slug == 'view':
            return self.view(request)

    def post(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'delete':
            return self.deleteblog(request)
        elif slug == 'like':
            return self.like(request)
        elif slug == 'forward':
            return self.forward(request)
        elif slug == 'comment':
            return self.comment(request)

    def get_context_data(self, *args, **kwargs):
        context = super(BlogView, self).get_context_data(**kwargs)
        log_user = context['log_user']
        b_id = self.kwargs.get('b_id')
        blog = Blog.objects.get(pk=b_id)
        home_id = blog.blog_author_id
        user = get_object_or_404(User, pk=home_id)

        if type(log_user) is User:

            if home_id == log_user.id:
                is_self = True
            else:
                is_self = False

            context['liked'] = blog.liked_user.filter(pk=log_user.id).exists()
        else:
            is_self = False
            context['liked'] = False

        context['blog'] = blog
        context['User'] = user
        context['self'] = is_self
        context['comment_list'] = blog.comment_set.all()
        context['music'] = blog.relate_music.music

        return context

    def view(self, request):
        context = self.get_context_data()

        return render(self.request, 'blog/viewblog.html', context)

    def forward(self, request):
        context = self.get_context_data()
        blog = context['blog']
        log_user = context['log_user']

        form = ForwardForm(self.request.POST)

        if form.is_valid():
            fwdcontent = form.cleaned_data['fwdcontent']
            fwdprivate = form.cleaned_data['fwdprivate']
            fwddate = timezone.now()
            fwdblog = Blog(
                blog_author=log_user,
                blog_title=fwdcontent,
                blog_postdate=fwddate,
                blog_private=fwdprivate,
                fwd_blog=blog,
                relate_music=blog.relate_music
            )
            fwdblog.save()

        return render(self.request, 'blog/viewblog.html', context)

    def like(self, request):
        context = self.get_context_data()
        blog = context['blog']
        log_user = context['log_user']
        id = log_user.id
        if id != blog.blog_author_id:
            if blog.liked_user.filter(pk=id).exists():
                blog.liked_user.remove(log_user)
                context['liked'] = False
            else:
                blog.liked_user.add(log_user)
                context['liked'] = True

        return render(self.request, 'blog/viewblog.html', context)

    def deleteblog(self, request):
        context = self.get_context_data()
        blog = context['blog']
        log_user = context['log_user']
        if blog.blog_author_id == log_user.id:
            Blog.objects.get(pk=blog.id).delete()
            context['blog'] = None
            context['follow'] = False
            context['Blog_list'] = Blog.objects.filter(blog_author=log_user)

        context['comment_list'] = None
        context['music'] = None

        return render(self.request, 'blog/personalhomepage.html', context)

    def comment(self, request):
        context = self.get_context_data()
        blog = context['blog']
        form = CommentForm(request.POST)

        if form.is_valid():
            author_id = form.cleaned_data['author_id']
            content = form.cleaned_data['content']
            date = timezone.now()
            comment = Comment(comment_author_id=author_id, comment_blog=blog, comment_content=content,
                              comment_date=date)
            try:
                comment.save()
            except Exception:
                raise Http404
            else:
                context['comment_list'] = blog.comment_set.all()

        return render(self.request, 'blog/viewblog.html', context)


class DeleteCommentView(BaseMixin, View):
    def get(self, request, *args):
        self.get_context_data()

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        c_id = self.kwargs.get('c_id')
        if context['self']:
            Comment.objects.get(pk=c_id).delete()
            blog = context['blog']
            context['comment_list'] = blog.comment_set.all()

        return render(self.request, 'blog/viewblog.html', context)

    def get_context_data(self, *args, **kwargs):
        context = super(DeleteCommentView, self).get_context_data(**kwargs)

        log_user = context['log_user']
        c_id = self.kwargs.get('c_id')
        comment = Comment.objects.get(pk=c_id)
        b_id = comment.comment_blog.id
        blog = Blog.objects.get(pk=b_id)
        home_id = blog.blog_author_id
        user = get_object_or_404(User, pk=home_id)

        if type(log_user) is User:

            if home_id == log_user.id:
                is_self = True
            else:
                is_self = False

            context['liked'] = blog.liked_user.filter(pk=log_user.id).exists()
        else:
            is_self = False
            context['liked'] = False

        context['blog'] = blog
        context['User'] = user
        context['self'] = is_self
        context['comment_list'] = blog.comment_set.all()

        return context

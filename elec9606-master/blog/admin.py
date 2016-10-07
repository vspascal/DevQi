from django.contrib import admin


from .models import User, Blog, Comment


# Register your models here.
class BlogAdmin(admin.ModelAdmin):
    fields = [
        'blog_title',
        'blog_postdate',
        'blog_content',
        'blog_author',
    ]

    list_display = ('blog_title', 'blog_author', 'blog_postdate')


class CommentAdmin(admin.ModelAdmin):
    fields = [
        'comment_content',
        'comment_date',
        'comment_author_id',
        'comment_blog_id',
    ]

    list_display = ('comment_blog', 'comment_author_id', 'comment_content', 'comment_date')


admin.site.register(User)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Comment, CommentAdmin)
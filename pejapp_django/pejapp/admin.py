from django.contrib import admin
from .models import Post, Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio')
    search_fields = ('user__username',)
    list_filter = ('user',)
    fieldsets = (
        (None, {
            'fields': ('user', 'bio')
        }),
    )

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'date_posted', 'last_modified', 'modified_flag')
    search_fields = ('title', 'author__username', 'content')
    list_filter = ('date_posted', 'last_modified', 'modified_flag')
    readonly_fields = ('date_posted', 'last_modified')
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'content', 'modified_flag', 'original_content')
        }),
    )
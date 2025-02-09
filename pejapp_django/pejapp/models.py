from django.db import models
from django.contrib.auth.models import User
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=False, null=False, default='Anonymous')
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.username}'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class Post(models.Model):
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=False, null=False, default='Anonymous')
    modified_flag = models.BooleanField(default=False)
    original_content = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.display_name} Post id {self.id}'

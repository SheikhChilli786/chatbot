from django.db import models
from django.conf import settings
class ChatHistory(models.Model):
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    user_chat = models.TextField(null=True,blank=True)
    response_chat = models.TextField(null=True,blank = True)
    created_at = models.DateTimeField(auto_now_add=True)
    
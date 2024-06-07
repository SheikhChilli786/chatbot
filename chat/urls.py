from django.urls import include,path
from . import views

urlpatterns = [
    path('chat-bot/',views.ChatBotView.as_view(),name='')
]
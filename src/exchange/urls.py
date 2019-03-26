from django.conf.urls import url, include
from .views import IndexView, TransactionView, ChatView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^transaction/$', TransactionView.as_view(),
        name='transaction'),
    url(r'chat/$', ChatView.as_view(),
        name='chat'),
]
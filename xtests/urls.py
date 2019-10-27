from django.urls import path
from . import views
from django.conf.urls import url
from .views import SignUpView


urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
]

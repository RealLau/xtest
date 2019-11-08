"""XTest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls import url
from xtests import views

urlpatterns = [
                  url(r'batch_create_case/', views.batch_create_case, name="batch_create_case"),
                  url(r'plan_associate/', views.plan_associate, name="plan_associate"),
                  path(r'search/', include('haystack.urls')),
                  url(r'sign_in/', views.sign_in, name="sign_in"),
                  url(r'home/$', views.index, name="home"),
                  url(r'task/', views.task, name="task"),
                  url(r'plan/', views.plan, name="plan"),
                  url(r'project$', views.project, name="project"),
                  url(r'execution/', views.execution, name="execution"),
                  url(r'list_case/', views.list_case, name="list_case"),
                  url(r'case_detail/', views.case_detail, name="case_detail"),
                  url(r'module/$', views.module, name="module"),
                  url(r'account/$', views.account, name="account"),
                  url(r'remove_case/$', views.remove_case, name="remove_case"),
                  url(r'save_case/$', views.save_case, name="save_case"),
                  path('xtest/', include('xtests.urls')),
                  path('users/', include('xtests.urls')),
                  path('users/', include('django.contrib.auth.urls')),
                  path('', include('social_django.urls', namespace='social')),
                  path('admin/', admin.site.urls),
                  path('xtest/', include('xtests.urls')),
                  url(r'get_jira_bugs/', views.get_jira_bugs, name='get_jira_bugs'),
                  url(r'execute_case', views.execute_case, name='execute_case'),
                  url(r'bugs_by_plan', views.bugs_by_plan, name='bugs_by_plan'),
                  url(r'bugs_by_level', views.bugs_by_level, name='bugs_by_level'),
                  url(r'bugs_by_module', views.bugs_by_module, name='bugs_by_module'),
                  url(r'plan_execute_info', views.plan_execute_info, name='plan_execute_info'),
                  url(r'users', views.users, name="users"),
                  url(r'remove_cases_from_plan', views.remove_cases_from_plan, name='remove_cases_from_plan'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

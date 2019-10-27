from __future__ import division
from django.db import models
from django.contrib.auth.models import AbstractUser
import json
from django.db.models import Q


class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to='static/images/avatar/', default="/static/images/avatar/user_man.png")

    def __str__(self):
        return self.username

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return "/" + self.avatar.url[self.avatar.url.find("static"):]
        else:
            return "/static/images/avatar/user_man.png"

    @property
    def avatar_url_for_tree(self):
        return self.avatar_url.split(".")[0]+"_for_tree"+"."+self.avatar_url.split(".")[1]

class Project(models.Model):
    name = models.CharField(max_length=100, null=False)
    desc = models.CharField(max_length=200, null=True)
    avatar = models.ImageField(upload_to='project', default="/project/default.png")
    created_time = models.DateTimeField(auto_now=True)


    @property
    def get_cases_count(self):
        modules = TestModule.objects.filter(project=self)
        return TestCase.objects.filter(module_id__in=modules).count()

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        else:
            return "/media/uploads/project/default.png"

    @property
    def avatar_url_for_tree(self):
        return self.avatar_url.split(".")[0]+"_for_tree"+"."+self.avatar_url.split(".")[1]


class Task(models.Model):
    executor = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    plan = models.ForeignKey('TestPlan', on_delete=models.CASCADE, null=False)

    @property
    def get_bugs(self):
        q = ~Q(associate_bug='') & Q(task=self)
        cases_records = CaseRecord.objects.values_list(flat=True).filter(q)
        return cases_records

    @property
    def get_bugs_count(self):
        return self.get_bugs.count()

    @property
    def get_cases(self):
        cases = CaseRecord.objects.filter(task=self)
        return cases

    def get_cases_by_user(self, u):
        cases = CaseRecord.objects.distinct().values_list('case_id', flat=True).filter(plan_id=self.plan.pk, user_id=u.pk)
        return cases

    @property
    def get_cases_count(self):
        return self.get_cases.count()

    def set_cases(self, x):
        self.cases = json.dumps(x)

    @property
    def get_progress(self):
        count_all_cases = self.get_cases_count
        q1 = Q(task=self)
        q2 = ~Q(result_status='Q')
        q3 = ~Q(result_status='B')
        count_executed = CaseRecord.objects.values_list(flat=True).filter(q1 & q2 & q3).count()
        if not count_all_cases:
            return "0%"
        else:
            return "{0:.1f}%".format(count_executed / count_all_cases * 100)


class TestPlan(models.Model):
    name = models.CharField(max_length=100, null=False)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=1,
                              choices=[('0', "creating"), ('1', "pending"), ('2', "in-progress"), ("4", "pause"),
                                       ("5", "stopped")], default='0')

    @property
    def get_executors(self):
        user_ids = Task.objects.values_list('executor_id', flat=True).filter(plan=self)
        users = CustomUser.objects.filter(pk__in=user_ids)
        return users

    @property
    def get_bugs(self):
        q1 = Q(plan=self)
        q2 = ~Q(associate_bug='')
        return CaseRecord.objects.values_list(flat=True).filter(q1 & q2)

    @property
    def get_bugs_count(self):
        return self.get_bugs.count()

    @property
    def get_tasks(self):
        return Task.objects.filter(plan=self)

    def get_tasks_by_user(self, u):
        return Task.objects.filter(plan=self, executor=u)

    @property
    def get_cases_count(self):
        c = 0
        for t in self.get_tasks:
            c += t.get_cases_count
        return c

    @property
    def get_progress(self):
        q1 = Q(plan=self)
        all_cases = CaseRecord.objects.values_list(flat=True).filter(q1).count()
        q2 = ~Q(result_status='B')
        q3 = ~Q(result_status='Q')
        executed = CaseRecord.objects.values_list(flat=True).filter(q1 & q2 & q3).count()
        if not executed:
            return "0%"
        else:
            return "{:.1%}".format(executed / all_cases)


class TestModule(models.Model):
    name = models.CharField(max_length=100, null=False)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True)
    created_time = models.DateTimeField(auto_now=True)

    @property
    def get_cases_count(self):
        cases_count = TestCase.objects.filter(module=self).count()
        return cases_count


class TestCase(models.Model):
    module = models.ForeignKey('TestModule', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=False)
    desc = models.CharField(max_length=200, null=True)
    preconditions = models.TextField(null=True)
    steps = models.TextField(null=False)
    expectation = models.TextField(null=False)
    priority = models.CharField(max_length=1, choices=[('H', 'High'), ('M', 'Medium'), ('L', 'Low')], default='M')
    path = models.CharField(max_length=100, blank=True)
    created_time = models.DateTimeField(auto_now=True)
    last_update_time = models.DateTimeField(auto_now=True)


class CaseRecord(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, null=False)
    plan = models.ForeignKey('TestPlan', on_delete=models.CASCADE, null=False)
    task = models.ForeignKey('Task', on_delete=models.CASCADE, null=False)
    case = models.ForeignKey('TestCase', on_delete=models.CASCADE, null=False)
    execute_status = models.CharField(max_length=1, choices=[('P', 'Pending'), ('B', 'Block'), ('C', 'Complete')], default='P')
    result_status = models.CharField(max_length=1, choices=[('P', 'Pass'), ('F', 'Fail'), ('B', 'Block'), ('Q', 'Pending')], default='Q')
    attach = models.FileField(upload_to='static/case_execution_attach/', blank=True)
    associate_bug = models.CharField(max_length=200, blank=True)
    bug_link = models.CharField(max_length=200, default="")
    @property
    def attach_url(self):
        if self.attach and hasattr(self.attach, 'url'):
            return "/" + self.attach.url[self.attach.url.find("static"):]
        else:
            return "/static/case_execution_attach/default_image_missing.png"

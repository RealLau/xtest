from django.db import connection
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
from django.http import QueryDict
from .models import *
from django.http import JsonResponse, HttpResponseRedirect
from .PUBLIC_MESSAGE import *
from .common import *
import datetime
from django.utils import timezone
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.utils.dateparse import parse_datetime
import pytz
from django.conf import settings
import os
from django.db.models import Q, Count
from collections import Counter


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'


def users(request):
    if request.method == "GET":
        not_has_task = request.GET.get("not_has_task")
        data = []
        if not not_has_task:
            us = CustomUser.objects.all()
            for u in us:
                data.append({"name": u.username, "id": u.pk})
        else:
            with connection.cursor() as cursor:
                cursor.execute("select distinct id from xtest.xtests_customuser where id not in (select distinct user_id from xtest.xtests_caserecord)")
                for i in cursor.fetchall():
                    u_id = i[0]
                    user = CustomUser.objects.get(pk=u_id)
                    data.append({"name": user.username, "id": u_id})
        return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_QUERY_SUCCESS, "data": data})
    else:
        return JsonResponse({"status": STATUS_FAILED, "msg": MSG_METHOD_NOT_ALLOWED})


def sign_in(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect("/home/")
    else:
        return render(request, "registration/login.html", {"status": 0, "msg": MSG_USERNAME_OR_PASSWORD_WRONG})


def index(request):
    if request.user.is_anonymous:
        return render(request, "registration/login.html")
    else:
        u = request.user
        plans = TestPlan.objects.all()
        return render(request, "index.html", {"plans": plans, "user": u})


def list_case(request):
    tree_root_id = "Root"
    all_data = [
        {"id": tree_root_id, "parent": "#", "text": "All",
         "icon": "/static/images/img/tree-project.png"}]
    projects = Project.objects.all()
    for project in projects:
        project_id = "project" + str(project.pk)
        p_data = {"id": project_id, "parent": tree_root_id, "text": project.name,
                  "icon": project.avatar_url_for_tree}
        all_data.append(p_data)
        modules = TestModule.objects.filter(project=project)
        for m in modules:
            module_id = "module" + str(m.pk)
            m_data = {"id": module_id, "parent": project_id, "text": m.name,
                      "icon": "/static/images/img/tree-module.png"}
            all_data.append(m_data)
            cases = TestCase.objects.filter(module=m)
            for c in cases:
                c_data = {"id": "case" + str(c.pk), "parent": module_id, "text": c.title,
                          "icon": "/static/images/img/tree-leaf.png"}
                all_data.append(c_data)
    return render(request, "all_cases.html", {"all_data": json.dumps(all_data, cls=DjangoJSONEncoder)})


def case_detail(request):
    ca_pk = request.GET.get("pk")
    ca = TestCase.objects.get(pk=ca_pk)
    return JsonResponse(
            {"status": STATUS_SUCCESS, "msg": {"module": ca.module.name, "title": ca.title, "desc": ca.desc,
                                               "preconditions": ca.preconditions, "steps": ca.steps,
                                               "expectation": ca.expectation, "priority": ca.priority,
                                               "case_id": ca.pk}})


def batch_create_case(request):
    if request.method == "GET":
        example = request.GET.get("example")
        if example:
            return render(request, "batch_create_case_format.html")
        else:
            return render(request, "batch_create_cases_form.html")
    else:
        org_f = request.FILES["file"]
        str_time_now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        str_user = request.user.username.replace(" ", "")
        file_path_dir = os.path.join(settings.BATCH_CREATE_CASE_ORIGIN_FILE_DIR, str_user)
        if not os.path.exists(file_path_dir):
            os.makedirs(file_path_dir)
        file_path = os.path.join(file_path_dir, str_time_now + ".xls")
        with open(file_path, "wb+") as f:
            for chunk in org_f.chunks():
                f.write(chunk)
        data = data_check(file_path)
        if not isinstance(data, dict):
            return JsonResponse(
                {"status": STATUS_FAILED, "msg": "{msg}: {data}".format(msg=MSG_BATCH_CREATE_FAILED, data=data)})
        for p_name in data.keys():
            query_project_results = Project.objects.filter(name=p_name)
            # 如果项目不存在，则需要先创建项目
            if not query_project_results.exists():
                project = Project.objects.create(name=p_name)
                project.save()
            else:
                project = query_project_results[0]
            # 如果该项目下没有该模块，则需要先创建该模块
            for module_name in data[p_name].keys():
                query_module_results = TestModule.objects.filter(name=module_name, project=project)
                if not query_module_results.exists():
                    module = TestModule.objects.create(name=module_name, project=project)
                    module.save()
                else:
                    module = query_module_results[0]
                    for case_info in data[p_name][module_name]:
                        title = case_info["title"]
                        desc = case_info["desc"]
                        preconditions = case_info["preconditions"]
                        steps = case_info["steps"]
                        expectation = case_info["expectation"]
                        priority = case_info["priority"]
                        case = TestCase.objects.create(module=module, title=title, desc=desc,
                                                       preconditions=preconditions, steps=steps,
                                                       expectation=expectation, priority=priority)
                        case.save()
        return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_BATCH_CREATE_SUCCESS})


def module(request):
    if request.method == "GET":
        module_pk = request.GET["pk"]
        module = TestModule.objects.get(pk=module_pk)
        return JsonResponse({"status": STATUS_SUCCESS, "msg":MSG_QUERY_SUCCESS, "data": {"module_name": module.name, "case_count": module.get_cases_count}})

    elif request.method == "POST":
        pk = request.POST.get("module_pk")
        module_name = request.POST["module_name"]
        if pk:
            m = TestModule.objects.get(pk=pk)
            m.name = module_name
            m.save()
            data = {"module_name": module_name, "case_count": m.get_cases_count}
            return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_MODIFY_SUCCESS, "data": data})
        else:
            pro_pk = request.POST.get("project_pk")
            exist_pro = Project.objects.get(pk=pro_pk)
            m = TestModule.objects.create(name=module_name, project=exist_pro)
            m.save()
            data = {"module_name": module_name, "module_id": m.pk, "case_count": m.get_cases_count}
            return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_CREATE_SUCCESS, "data": data})
    else:
        pk = QueryDict(request.body).get("pk")
        m = TestModule.objects.get(pk=pk)
        m.delete()
        return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_DELETE_SUCCESS})


def account(request):
    return render(request, "accounts.html")


def remove_case(request):
    if request.method == "DELETE":
        pk = QueryDict(request.body).get("pk")
        cases = TestCase.objects.filter(pk=pk)
        if cases:
            for case in cases:
                case.delete()
            return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_DELETE_SUCCESS})
        else:
            return JsonResponse({"status": STATUS_FAILED, "msg": "找不到此用例，可能已被删除"})
    else:
        return JsonResponse({"status": STATUS_FAILED, "msg": MSG_METHOD_NOT_ALLOWED})


def save_case(request):
    if request.method != "POST":
        return JsonResponse({"status": STATUS_FAILED, "msg": MSG_METHOD_NOT_ALLOWED})
    else:
        # 解析参数module_pk, 如果不为None，则解析为修改用例，否则是新建，新建则要求提供module_pk参数
        case_pk = request.POST.get("case_pk")
        if case_pk:
            case_title = request.POST.get("case_title")
            case_desc = request.POST.get("case_desc")
            case_preconditions = request.POST.get("case_preconditions")
            case_steps = request.POST.get("case_steps")
            case_expectation = request.POST.get("case_expectation")
            case_priority = request.POST.get("case_priority")
            if case_title and case_steps and case_expectation and case_priority:
                case = TestCase.objects.get(pk=case_pk)
                case.title = case_title
                case.desc = case_desc
                case.preconditions = case_preconditions
                case.steps = case_steps
                case.expectation = case_expectation
                case.priority = case_priority
                case.save()
                data = {"case_title": case_title, "case_desc":case_desc, "case_preconditions": case_preconditions, "case_steps": case_steps, "case_expectation": case_expectation, "case_priority": case_priority}
                return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_MODIFY_SUCCESS, "data": data})
            else:
                return JsonResponse({"status": STATUS_FAILED, "msg": MSG_MISSING_REQUIRED_FIELDS.format(field="标题、步骤、期望结果、优先级")})
        else:
            module_pk = request.POST.get("module_pk")
            case_title = request.POST.get("case_title")
            case_desc = request.POST.get("case_desc")
            case_preconditions = request.POST.get("case_preconditions")
            case_steps = request.POST.get("case_steps")
            case_expectation = request.POST.get("case_expectation")
            case_priority = request.POST.get("case_priority")
            if module_pk and case_title and case_steps and case_expectation and case_priority:
                case = TestCase.objects.create(module=TestModule.objects.get(pk=module_pk), title=case_title, desc=case_desc, preconditions=case_preconditions, steps=case_steps, expectation=case_expectation,priority=case_priority)
                case.save()
                data = {"case_id":case.pk,"case_title": case_title, "case_desc": case_desc, "case_preconditions": case_preconditions, "case_steps": case_steps, "case_expectation": case_expectation, "case_priority": case_priority}
                return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_CREATE_SUCCESS, "data": data})
            else:
                return JsonResponse({"status": STATUS_FAILED, "msg": MSG_MISSING_REQUIRED_FIELDS.format(field="标题、步骤、期望结果、优先级")})


def project(request):
    if request.method == "GET":
        pk = request.GET.get("pk")
        if pk:
            p = Project.objects.get(pk=pk)
            return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_QUERY_SUCCESS, "data": {"name": p.name, "case_count": p.get_cases_count, "avatar": p.avatar_url, "desc": p.desc, "avatar_tree": p.avatar_url_for_tree}})
        else:
            projects = Project.objects.all()
            return render(request, "projects.html", {"projects": projects})
    elif request.method == "POST":
        # 如果存在pk，则判断为修改
        pk = request.POST.get("pk")
        if pk:
            name = request.POST["project_name"]
            desc = request.POST["project_desc"]
            try:
                avatar = request.FILES["avatar"]
            except MultiValueDictKeyError:
                avatar = "project/default.png"
            p = Project.objects.get(pk=pk)
            p.name = name
            p.desc = desc
            p.avatar = avatar
            p.save()
            avatar_path = settings.BASE_DIR + p.avatar_url
            resize_upload_file(file_path=avatar_path)
            resize_upload_file_for_tree(org_file_path=avatar_path, des_file_path=settings.BASE_DIR+p.avatar_url.split(".")[0]+"_for_tree"+"."+p.avatar_url.split(".")[1])
            return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_MODIFY_SUCCESS, "data": {"name": p.name, "case_count": p.get_cases_count, "avatar": p.avatar_url, "desc": p.desc}})
        # 否则为新建
        else:
            name = request.POST["project_name"]
            if name:
                already_exist_same_name_project = Project.objects.filter(name=name)
                if already_exist_same_name_project:
                    return JsonResponse({"status": STATUS_FAILED, "msg": "已经存在同名的项目"})
                else:
                    desc = request.POST["project_desc"]
                    try:
                        avatar = request.FILES["avatar"]
                    except MultiValueDictKeyError:
                        avatar = "project/default.png"
                    p = Project.objects.create(name=name, desc=desc, avatar=avatar)
                    p.save()
                    avatar_path = settings.BASE_DIR + p.avatar_url
                    resize_upload_file(file_path=avatar_path)
                    resize_upload_file_for_tree(org_file_path=avatar_path, des_file_path=settings.BASE_DIR + p.avatar_url.split(".")[0] + "_for_tree"+ "."  + p.avatar_url.split(".")[1])
                    return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_CREATE_SUCCESS})
            else:
                return JsonResponse({"status": STATUS_FAILED, "msg": "项目名称不能为空"})
    elif request.method == "DELETE":
        pk = QueryDict(request.body).get("pk")
        projects = Project.objects.filter(pk=pk)
        if projects:
            for p in projects:
                p.delete()
            return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_DELETE_SUCCESS})
        else:
            return JsonResponse({"status": STATUS_FAILED, "msg": "找不到此项目，可能已被删除"})
    else:
        return JsonResponse({"status": STATUS_FAILED, "msg": MSG_METHOD_NOT_ALLOWED})


def plan_associate(request):
    plan_pk = request.POST.get("plan")
    task_pk = request.POST.get("task")
    u_pk = request.POST.get("user")
    org_cases = request.POST.get("cases")
    if plan_pk and task_pk and u_pk and org_cases:
        cases = [int(i) for i in json.loads(org_cases)]
        # 先检查一遍，如果存在用例关联过传进来的任务，则返回失败，否则才进行关联
        for case_pk in cases:
            already_have_same_record = CaseRecord.objects.filter(plan_id=plan_pk, case_id=case_pk)
            if already_have_same_record:
                case_name = TestCase.objects.get(pk=case_pk).title
                return JsonResponse(
                    {"status": STATUS_FAILED, "msg": MSG_ALREADY_HAVE_SAME_RECORD.format(case=case_name, plan=plan_pk)})
        for case_pk in cases:
            r = CaseRecord.objects.create(case_id=case_pk, plan_id=plan_pk, task_id=task_pk, user_id=u_pk)
            r.save()
            # 用例和测试任务关联成功后，关联的计划的状态需要修改为pending("1")
            p = TestPlan.objects.get(pk=plan_pk)
            p.status = "1"
            p.save()
        return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_ASSOCIATE_SUCCESS})
    else:
        return JsonResponse({"status": STATUS_FAILED, "msg": MSG_MISSING_REQUIRED_FIELDS.format(field="任务、计划、执行者、所选用例均")})


def plan(request):
    if request.method == "POST":
        # 修改测试计划
        pk = request.POST.get("pk")
        if pk:
            p = TestPlan.objects.get(pk=pk)
            new_name = request.POST["plan_code_name"]
            start_time = pytz.timezone(settings.TIME_ZONE).localize(parse_datetime(request.POST["start_time"]), is_dst=None)
            end_time = pytz.timezone(settings.TIME_ZONE).localize(parse_datetime(request.POST["end_time"]), is_dst=None)
            if new_name and start_time and end_time:
                p.name = new_name
                p.start_time = start_time
                p.end_time = end_time
                p.save()
                executors = [e.username for e in p.get_executors]
                return JsonResponse({"status":STATUS_SUCCESS, "msg": MSG_MODIFY_SUCCESS, "data":{"name": p.name, "start_time":p.start_time, "end_time":p.end_time, "process": p.get_progress, "executors": executors, "bugs": p.get_bugs_count, "cases": p.get_cases_count}})
            else:
                return JsonResponse({"status": STATUS_FAILED, "msg": MSG_MODIFY_FAIL, "reason": "代号、开始时间、结束时间均不能为空"})
        # 创建新测试计划
        else:
            name = request.POST["plan_code_name"]
            already_exist_same_name_plan = TestPlan.objects.filter(name=name)
            if already_exist_same_name_plan:
                return JsonResponse({"status": STATUS_FAILED, "msg": "已经存在同名的测试计划"})
            else:
                start_time = pytz.timezone(settings.TIME_ZONE).localize(parse_datetime(request.POST["start_time"]),
                                                                        is_dst=None)
                end_time = pytz.timezone(settings.TIME_ZONE).localize(parse_datetime(request.POST["end_time"]),
                                                                      is_dst=None)
                p = TestPlan.objects.create(name=name, start_time=start_time, end_time=end_time)
                p.save()
                executors = [e.username for e in p.get_executors]
                return JsonResponse({"status": STATUS_SUCCESS, "msg": "创建测试计划成功", "data":{"plan": p.pk,"name": p.name, "start_time":p.start_time, "end_time":p.end_time, "process": p.get_progress, "executors": executors, "bugs": p.get_bugs_count, "cases": p.get_cases_count}})
    elif request.method == "DELETE":
        pk = QueryDict(request.body).get("pk")
        plans = TestPlan.objects.filter(pk=pk)
        if plans:
            for p in plans:
                p.delete()
                # 除了删除测试计划外，还要删除测试计划和任务(执行者、用例)的关联关系
                CaseRecord.objects.filter(plan_id=p.pk).delete()
            return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_DELETE_SUCCESS})
        else:
            return JsonResponse({"status": STATUS_FAILED, "msg": "找不到此测试计划，可能已被删除"})
    elif request.method == "GET":
        plan_id = request.GET.get("pk")
        if not plan_id:
            tree_root_id = "Root"
            all_data = [
                {"id": tree_root_id, "parent": "#", "text": "All",
                 "icon": "/static/images/img/tree-project.png"}]
            plans = TestPlan.objects.all()
            for plan in plans:
                plan_id = "plan" + str(plan.pk)
                p_data = {"id": plan_id, "parent": tree_root_id, "text": plan.name,
                          "icon": "/static/images/img/tree-plan.png"}
                all_data.append(p_data)
                tasks = Task.objects.filter(plan=plan)
                for t in tasks:
                    task_id = "task" + str(t.pk)
                    t_data = {"id": task_id, "parent": plan_id, "text": t.executor.username, "icon": t.executor.avatar_url}
                    all_data.append(t_data)
                    with connection.cursor() as cursor:
                        cursor.execute("select case_id from xtest.xtests_caserecord where task_id=%d and plan_id=%d" % (t.pk, plan.pk))
                        cases_ids = [i[0] for i in cursor.fetchall()]
                        if cases_ids:
                            cursor.execute("select distinct module_id from xtest.xtests_testcase where id in {cases_ids}".format(cases_ids=tuple(cases_ids)))
                            modules_ids = [i[0] for i in cursor.fetchall()]
                            if len(modules_ids)>1:
                                cursor.execute("select distinct project_id from xtest.xtests_testmodule where id in {modules_ids}".format(modules_ids=tuple(modules_ids)))
                            else:
                                cursor.execute(
                                    "select distinct project_id from xtest.xtests_testmodule where id ={modules_ids}".format(
                                        modules_ids=modules_ids[0]))
                            projects_ids = [i[0] for i in cursor.fetchall()]
                            for p_id in projects_ids:
                                project = Project.objects.get(pk=p_id)
                                project_id = "project"+str(p_id)+"user"+str(t.executor.pk)
                                pro_data = {"id": project_id, "parent": task_id, "text": project.name, "icon": project.avatar_url_for_tree}
                                all_data.append(pro_data)
                            for m_id in modules_ids:
                                module = TestModule.objects.get(pk=m_id)
                                parent_id = "project"+str(module.project.pk)+"user"+str(t.executor.pk)
                                module_id = "module"+str(m_id)+"user"+str(t.executor.pk)
                                module_data = {"id": module_id, "parent": parent_id, "text": module.name, "icon": "/static/images/img/tree-module.png"}
                                all_data.append(module_data)
                            for c_id in cases_ids:
                                case = TestCase.objects.get(pk=c_id)
                                case_record = CaseRecord.objects.get(task_id=t.pk, plan_id=plan.pk, case_id=c_id)
                                parent_id = "module" + str(case.module.pk)+"user"+str(t.executor.pk)
                                case_id = "case" + str(c_id)
                                case_data = {"id": case_id, "parent": parent_id, "text": case.title,
                                               "icon": "/static/images/img/case_execute_status/case_%s.png" % case_record.get_result_status_display()}
                                all_data.append(case_data)
            return render(request, "plans.html", {"all_data": json.dumps(all_data, cls=DjangoJSONEncoder)})
        else:
            p = TestPlan.objects.get(pk=plan_id)
            executors = [e.username for e in p.get_executors]
            start_time = p.start_time
            end_time = p.end_time
            return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_QUERY_SUCCESS, "data":{"name": p.name, "start_time":start_time, "end_time":end_time, "process": p.get_progress, "executors": executors, "bugs": p.get_bugs_count, "cases": p.get_cases_count}})


def task(request):
    if request.method == "GET":
        pk = request.GET.get("pk")
        if not pk:
            tasks = Task.objects.all()
            return render(request, "task_pop.html", {"tasks": tasks})
        else:
            task = Task.objects.get(pk=pk)
            return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_QUERY_SUCCESS, "data": {"executor": task.executor.username, "process": task.get_progress, "bugs": task.get_bugs_count, "cases": task.get_cases_count}})
    elif request.method == "POST":
        pk = request.POST.get("pk")
        user_pk = request.POST["user"]
        if not pk:
            plan_pk = request.POST["plan"]
            user = CustomUser.objects.get(pk=user_pk)
            plan = TestPlan.objects.get(pk=plan_pk)
            # 若该用户在该计划下已有任务，则不允许创建
            new_user_already_has_task = Task.objects.filter(executor=user, plan=plan)
            if new_user_already_has_task:
                return JsonResponse({"status": STATUS_FAILED, "msg": MSG_USER_ALREADY_HAVE_INCOMPLETE_TASK})
            else:
                t = Task.objects.create(executor=user, plan=plan)
                t.save()
                return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_CREATE_SUCCESS, "data": {"task": t.pk, "user": t.executor.username, "avatar": t.executor.avatar_url_for_tree}})
        else:
            task = Task.objects.get(pk=pk)
            case_records = CaseRecord.objects.filter(task_id=task.pk)
            if not case_records:
                return JsonResponse({"status": STATUS_FAILED, "msg": MSG_MODIFY_FAIL, "reason": "空任务不允许变更，如不再需要，请直接删除."})
            else:
                new_user = CustomUser.objects.get(pk=user_pk)
                org_executor = task.executor
                if new_user == org_executor:
                    return JsonResponse(
                        {"status": STATUS_FAILED, "msg": MSG_MODIFY_FAIL, "reason": "不允许：任务变更前后执行者一样"})
                else:
                    plan = task.plan
                    new_user_already_has_task = Task.objects.get(executor=new_user, plan=plan)
                    if new_user_already_has_task:
                        # new_task_id = list(CaseRecord.objects.distinct().values_list('task_id', flat=True).filter(plan_id=plan.pk, user_id=user_pk))[0]
                        new_task_id = new_user_already_has_task.pk
                        case_records.update(task_id=new_task_id, user_id=user_pk)
                    else:
                        new_task = Task.objects.create(executor=new_user, plan=task.plan)
                        case_records.update(task_id=new_task.pk, user_id=user_pk)
                    return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_MODIFY_SUCCESS})
    elif request.method == "DELETE":
        task_pk = QueryDict(request.body).get("pk")
        tasks = Task.objects.filter(pk=task_pk)
        if tasks:
            for t in tasks:
                t.delete()
            return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_DELETE_SUCCESS})
        else:
            return JsonResponse({"status": STATUS_FAILED, "msg": "找不到此任务，可能已被删除"})


def execution(request):
    plan_ids = list(CaseRecord.objects.distinct().values_list('plan_id', flat=True).filter(user_id=request.user.pk,
                                                                                           execute_status='P'))
    if len(plan_ids) > 1:
        print("超过一个测试计划")

    elif len(plan_ids) == 0:
        all_data = []
        return render(request, "execution.html",
                      {"all_data": json.dumps(all_data, cls=DjangoJSONEncoder)})
    else:
        plan = TestPlan.objects.get(pk=plan_ids[0])
        tree_root_id = "plan" + str(plan.pk)
        all_data = [
            {"id": tree_root_id, "parent": "#", "text": plan.name, "icon": "/static/images/img/tree-plan.png"}]
        task_ids = plan.get_tasks_by_user(u=request.user)
        for t in task_ids:
            t_id = "task" + str(t.pk)
            t_data = {"id": t_id, "parent": tree_root_id, "text": "任务" + str(t.pk),
                      "icon": "/static/images/img/tree-task.png"}
            all_data.append(t_data)
            cases = t.get_cases_by_user(request.user)
            for c_pk in list(cases):
                c = TestCase.objects.get(pk=c_pk)
                module = c.module
                module_id = "module" + str(module.pk)
                project = module.project
                project_id = "project" + str(project.pk)
                project_data = {"id": project_id, "parent": t_id, "text": project.name,
                                "icon": project.avatar_url_for_tree}
                if project_data not in all_data:
                    all_data.append(project_data)
                module_data = {"id": module_id, "parent": project_id, "text": module.name,
                               "icon": "/static/images/img/tree-module.png"}
                if module_data not in all_data:
                    all_data.append(module_data)
                c_record = CaseRecord.objects.get(task_id=t.pk, case_id=c.pk).get_result_status_display()
                c_data = {"id": "case" + str(c.pk), "parent": module_id, "text": c.title,
                          "icon": "/static/images/img/case_execute_status/case_%s.png" % c_record,
                          "a_attr": {"style": 'color: %s' % CASE_COLOR_DIC[c_record]}}
                all_data.append(c_data)
        return render(request, "execution.html",
                      {"all_data": json.dumps(all_data, cls=DjangoJSONEncoder)})


def get_jira_bugs(request):
    search_condition = settings.JIRA_CONFIG["search_condition"]
    jira_client = get_jira_client()
    issues = jira_client.search_issues(search_condition, maxResults=False)
    issue_dict = dict(zip([issue.key for issue in issues], [issue.permalink() for issue in issues]))
    return JsonResponse({"status": STATUS_SUCCESS, "issues": json.dumps(issue_dict)})


def execute_case(request):
    if request.method == "POST":
        task_id = request.POST["task_id"]
        case_id = request.POST["case_id"]
        result_status = request.POST["result_status"]
        associate_bug = request.POST["associate_bug"]
        bug_link = request.POST["bug-link"]
        c = CaseRecord.objects.get(task_id=task_id, case_id=case_id)
        c.result_status = result_status
        c.associate_bug = associate_bug
        c.bug_link = bug_link
        c.save()
        return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_CASE_EXECUTE_SUCCESS})


def bugs_by_plan(request):
    if request.method == "POST":
        plans = json.loads(request.POST.get("plans"))
        res = {}
        jira_client = get_jira_client()
        highest_list = []
        high_list = []
        medium_list = []
        low_list = []
        lowest_list = []
        projects = []
        for p_id in plans:
            p = TestPlan.objects.get(pk=p_id)
            p_name = p.name
            q = ~Q(associate_bug='') & Q(plan=p)
            bugs = CaseRecord.objects.values_list('associate_bug', flat=True).filter(q)
            highest = 0
            high = 0
            medium = 0
            low = 0
            lowest = 0
            for b_id in list(bugs):
                issue = jira_client.issue(b_id)
                issue_priority = issue.fields.priority.name
                if issue_priority == "Highest":
                    highest += 1
                elif issue_priority == "High":
                    high += 1
                elif issue_priority == "Medium":
                    medium += 1
                elif issue_priority == "Low":
                    low += 1
                elif issue_priority == "Lowest":
                    lowest += 1
            projects.append(p_name)
            high_list.append(high)
            highest_list.append(highest)
            medium_list.append(medium)
            low_list.append(low)
            lowest_list.append(lowest)
        res["projects"] = projects
        res["highest"] = highest_list
        res["high"] = high_list
        res["medium"] = medium_list
        res["low"] = low_list
        res["lowest"] = lowest_list
        return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_QUERY_SUCCESS, "data": res})
    else:
        return JsonResponse({"status": STATUS_FAILED, "msg": MSG_METHOD_NOT_ALLOWED})


def bugs_by_level(request):
    if request.method == "POST":
        plan = request.POST.get("plan")
        p = TestPlan.objects.get(pk=plan)
        q = ~Q(associate_bug='') & Q(plan=p)
        bugs = CaseRecord.objects.values_list('associate_bug', flat=True).filter(q)
        jira_client = get_jira_client()
        res = []
        highest = 0
        high = 0
        medium = 0
        low = 0
        lowest = 0
        for b_id in list(bugs):
            issue = jira_client.issue(b_id)
            issue_priority = issue.fields.priority.name
            if issue_priority == "Highest":
                highest += 1
            elif issue_priority == "Medium":
                medium += 1
            elif issue_priority == "High":
                high += 1
            elif issue_priority == "Low":
                low += 1
            elif issue_priority == "Lowest":
                lowest += 1
        res.append(highest)
        res.append(high)
        res.append(medium)
        res.append(low)
        res.append(lowest)
        return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_QUERY_SUCCESS, "data": res})
    else:
        return JsonResponse({"status": STATUS_FAILED, "msg": MSG_METHOD_NOT_ALLOWED})


def bugs_by_module(request):
    if request.method == "POST":
        plan = request.POST.get("plan")
        p = TestPlan.objects.get(pk=plan)
        q = ~Q(associate_bug='') & Q(plan=p)
        bugs = CaseRecord.objects.values_list('associate_bug', flat=True).filter(q)
        jira_client = get_jira_client()
        tem = []
        for b_id in list(bugs):
            issue = jira_client.issue(b_id)
            org_components = issue.fields.components
            components = [i.name for i in org_components]
            tem += components
        if len(tem)>=1:
            dic = dict(Counter(tem))
            keys, values = zip(*dic.items())
            res = {"modules": keys, "modules_data":values}
        else:
            res = {"modules": [], "modules_data":[]}
        return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_QUERY_SUCCESS, "data": res})
    else:
        return JsonResponse({"status": STATUS_FAILED, "msg": MSG_METHOD_NOT_ALLOWED})


def plan_execute_info(request):
    if request.method == "POST":
        plan = request.POST.get("plan")
        p = TestPlan.objects.get(pk=plan)
        q = ~Q(associate_bug='') & Q(plan=p)
        executors_pk = CaseRecord.objects.values_list('user_id', flat=True).filter(q)
        executors = []
        for e_pk in set(executors_pk):
            executor_name = CustomUser.objects.get(pk=e_pk).username
            executors.append(executor_name)
        if len(executors_pk)>=1:
            dic = dict(Counter(executors_pk))
            _, values = zip(*dic.items())
            res = {"executors": executors, "bugs_count":values}
        else:
            res = {"executors": [], "bugs_count":[]}
        processes = []
        for e in set(executors_pk):
            t = Task.objects.get(plan=p, executor=CustomUser.objects.get(pk=e))
            processes.append(t.get_progress)
        res["processes"] = processes
        return JsonResponse({"status": STATUS_SUCCESS, "msg": MSG_QUERY_SUCCESS, "data": res})
    else:
        return JsonResponse({"status": STATUS_FAILED, "msg": MSG_METHOD_NOT_ALLOWED})


def remove_cases_from_plan(request):
    if request.method == "POST":
        param = request.POST.get("param")
        param_id = request.POST.get("param_id")
        user_id = request.POST.get("user_id")
        task_id = request.POST.get("task_id")
        print(param, param_id, type(param_id), task_id, type(task_id), user_id, type(user_id))
        if param == "project":
            sql = "select r.case_id from xtest.xtests_caserecord r inner join xtest.xtests_testcase c on r.case_id=c.id inner join xtest.xtests_testmodule m on c.module_id=m.id inner join xtest.xtests_project p on m.project_id=p.id where p.id='%s' and r.user_id='%s'" % (param_id, user_id)
            with connection.cursor() as cursor:
                cursor.execute(sql)
                cases_ids = [i[0] for i in cursor.fetchall()]
                if not cases_ids:
                    return JsonResponse({"status": STATUS_FAILED, "msg": "该执行者在该项目下无关联用例，无需删除"})
                else:
                    CaseRecord.objects.filter(user_id=user_id, task_id=task_id, case_id__in=cases_ids).delete()
                    return JsonResponse({"status": STATUS_SUCCESS, "msg": "删除成功"})
        elif param == "module":
            sql = "select r.case_id from xtest.xtests_caserecord r inner join xtest.xtests_testcase c on r.case_id=c.id inner join xtest.xtests_testmodule m on c.module_id=m.id where m.id='%s' and r.user_id='%s'" % (
            param_id, user_id)
            with connection.cursor() as cursor:
                cursor.execute(sql)
                cases_ids = [i[0] for i in cursor.fetchall()]
                if not cases_ids:
                    return JsonResponse({"status": STATUS_FAILED, "msg": "该执行者在该模块下无关联用例，无需删除"})
                else:
                    CaseRecord.objects.filter(user_id=user_id, task_id=task_id, case_id__in=cases_ids).delete()
                    return JsonResponse({"status": STATUS_SUCCESS, "msg": "删除成功"})
        elif param == "case":
            CaseRecord.objects.filter(user_id=user_id, task_id=task_id, case_id__in=json.loads(param_id)).delete()
            return JsonResponse({"status": STATUS_SUCCESS, "msg": "删除成功"})
        else:
            return JsonResponse({"status": STATUS_FAILED, "msg": "参数错误"})
    else:
        return JsonResponse({"status": STATUS_FAILED, "msg": MSG_METHOD_NOT_ALLOWED})
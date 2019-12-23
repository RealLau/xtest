from PIL import Image
import xlrd
from .PUBLIC_MESSAGE import REQUIRED_SECTIONS
from django.conf import settings
from jira import JIRA


def resize_upload_file(file_path, size=(80, 80)):
    img = Image.open(fp=file_path)
    out = img.resize(size=size, resample=Image.ANTIALIAS)
    out.save(fp=file_path, quality=100)


def resize_upload_file_for_tree(org_file_path, des_file_path, size=(24, 24)):
    img = Image.open(fp=org_file_path)
    out = img.resize(size=size, resample=Image.ANTIALIAS)
    out.save(fp=des_file_path, quality=100)


def data_check(file_path):
    # ['模块', '标题', '描述', '前提条件', '步骤', '期望结果', '优先级']
    data = {}
    book = xlrd.open_workbook(file_path)
    projects = book.sheet_names()
    for p_name in projects:
        sh = book.sheet_by_name(p_name)
        actual_sections = sh.row_values(0)
        if not all(ele in actual_sections for ele in REQUIRED_SECTIONS):
            return "Row: 0, 缺少必要字段，请检查"
        else:
            index_col_module = actual_sections.index("模块")
            index_col_title = actual_sections.index("标题")
            index_col_desc = actual_sections.index("描述")
            index_col_preconditions = actual_sections.index("前提条件")
            index_col_steps = actual_sections.index("步骤")
            index_col_expectation = actual_sections.index("期望结果")
            index_col_priority = actual_sections.index("优先级")
            module_name_pre = sh.cell_value(1, index_col_module)
            if module_name_pre == "":
                return "首行模块名不能为空"
            module_case_dic = {module_name_pre: []}
            for r in range(2, sh.nrows):
                module_name = sh.cell_value(r, index_col_module)
                if module_name == "":
                    module_name = module_name_pre
                else:
                    module_name_pre = module_name
                    module_case_dic[module_name_pre] = []
                case_title = sh.cell_value(r, index_col_title)
                case_desc = sh.cell_value(r, index_col_desc)
                case_preconditions = sh.cell_value(r, index_col_preconditions)
                case_steps = sh.cell_value(r, index_col_steps)
                case_expectation = sh.cell_value(r, index_col_expectation)
                case_priority = sh.cell_value(r, index_col_priority)
                if not all([case_title, case_steps, case_expectation, case_priority, case_priority in ['H', 'M', 'L']]):
                    return "Row: %d, 标题、步骤、期望结果、优先级均不能为空，且优先级必须为H或M或L" % r
                else:
                    dic_case = {"title": case_title, "desc": case_desc,
                                "preconditions": case_preconditions, "steps": case_steps,
                                "expectation": case_expectation, "priority": case_priority}
                    module_case_dic[module_name].append(dic_case)
            data[p_name] = module_case_dic
    print(data)
    return data


def get_jira_client():
    options = settings.JIRA_CONFIG["options"]
    auth = settings.JIRA_CONFIG["auth"]
    jira = JIRA(options=options, auth=auth)
    return jira
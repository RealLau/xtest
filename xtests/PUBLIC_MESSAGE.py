REQUIRED_SECTIONS = ['模块', '标题', '描述', '前提条件', '步骤', '期望结果', '优先级']
# project: 1, module: 2, plan: 3, case: 4
NUMBER_TYPE = {"1": "project", "2": "module", "3": "plan", "4": "case"}
CASE_COLOR_DIC = {"Pending": "black", "Pass": "green", "Fail": "red", "Block": "gray"}
MSG_USERNAME_OR_PASSWORD_WRONG = "用户名或密码错误"
STATUS_SUCCESS = 1
STATUS_FAILED = 0
MSG_METHOD_NOT_ALLOWED = "不允许的方法"
MSG_INVALID_KEY_DATA = "参数错误"
MSG_INVALID_DATA = "创建数据错误"
MSG_OK = "OK"
MSG_DELETE_SUCCESS = "删除成功"
MSG_DELETE_FAILED = "删除失败:{info}"
MSG_CREATE_SUCCESS = "创建成功"
MSG_MODIFY_SUCCESS = "修改成功"
MSG_MODIFY_FAIL = "修改失败"
MSG_QUERY_SUCCESS = "查询成功"
MSG_MISSING_REQUIRED_FIELDS = "{field}不能为空"
MSG_ASSOCIATE_SUCCESS = "关联成功"
MSG_ALREADY_HAVE_SAME_RECORD = "关联失败：用例'{case}'已经存在于计划{plan}中"
MSG_USER_ALREADY_HAVE_INCOMPLETE_TASK = "失败：该用户已有任务，请直接关联新用例即可"
MSG_BATCH_CREATE_SUCCESS = "批量创建成功"
MSG_BATCH_CREATE_FAILED = "批量创建失败"
MSG_CASE_EXECUTE_SUCCESS = "执行成功"

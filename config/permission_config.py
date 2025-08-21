from tools.public.enum import OperationType


class permissionConfig:
    """
    权限配置类，用于定义系统中各个模块及其对应的权限。

    该类包含两个主要属性：
    - modules: 定义系统中可用的模块列表，每个模块包含模块标识和模块名称。
    -模块名称 需要和数据库模型的表名保持一致，如 UserModel,RoleModel(权限校验会自动小写,去除Model)


    - permissions: 根据 modules 自动生成每个模块对应的权限列表，
                包含查看、编辑、删除、新增、导入、导出等操作权限。

    - 如需默认字符不够，要新增权限字符，可以使用 permissions.append() 方法添加新的权限字典。


    - 操作类型 使用枚举类 OperationType
    from tools.public.enum import OperationType
    """

    modules = [
        {"module_key": "user", "module_name": "用户"},
        {"module_key": "role", "module_name": "角色"},
        {"module_key": "post", "module_name": "岗位"},
        {"module_key": "dept", "module_name": "部门"},
    ]
    permissions = {
        item["module_key"]: [
            {
                "key": f"{item['module_key']}:{OperationType.QUERY.code}",
                "name": f"{item['module_name']}:{OperationType.QUERY.description}",
            },
            {
                "key": f"{item['module_key']}:{OperationType.UPDATE.code}",
                "name": f"{item['module_name']}:{OperationType.UPDATE.description}",
            },
            {
                "key": f"{item['module_key']}:{OperationType.DELETE.code}",
                "name": f"{item['module_name']}:{OperationType.DELETE.description}",
            },
            {
                "key": f"{item['module_key']}:{OperationType.CREATE.code}",
                "name": f"{item['module_name']}:{OperationType.CREATE.description}",
            },
            {
                "key": f"{item['module_key']}:{OperationType.IMPORT.code}",
                "name": f"{item['module_name']}:{OperationType.IMPORT.description}",
            },
            {
                "key": f"{item['module_key']}:{OperationType.EXPORT.code}",
                "name": f"{item['module_name']}:{OperationType.EXPORT.description}",
            },
        ]
        for item in modules
    }
    # 自定义配置权限
    permissions["permissions"] = [
        {"key": f"permissions:{OperationType.QUERY.code}", "name": f"权限字符:{OperationType.QUERY.description}"},
    ]
    permissions["log"]= [
        {"key": f"log:{OperationType.QUERY.code}", "name": f"日志:{OperationType.QUERY.description}"},
    ]

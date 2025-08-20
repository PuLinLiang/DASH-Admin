# 项目说明文档

## 项目概述

DASH-Admin是一个使用纯python代码构建的WEB应用系统,使用python代码即可完成前端 和后端的开发,

基于Python、Dash构建的企业级后台管理系统快速开发基础平台，提供权限控制、路由管理、日志系统和通用CRUD操作功能。实现了的权限验证和数据访问控制。



### 技术栈
- **后端**: Python, SQLAlchemy 2.0
- **前端框架**: Dash
- **数据库**: MySQL
- **UI组建库及官网** [feffery_antd_components](https://fac.feffery.tech/),[feffery_utils_components](https://fuc.feffery.tech/)
- **权限**: 基于角色的访问控制(RBAC)

### 项目结构

```
├── app.py                 # 应用入口
├── server.py              # 服务启动
├── config/                # 配置文件
├── models/                # 数据模型和服务
├── views/                 # 页面视图
├── callbacks/             # 回调函数
├── tools/                 # 工具函数
├── assets/                # 静态资源
└── docs/                  # 文档
```


## 🧩 核心功能模块

- 用户管理：创建、删除、修改用户信息, 分配角色和部门岗位。
- 角色管理：定义角色及其数据范围和操作权限。
- 权限分配：绑定角色与页面访问、操作权限。
- 数据隔离：限制角色只能查看指定部门的数据。
- 前端控制：根据权限动态启用/禁用按钮或菜单项,根据可以访问页面渲染菜单和访问控制。

- 日志系统：记录用户操作日志，可配置保存天数,可以整体控制输出,储存开关,也可以分别管理 文件,控制台,数据库存储, 兼容原生日志,和app.logger日志。
  - 日志记录 : 手动输入日志消息,模块,操作动作, 自动获取用户信息,和iP地址等额外信息,也可以传入额外信息
  - 日志装饰器 :  装饰器可以传入函数入参,可以记录函数运行时间等

- 路由系统:只需要在路由配置文件里一次性配置好页面关联的权限,和视图位置,即可自动生成菜单导航,访问url 自动渲染,自动鉴权是否拥有访问权限
  - 根据配置文件,会处理公共页面,标准页面,独立渲染页面,菜单栏渲染(权限内)
  - 访问的时候会自动校验权限放行,公共页面直接访问,独立渲染自动识别,无权页面不会渲染菜单 url访问会返回403,

- 通用CRUD: 提供通用的增删改查功能--    ---(对对多关系 需要重写 增加关联字段校验)
  - 查询: 校验使用有查询权限,   以及自动过滤数据范围
  - 修改: 校验使用有修改权限,以及校验修改数据是否在数据范围,涉及部门等变更会校验是否在数据范围内
  - 删除: 校验使用有删除权限,以及校验删除数据是否在数据范围,还会自动检查该数据是否存在关联数据,需要再删除关联检查文件配置
  - 新增: 校验使用有新增权限,以及校验新增数据是否在数据范围,涉及部门等变更会校验是否在数据范围内,
  
### 1. 权限系统
系统采用RBAC(基于角色的访问控制)模型，主要包含以下实体：
## 🔐 权限模型设计

权限分为三个层级：

| 层级 | 示例                                                        | 说明           |
|------|-----------------------------------------------------------|--------------|
| 页面访问 | `access`                                                  | 是否可以查看该页面    |
| 操作权限 | `query`, `create`, `update`, `delete`, `import`, `export` | 控制页面内部具体操作权限 |
| 数据范围 | `Dept`, `Dept_with_child`                                 | 控制角色能访问部门类型  |

## 权限绑定方式

- 角色通过 `sys_role_to_permission` 表绑定多个权限对象。
- 每个权限对象对应一个页面，并拥有独立的操作权限字段。
- 用户通过 `sys_role_to_sys_user` 表绑定多个角色。


## 🛠️ 权限配置流程

### 配置角色权限步骤

1. 进入角色编辑页面。
2. 选择或输入角色名称。
3. 设置数据范围（如“本部门”则需指只能访问选择部门,如果本部门及以下则需指只能访问选择部门及以下子部门）。
4. 在权限树中勾选需要授权的页面及其操作权限。
5. 提交后保存。

## 📈 权限验证流程图解

```
[用户登录]
       │
       ▼
[加载用户角色]
       │
       ▼
[获取角色关联权限]
       │
       ▼
[判断是否为超级管理员]
   ┌───────────────┐
   │     是         │          否
   ▼               ▼
[跳过权限检查]   [检查是否允许访问当前页面]
       │               │
       ▼               ▼
[进入页面]      [判断是否允许执行具体操作]
                       │
                       ▼
                   [允许/禁止操作]
```




### 2. 🔄 路由系统
- 路由系统使用`RouterConfig`类统一管理路由配置,
- 配置好后,自动生成侧边导航菜单,数据库页面信息,数据库权限字符和页面关联,访问url 后自动鉴权是否有权访问,自动返回对应的页面元素渲染

#### 2.1 页面权限配置
页面权限配置定义在`<mcfile name="permission_config.py" path="\config\permission_config.py"></mcfile>`中，采用`PermissionConfig`类统一管理：
***(添加数据库模型类名称后自动生成,访问,查询,新增,修改,删除,导入,导出权限)***

```python
  modules = [
        {"module_key": "user", "module_name": "用户"},  # 添加权限模型名称 和数据库表模型类名称对应,如 UserModal  ,只需要user即可,前缀且为小写
    ]

```

#### 2.2路由配置
路由配置定义在`<mcfile name="router_config.py" path="\config\router_config.py"></mcfile>`中，采用`RouterConfig`类统一管理：

```python
class RouterConfig:
    # 首页路径
    core_side_menu: List[Dict[str, Any]] = [{
        "component": "SubMenu",
        "props": {
            "key": "system",
            "title": "系统管理",
            "icon": "antd-setting",
        },
        "children": [
            {
                "component": "Item",
                "props": {
                    "key": "/system/user",
                    "title": "用户管理",
                    "href": "/system/user",
                    "icon": "antd-user",
                    "view": "views.system.sys_user.render",  # 页面视图模块路径
                    "page_type": "standard",
                    "show_sidebar": True,
                },
            },
        ]}

    ]
```
### 3.💡  日志系统
- 日志系统, 可以兼容原生日志,自定义日志,和DASH的 app.logger 日志
- 统一控制 输出 存入等
- 模块名称,和操作类型 使用 tools.pubilc.enum 枚举类 里的LogModule,OperationType ,已经封装到自定义日志类
#### 3.1 日志配置

全局日志配置在`<mcfile name="base_config.py" path="\config\base_config.py"></mcfile>`中定义：

```python
class BaseConfig:
    # 日志配置
    #----------------------------------------------------------全局 日志配置--------------------------------------------------------------------
    # 日志总开关
    ENABLE_LOGGING = True  # 全局日志开关，设置为 True 表示开启日志功能
    LOG_LEVEL = "WARNING"  # 全局日志级别，当前设置为 INFO 级别
    LOG_SENSITIVE_FIELDS = ['password', 'token']  # 需要脱敏的敏感字段


    # 控制台日志配置
    LOG_TO_CONSOLE = True  # 是否将日志输出到控制台，设置为 True 表示开启控制台日志
    LOG_CONSOLE_LEVEL = "DEBUG"  # 控制台日志级别，当前设置为 DEBUG 级别

    # 文件日志配置
    LOG_TO_FILE = True  # 是否将日志输出到文件，设置为 True 表示开启文件日志
    LOG_FILE_PATH = "logs/app.log"  # 日志文件的存储路径
    LOG_FILE_LEVEL = "INFO"  # 文件日志级别，当前设置为 INFO 级别
    LOG_FILE_BACKUP_COUNT = 30  # 日志文件的备份数量
    LOG_ROTATE_WHEN = "midnight"  # 日志文件轮转的时间点，设置为午夜
    LOG_ROTATE_INTERVAL = 1  # 日志文件轮转的间隔，单位根据 LOG_ROTATE_WHEN 确定
    LOG_FILE_ENCODING = "utf-8"  # 日志文件的编码格式
    LOG_FILE_MAX_BYTES = 10485760  # 单个日志文件最大大小(10MB)
    LOG_FILE_COMPRESS = True  # 是否压缩历史日志

    # 数据库日志配置
    LOG_TO_DB = True  # 是否将日志输出到数据库，设置为 True 表示开启数据库日志
    LOG_DB_LEVEL = "WARNING"  # 数据库日志级别，当前设置为 WARNING 级别
    LOG_DB_BATCH_SIZE = 500  # 数据库日志批量写入的数量 
    LOG_DB_FLUSH_INTERVAL = 10.0  # 数据库日志刷新的间隔时间，单位为秒
    LOG_QUEUE_MAX_SIZE = 8000  # 日志队列最大长度，防止内存溢出
    LOG_DB_RETRY_MAX = 3  # 数据库写入最大重试次数
    LOG_DB_RETRY_DELAY = 1.0  # 重试间隔(秒)
    LOG_EMERGENCY_PATH = "logs/emergency"  # 应急日志文件存储路径
```

#### 3.2 日志使用

自定义日志类`DashLogger`在`<mcfile name="logger.py" path="d:\it-pro\tools\sys_log\logger.py"></mcfile>`中实现：

```python
from tools.sys_log.logger import dash_logger
    dash_logger.error(
        f"失败: {str(e)}",
        logmodule=dash_logger.logmodule.BASE_SERVICE,  # 日志模块 使用枚举值
        operation=sdash_logger.operation.QUERY,      # 操作类型 使用枚举值
    )

```

#### 3.3 操作日志装饰器

系统提供了`log_operation`装饰器用于记录操作日志：

```python
 @dash_logger.log_operation(
        "创建数据",
        logmodule=dash_logger.logmodule.BASE_SERVICE,
        operation=dash_logger.operation.CREATE,
    )
    def create(self, **kwargs) -> T:
        """
```

## 项目启动教程
### 1. 安装依赖
首先确保你已经安装了 Python 环境（建议使用 Python 3.8 及以上版本），然后在项目根目录下执行以下命令安装项目依赖：
```
pip install -r requirements.txt
```

### 2. 数据库配置
确保你已经配置好数据库连接信息，项目使用 SQLAlchemy 进行数据库操作。
数据库配置在`<mcfile name="base_config.py" path="\config\base_config.py"></mcfile>`中定义：
```python

class DB_Config:
    """
        数据库配置类，支持从环境变量读取配置
    
        属性:
            URL (str): 数据库连接URL
            ECHO (bool): 是否输出SQL日志
            ...其他配置参数
    """
    # 从环境变量读取配置，无则使用默认值
    URL: str = os.getenv('DB_URL', 'sqlite:///dash_admin.db')  # 数据库连接URL，默认使用SQLite内存数据库
    ECHO: bool = os.getenv('DB_ECHO', 'False').lower() == 'true'  # 是否输出SQL日志，默认不输出
    POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '50'))  # 数据库连接池大小，默认50
    MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '80'))  # 连接池最大溢出连接数，默认80
    POOL_TIMEOUT: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))  # 连接池获取连接的超时时间(秒)，默认30秒
    POOL_RECYCLE: int = int(os.getenv('DB_POOL_RECYCLE', '1800'))  # 连接池连接回收时间(秒)，默认1800秒
    MONITOR_POOL: bool = os.getenv('DB_MONITOR_POOL', 'False').lower() == 'true'  # 是否监控连接池，默认不监控
    DEBUG_MEMORY: bool = os.getenv('DB_DEBUG_MEMORY', 'False').lower() == 'true'  # 是否调试内存使用，默认不调试

```

### 3. 初始化
自动初始化数据库，包括创建表、初始化数据 菜单导航,页面,以及权限等。
```
# 数据库迁移
alembic upgrade head
# 初始化数据库
python init_db.py
```

### 4. 项目启动
在项目根目录下执行以下命令启动项目：
```
python app.py
```

### 5. 访问
项目默认监听8050端口，你可以在浏览器中访问`http://127.0.0.1:8050`来查看项目页面。

### 6. 登录
登录账号: admin
登录密码: Admin123+admin123
## 其他文档
### 项目文档在`docs`目录下，包括项目设计、项目开发、项目维护等方面的文档。

[二次开发文档](/docs/二次开发教程.md)
- 
[服务基类_内部接口说明文档](/docs/服务基类_内部方法.md)
- 
[服务基类_通用方法说明文档](/docs/服务基类_通用方法.md)
-


## 截图
![登录页面](/docs/login.png) 
![部门管理](/docs/dept.png) 
![岗位管理](/docs/post.png) 
![新建角色](/docs/role.png)
![角色列表](/docs/roles.png)
![角色权限配置](/docs/role-per.png)
![用户管理](/docs/user.png) 
![日志管理](/docs/log.png)
![权限管理](/docs/per.png)





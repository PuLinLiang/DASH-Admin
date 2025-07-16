# 导入本地应用/模块相关包
from feffery_dash_utils.version_utils import (
    check_python_version,
    check_dependencies_version,
)
from server import app,dash_logger
from views.core_pages import render
# 设置路由框架
app.layout = render
# 检查Python版本
check_python_version(min_version="3.8", max_version="3.12")
# 检查关键依赖库版本
check_dependencies_version( 
    rules=[
        {"name": "dash", "specifier": "==2.18.2"},
        {"name": "feffery_antd_components", "specifier": "==0.3.15"},
        {"name": "feffery_utils_components", "specifier": "==0.2.0rc27"},
        {"name": "feffery_dash_utils", "specifier": ">=0.2.4"},
    ]
) 
if __name__ == "__main__":
    # 非正式环境下开发调试预览使用 
    # 生产环境推荐使用gunicorn启动
    dash_logger.warning("系统启动完成...",logmodule=dash_logger.logmodule.SYSTEM,operation=dash_logger.operation.SYSTEM_START)
    app.run(debug=False) 




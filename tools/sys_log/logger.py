import inspect
import logging
import functools
import time
from flask import request
from typing import Any
from ..public.enum import OperationType, LogModule
from config.base_config import BaseConfig

# 导入配置


class SafeFormatter(logging.Formatter):
    def format(self, record):
        for key in [
            "logmodule",
            "operation",
            "status",
            "duration_ms",
            "description",
            "logmodule_operation",
        ]:
            if not hasattr(record, key):
                setattr(record, key, self._get_default_value(key))
        return super().format(record)

    def _get_default_value(self, key):
        defaults = {
            "logmodule": LogModule.CUSTOM.code,
            "operation": OperationType.CUSTOM.code,
            "logmodule_operation": f"{LogModule.CUSTOM.description}-{OperationType.CUSTOM.description}",
            "status": "成功",
            "duration_ms": 0,
            "description": {},
        }
        return defaults.get(key, None)


class DashLogger:
    """
    一个支持动态参数解析、数据库存储和异步写入的日志类。

    功能：
    - 支持手动记录日志（info, debug, warning, error）
    - 提供装饰器自动记录操作日志
    - 根据配置决定是否将日志写入数据库
    - 使用线程池异步写入数据库，提升性能

    配置项：
    - LOG_TO_DB: 是否启用数据库日志（True/False）
    """

    def __init__(self):
        self.logger = None  # Flask 的 logger 实例
        self.logmodule = LogModule
        self.operation = OperationType

    def init_app(self, app_logger):
        """
        绑定 Flask 的 logger

        参数:
            app_logger (logging.Logger): Flask 默认的 logger 实例
        """
        self.logger = app_logger
        self.logger.propagate = False  # ❗阻止传播到 root logger

    def info(
        self,
        message: str,
        logmodule: LogModule,
        operation: OperationType,
        extra: dict[str, Any] | None = None,
    ):
        """记录 INFO 级别日志
        Args:
            message: 日志消息内容
            module: 日志模块枚举
            operation: 操作类型枚举
            extra: 额外日志字段
        """
        if extra is None:
            extra = {}
        self._log("INFO", message, logmodule, operation, extra)

    def debug(
        self,
        message: str,
        logmodule: LogModule,
        operation: OperationType,
        extra: dict[str, Any] | None = None,
    ):
        """记录 DEBUG 级别日志"""
        if extra is None:
            extra = {}
        self._log("DEBUG", message, logmodule, operation, extra)

    def warning(
        self,
        message: str,
        logmodule: LogModule,
        operation: OperationType,
        extra: dict[str, Any] | None = None,
    ):
        """记录 WARNING 级别日志"""
        if extra is None:
            extra = {}
        self._log("WARNING", message, logmodule, operation, extra)

    def error(
        self,
        message: str,
        logmodule: LogModule,
        operation: OperationType,
        extra: dict[str, Any] | None = None,
    ):
        """记录 ERROR 级别日志"""
        if extra is None:
            extra = {}
        self._log("ERROR", message, logmodule, operation, extra)

    def critical(
        self,
        message: str,
        logmodule: LogModule,
        operation: OperationType,
        extra: dict[str, Any] | None = None,
    ):
        """记录 CRITICAL 级别日志"""
        if extra is None:
            extra = {}
        self._log("CRITICAL", message, logmodule, operation, extra)

    def _merge_dict(self, target, source):
        """
        递归合并两个字典：
        - 如果 key 存在于 target 中且 value 同样是 dict，则继续递归合并；
        - 否则覆盖或新增。
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_dict(target[key], value)
            else:
                target[key] = value

    def _sanitize_data(self, data: dict) -> dict:
        """脱敏敏感字段"""
        if not data:
            return data
        sanitized = data.copy()
        for field in BaseConfig.LOG_SENSITIVE_FIELDS:
            if field in sanitized:
                sanitized[field] = "***"
        return sanitized

    def _format_context(
        self, logmodule: LogModule, operation: OperationType, extra: dict | None = None
    ):
        """
        格式化日志上下文信息，确保字段完整性

        参数:
            logmodule (LogModule): 日志模块枚举
            operation (OperationType): 操作类型枚举
            extra (dict): 用户提供的额外字段
        返回:
            dict: 包含完整日志上下文的字典
        """
        if extra is None:
            extra = {}
        stack = inspect.stack()
        # 动态计算安全索引
        safe_index = min(3, len(stack) - 1)
        caller_frame = stack[safe_index] if len(stack) > 3 else None

        # 添加空值保护
        frame_info = {"log_module": "unknown", "log_funcName": "unknown"}
        if caller_frame and hasattr(caller_frame, "frame"):
            frame_globals = caller_frame.frame.f_globals
            frame_info["log_module"] = frame_globals.get("__name__", "unknown")
            frame_info["log_funcName"] = caller_frame.function
        context = {
            "logmodule": logmodule,
            "operation": operation,
            "logmodule_operation": f"{logmodule.description}-{operation.description}",
            "status": "成功",
            "duration_ms": 0,
            "description": self._sanitize_data(
                {
                    "user_id":"",
                    "ip": self._get_ip(),
                    "页面模块": frame_info["log_module"],
                    "函数名": frame_info["log_funcName"],
                    "行号": caller_frame.lineno if caller_frame else 0,
                }
            ),
        }

        if extra:
            self._merge_dict(context, extra)
        return context

    def _get_ip(self):
        """
        获取客户端 IP 地址。

        在无请求上下文时返回 ''。
        """
        try:
            return str(request.remote_addr) if request else ""
        except:
            return ""


    def _log(
        self,
        level: str,
        message: str,
        logmodule: LogModule,
        operation: OperationType,
        extra: dict,
    ):
        """
        通用日志方法，处理日志记录的公共逻辑

        参数:
            level (str): 日志级别，如 "INFO", "ERROR"
            message (str): 日志消息内容
            logmodule (LogModule): 日志模块枚举
            operation (OperationType): 操作类型枚举
            extra (dict): 附加信息，用于填充模板和扩展字段
        """
        if not self.logger:
            return
            # 控制台处理器
        extra = self._format_context(logmodule, operation, extra)
        log_method = getattr(self.logger, level.lower())
        log_method(message, exc_info=(level == "ERROR"), extra=extra or {})

    def log_operation(
        self,
        message_str: str,
        logmodule: LogModule,
        operation: OperationType,
        level="INFO",
        extra=None,
    ):
        """
        日志装饰器
        参数:
            message (str):日志消息,支持关联函数的 入参变量,如: 当前访问页面{pathname}
            logmodule (LogModule): 日志模块
            operation (OperationType): 操作类型
            level (str): 日志级别（如 'INFO', 'ERROR'），默认为 'INFO'
            extra (dict): 自定义附加消息
        返回:
            function: 装饰后的函数
        """

        def decorator(f):
            @functools.wraps(f)
            def wrapped(*args, **kwargs):
                try:
                    # 解析函数签名并获取实际参数
                    from inspect import signature

                    sig = signature(f)

                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                    # 构建 action 字符串,为字典形式
                    action_values = dict(bound_args.arguments)
                    try:
                        message_kwargs = ""
                        if message_str:
                            message_kwargs = message_str.format(**action_values)
                    except KeyError as e:
                        raise ValueError(
                            f"Action template missing required parameter: {e}"
                        )

                    # 执行原函数
                    start_time = time.time()
                    result = f(*args, **kwargs)
                    # 构造日志信息
                    duration = int((time.time() - start_time) * 1000)  # 毫秒
                    message = f"{logmodule.description}.{operation.description},{message_kwargs},状态:成功,耗时:{duration}ms"
                    out_extra = {
                        "duration_ms": duration,
                        "status": "成功",
                        "description": {
                            "函数名": f.__name__ if f.__name__ else "未知",
                        },
                    }
                    if extra:
                        out_extra.update(extra)

                    # 根据指定的日志等级记录日志
                    if level.upper() == "INFO":
                        self.info(message, logmodule, operation, extra=out_extra)
                    elif level.upper() == "DEBUG":
                        self.debug(message, logmodule, operation, extra=out_extra)
                    elif level.upper() == "WARNING":
                        self.warning(message, logmodule, operation, extra=out_extra)
                    elif level.upper() == "ERROR":
                        self.error(message, logmodule, operation, extra=out_extra)
                    else:
                        self.info(message, logmodule, operation, extra=out_extra)

                    return result

                except Exception as e:
                    # 异常情况下也记录错误日志
                    error_message = f"函数执行失败:{message_kwargs},错误信息 {str(e)}"
                    self.error(
                        error_message,
                        logmodule,
                        operation,
                        extra={"status": "失败", "error": str(e)},
                    )
                    raise

            return wrapped

        return decorator


# 初始化日志器实例
dash_logger = DashLogger()

import sys
from pathlib import Path
from typing import Optional
from loguru import logger


class LoggerManager:
    def __init__(self):
        # 延迟加载配置以避免循环依赖
        self._config = None
        # 移除 loguru 的默认 handler，由 setup() 统一配置
        logger.remove()
        self._is_setup = False

    @property
    def config(self):
        if self._config is None:
            from app.core.config.settings import settings  # 延迟导入

            self._config = settings.logging
        return self._config

    def _create_log_directory(self, directory: str) -> None:
        """创建日志目录"""
        Path(directory).mkdir(parents=True, exist_ok=True)

    def setup(self) -> None:
        """配置 loguru logger"""
        try:
            if self._is_setup:
                return  # 避免重复配置

            # 解析日志级别
            level = self.config.LOG_LEVEL.upper()

            # 控制台输出
            if self.config.LOG_TO_CONSOLE:
                console_level = self.config.LOG_CONSOLE_LEVEL.upper()
                # 使用 loguru 原生格式
                log_format = (
                    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                    "<level>{level: <8}</level> | "
                    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                    "<level>{message}</level>"
                )

                logger.add(
                    sys.stderr,
                    level=console_level,
                    format=log_format,
                    colorize=True,
                    backtrace=True,
                    diagnose=True,
                )

            # 文件输出
            if self.config.LOG_TO_FILE:
                log_path = Path(self.config.LOG_FILE_PATH)
                log_dir = log_path.parent
                self._create_log_directory(str(log_dir))

                # loguru 原生支持 rotation 和 retention
                rotation = self.config.LOG_ROTATION or "1 day"
                retention = self.config.LOG_RETENTION_PERIOD or "7 days"

                # 文件日志使用更详细的格式
                file_format = (
                    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                    "{level: <8} | "
                    "{name}:{function}:{line} | "
                    "{message}"
                )

                logger.add(
                    str(log_path),
                    level=level,
                    format=file_format,
                    rotation=rotation,
                    retention=retention,
                    compression="zip",  # 压缩旧日志文件
                    backtrace=True,  # 显示完整堆栈跟踪
                    diagnose=True,  # 显示变量值
                    enqueue=True,  # 线程安全
                    encoding="utf-8",  # UTF-8 编码
                )

            self._is_setup = True
            logger.info("✅ Loguru logging setup complete.")

        except Exception as e:
            # 如果配置失败，至少确保有基本的控制台输出
            logger.add(
                sys.stderr,
                level="INFO",
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
                colorize=True,
            )
            logger.error(f"Critical error in logging setup: {e}")

    def get_logger(self, name: Optional[str] = None):
        """
        获取 logger 实例
        loguru 使用单例模式，会自动记录调用位置（模块名、函数名、行号）
        如果提供了 name，会通过 bind 绑定到上下文中
        """
        if name:
            # 使用 bind 绑定模块名，可以通过 {extra[name]} 在格式中访问
            # 但 loguru 会自动记录调用位置，所以通常不需要
            return logger.bind(name=name)
        return logger


logger_manager = LoggerManager()

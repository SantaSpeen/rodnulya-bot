import glob
import logging
import os
import sys
import threading
import traceback
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger

@dataclass
class LoggerConfiguration:
    directory: Path | str
    # mode setup sys.stdout and `info.log`
    mode: str = "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_file: str = "info.log"

    file_debug: bool = True
    file_debug_name: str = "debug.log"

    file_low_debug: bool = False
    file_low_debug_name: str = "super_debug.log"

    module_set: str = "^12"
    prefix_set: str = "<12"
    # format: str = "<green>{elapsed} -- {time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | {extra[module]:%s} | {extra[prefix]:%s} | {message}"
    format: str = "<green>{elapsed} -- {time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | [{module:^10}] {message}"

    def __post_init__(self):
        if isinstance(self.directory, str):
            self.directory = Path(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    @property
    def log_path(self) -> Path:
        return self.directory / self.log_file

    @property
    def file_debug_path(self) -> Path:
        return self.directory / self.file_debug_name

    @property
    def file_low_debug_path(self) -> Path:
        return self.directory / self.file_low_debug_name

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt) or issubclass(exc_type, SystemExit):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.bind(module="Error", prefix="unhandled").error("Unhandled exception:\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

def handle_thread_exception(args):
    exc_type, exc_value, exc_traceback = args.exc_type, args.exc_value, args.exc_traceback
    if issubclass(exc_type, KeyboardInterrupt) or issubclass(exc_type, SystemExit):
        return
    logger.bind(module="ThreadError", prefix="unhandled").error("Unhandled exception in thread:\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

def zip_logs(config: LoggerConfiguration):
    log = logger.bind(module="LoggerSetup", prefix="zip")
    if os.path.exists(config.log_path):
        ftime = os.path.getmtime(config.log_path)
        index = 1
        while True:
            zip_path = config.directory / f"{datetime.fromtimestamp(ftime).strftime('%Y-%m-%d')}-{index}.zip"
            if not os.path.exists(zip_path):
                break
            index += 1
        with zipfile.ZipFile(zip_path, "w") as zipf:
            logs_files = glob.glob(f"{config.directory}/*.log")
            for file in logs_files:
                if os.path.exists(file):
                    zipf.write(file, os.path.basename(file))
                    os.remove(file)
        log.success("Previous logs zipped successfully.")

def hook_logging():
    level_map = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    class InterceptHandler(logging.Handler):
        def emit(self, record):
            level = level_map.get(record.levelno, record.levelno)
            logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.DEBUG)


def setup(config: LoggerConfiguration, hook_logger: bool = False):
    logger.remove()
    fmt = config.format # % (config.module_set, config.prefix_set)
    if sys.stdout:
        logger.add(sys.stdout, level=config.mode, format=fmt, backtrace=True, diagnose=True)
    logger.add(config.log_path, level=config.mode, format=fmt, backtrace=False, diagnose=False, rotation="25 MB")
    if config.file_debug:
        logger.add(config.file_debug_path, level=0, format=fmt, rotation="10 MB")
    if config.file_low_debug:
        logger.add(config.file_low_debug_path, level=0, rotation="10 MB")
    sys.excepthook = handle_exception
    threading.excepthook = handle_thread_exception
    if hook_logger:
        hook_logging()
    logger.bind(module="LoggerSetup", prefix="init").success("Logger initialized.")

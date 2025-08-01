import logging
import logging.config
import os
import sys
from colorlog import ColoredFormatter
from api.constraints import config  # seu dict vindo do config.toml

# Carrega as configurações
logger_cfg = config.get("Logger", {})

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

class RestrictedLoggerFilter(logging.Filter):
    """Permite apenas loggers que comecem com 'api.' ou 'uvicorn.'."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith("api.") or record.name.startswith("uvicorn.")

# Se ativado, aplica a configuração avançada
if logger_cfg.get("enable", False):
    # 1) Nível de log
    LOG_LEVEL = logger_cfg.get("level", "INFO").upper()

    # 2) Garante a existência da pasta logs/
    LOGS_DIR = "logs"
    os.makedirs(LOGS_DIR, exist_ok=True)

    # 3) Formatter colorido para o console
    console_fmt = {
        "()": ColoredFormatter,
        "format": (
            "%(log_color)s%(levelname)-8s%(reset)s"
            " - %(log_color)s[%(name)s]%(reset)s"
            " %(message)s"
        ),
        "log_colors": {
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "bold_red",
        },
    }

    # 4) Formatter de arquivo (texto puro, com ou sem datetime)
    if logger_cfg.get("enable_datetime", False):
        file_format = "%(asctime)s - [%(levelname)s] - %(name)s: %(message)s"
        datefmt     = logger_cfg.get("datetime_format", "%Y-%m-%d %H:%M:%S")
    else:
        file_format = "%(levelname)s - [%(name)s]: %(message)s"
        datefmt     = None

    # 5) Handlers
    handlers = {
        # Console: tudo aparece no terminal
        "console": {
            "class":     "logging.StreamHandler",
            "formatter": "console",
            "stream":    "ext://sys.stdout",
        },
        # louie.log: só logs da aplicação (root logger)
        "louie_file": {
            "class":     "logging.FileHandler",
            "formatter": "file",
            "filename":  os.path.join(LOGS_DIR, "louie.log"),
            "encoding":  "utf-8",
        },
        # api.log: só logs do Uvicorn/FastAPI
        "api_file": {
            "class":     "logging.FileHandler",
            "formatter": "file",
            "filename":  os.path.join(LOGS_DIR, "api.log"),
            "encoding":  "utf-8",
        },
    }
    
    # 6) Adiciona o filtro de restrição
    FULL_LOGS = logger_cfg.get("full_logs", True)
    if not FULL_LOGS:
        filter_instance = RestrictedLoggerFilter()
        for handler_cfg in handlers.values():
            filters = handler_cfg.setdefault("filters", [])
            if isinstance(filters, list):
                filters.append("restricted")

    # 7) Monta o dictConfig
    LOGGING = {
        "version":                  1,
        "disable_existing_loggers": False,
        "filters": {
            "restricted": {
                "()": RestrictedLoggerFilter,
            },
        },
        "formatters": {
            "console": console_fmt,
            "file": {
                "format":  file_format,
                "datefmt": datefmt,
            },
        },
        "handlers": handlers,
        "loggers": {
            # raiz: suas chamadas a get_logger(...)
            "": {
                "handlers":  ["console", "louie_file"],
                "level":     LOG_LEVEL,
                "propagate": False,
            },
            # Uvicorn e sub-loggers
            "uvicorn": {
                "handlers":  ["console", "api_file"],
                "level":     LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers":  ["console", "api_file"],
                "level":     LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers":  ["console", "api_file"],
                "level":     LOG_LEVEL,
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(LOGGING)

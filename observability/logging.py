import logging,json
from core.config import settings


class JsonFormatter(logging.Formatter):
    def format(self,record):
        return json.dumps({"level":record.levelname,"name":record.name,"message":record.getMessage()},ensure_ascii=False)


def configure_logging():
    h=logging.StreamHandler(); h.setFormatter(JsonFormatter())
    root=logging.getLogger(); root.handlers=[h]; root.setLevel(settings.log_level.upper())

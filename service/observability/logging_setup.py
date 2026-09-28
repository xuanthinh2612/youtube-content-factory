import logging,json
from service.settings import app_settings


class StructuredJsonLogFormatter(logging.Formatter):
    def format(self,record):
        return json.dumps({"level":record.levelname,"name":record.name,"message":record.getMessage()},ensure_ascii=False)


def configure_application_logging():
    h=logging.StreamHandler(); h.setFormatter(StructuredJsonLogFormatter())
    root=logging.getLogger(); root.handlers=[h]; root.setLevel(app_settings.log_level.upper())

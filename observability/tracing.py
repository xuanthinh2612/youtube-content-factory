import time,logging
from contextlib import contextmanager

logger=logging.getLogger("trace")

@contextmanager
def trace_agent(name,tier):
    start=time.perf_counter()
    logger.info(f"agent.start name={name} tier={tier}")
    try:
        yield
        logger.info(f"agent.done name={name} elapsed={time.perf_counter()-start:.3f}")
    except Exception:
        logger.exception(f"agent.error name={name}")
        raise

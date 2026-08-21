import logging
import time
from fastapi import Request

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def logger_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000

    if duration_ms > 500:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(
            f"Slow request: {request.method} {request.url.path} from {client_ip} took {duration_ms:.2f}ms"
        )

    return response
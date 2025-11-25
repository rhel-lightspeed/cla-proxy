import logging
from cla_proxy.error_handlers import register_exception_handlers
from cla_proxy.middleware import timeout_middleware
from fastapi import FastAPI
from contextlib import asynccontextmanager
from cla_proxy.config import Settings
from cla_proxy.routes.v1 import endpoints as v1_endpoints

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.config = Settings()
    yield


app = FastAPI(
    title="cla-proxy",
    description="An proxy for RHEL Lightspeed LLM inference",
    version="0.1.0",
    contact={"name": "RHEL Lightspeed Team", "email": "rhel-lightspeed-sst@redhat.com"},
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    root_path="/",
    # Disable documentation for now.
    docs_url=None,
    redoc_url=None,
    # Objects that will be available across the lifespan of the server.
    lifespan=lifespan,
)

app.middleware("http")(timeout_middleware)

# Register exception handlers for standard error responses
register_exception_handlers(app)


@app.get("/health")
async def health_check() -> None:
    """Health check endpoint for infrastructure probes."""
    return None


app.include_router(v1_endpoints.router, prefix="/v1")

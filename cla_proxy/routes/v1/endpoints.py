import logging
from typing import cast
from cla_proxy.config import Auth, Backend
from fastapi import APIRouter, Request
import httpx

from cla_proxy.routes.v1.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelsResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat/completions")
async def chat_completions(request: Request, data: ChatCompletionRequest):
    backend_settings = cast(Backend, request.app.state.config.backend)
    auth_settings = cast(Auth, backend_settings.auth)

    with httpx.Client(
        cert=(str(auth_settings.cert_file), str(auth_settings.key_file)),
        timeout=backend_settings.timeout,
        mounts=backend_settings.proxies,
    ) as client:
        endpoint = f"{backend_settings.endpoint}/chat/completions"
        result = client.post(endpoint, json=data.model_dump_json())

    return ChatCompletionResponse(**result.json())


@router.get("/models")
async def list_models(request: Request) -> ModelsResponse:
    backend_settings = cast(Backend, request.app.state.config.backend)
    auth_settings = cast(Auth, backend_settings.auth)

    with httpx.Client(
        cert=(str(auth_settings.cert_file), str(auth_settings.key_file)),
        timeout=backend_settings.timeout,
        mounts=backend_settings.proxies,
    ) as client:
        endpoint = f"{backend_settings.endpoint}/models"
        result = client.get(endpoint)

    return ModelsResponse(**result.json())

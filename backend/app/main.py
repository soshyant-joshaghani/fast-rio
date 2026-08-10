import re
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from scalar_fastapi import (
    AgentScalarConfig,
    DocumentDownloadType,
    Layout,
    get_scalar_api_reference,
)
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings

SCALAR_OAUTH2_SCHEME = "OAuth2PasswordBearer"

SCALAR_AUTHENTICATION: dict[str, Any] = {
    "preferredSecurityScheme": SCALAR_OAUTH2_SCHEME,
}

SCALAR_OVERRIDES: dict[str, Any] = {
    "theme": "elysiajs",
    "showToolbar": "localhost",
    "operationTitleSource": "summary",
    "defaultOpenFirstTag": True,
}


def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "untagged"
    methods = "_".join(sorted(method.lower() for method in (route.methods or set())))
    path = route.path_format.strip("/") or "root"
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", f"{tag}_{methods}_{path}_{route.name}")
    return normalized.strip("_")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url=None,
    generate_unique_id_function=custom_generate_unique_id,
)


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        routes=app.routes,
    )
    token_url = f"{settings.API_V1_STR}/base/login/access-token"
    security_schemes = openapi_schema.get("components", {}).get("securitySchemes", {})
    oauth2 = security_schemes.get(SCALAR_OAUTH2_SCHEME)
    if oauth2 and "flows" in oauth2 and "password" in oauth2["flows"]:
        oauth2["flows"]["password"]["tokenUrl"] = token_url

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]


@app.get("/sdoc", include_in_schema=False)
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=settings.PROJECT_NAME,
        layout=Layout.MODERN,
        show_sidebar=True,
        show_developer_tools="localhost",
        persist_auth=True,
        hide_client_button=False,
        hide_models=False,
        hide_search=False,
        hide_test_request_button=False,
        hide_dark_mode_toggle=False,
        with_default_fonts=True,
        document_download_type=DocumentDownloadType.BOTH,
        authentication=SCALAR_AUTHENTICATION,
        agent=AgentScalarConfig(disabled=True),
        overrides=SCALAR_OVERRIDES,
    )


if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

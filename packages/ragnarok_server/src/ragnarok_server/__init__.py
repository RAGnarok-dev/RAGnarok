import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ragnarok_server.exceptions import (
    CustomRuntimeError,
    HTTPException,
    custom_http_exception_handler,
    custom_runtime_error_handler,
)
from ragnarok_server.rdb.engine import init_rdb
from ragnarok_server.router import component, pipeline
from ragnarok_toolkit import config

env = config.ENV

app = FastAPI(
    title="Ragnarok Server",
    redoc_url=None,
    docs_url="/api-docs" if env == "dev" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(CustomRuntimeError, custom_runtime_error_handler)

app.include_router(component.router)
app.include_router(pipeline.router)


@app.get("/ping")
async def ping():
    return "pong"


# TODO register permission handler


def run_server():
    asyncio.run(init_rdb())
    uvicorn.run(app, host="0.0.0.0", port=int(config.SERVER_PORT))

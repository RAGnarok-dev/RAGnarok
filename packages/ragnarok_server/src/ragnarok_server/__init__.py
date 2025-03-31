import uvicorn
from fastapi import FastAPI
from ragnarok_toolkit import config
from .permissions import init_permission_system

env = config.ENV

app = FastAPI(
    title="Ragnarok Server",
    redoc_url=None,
    docs_url="/api-docs" if env == "dev" else None,
)


# Register startup event to initialize the permission system
@app.on_event("startup")
async def startup_event():
    await init_permission_system()


# TODO register permission handler


def run_server():
    uvicorn.run(app, host="0.0.0.0", port=int(config.SERVER_PORT))

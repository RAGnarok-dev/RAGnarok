import uvicorn
from fastapi import FastAPI
from ragnarok_toolkit import config

env = config.ENV

app = FastAPI(
    title="Ragnarok Server",
    redoc_url=None,
    docs_url="/api-docs" if env == "dev" else None,
)


# TODO server initialization


def run_server():
    uvicorn.run(app, host="0.0.0.0", port=int(config.SERVER_PORT))

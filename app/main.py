from fastapi import FastAPI

from app.presentation.router_order import router_order
from app.utils.create_container import create_container
from app.utils.logger import configure_logging


configure_logging()

app = FastAPI()
container = create_container()
app.container = container
app.include_router(router_order)


@app.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

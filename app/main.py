from fastapi import FastAPI

from app.logger import configure_logging
from app.presentation.router_order import router_order

configure_logging()

app = FastAPI()
app.include_router(router_order)


@app.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

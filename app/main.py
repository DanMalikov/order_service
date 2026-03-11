from fastapi import FastAPI

from app.api.orders import router as orders_router


app = FastAPI()
app.include_router(orders_router)


@app.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

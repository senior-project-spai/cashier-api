# fastapi
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

# pydantic for Model
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Iresponse_product(BaseModel):
    barcode: str


@app.get("/_api/product/{barcode}", response_model=Iresponse_product)
def get_product(barcode: str):
    return {
        'barcode': barcode,
    }

# fastapi
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

# pydantic for Model
from pydantic import BaseModel

# sql
import pymysql
from pymysql.cursors import DictCursor

import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event('startup')
def startup_event():
    global sql_connection, kafka_producer
    sql_connection = pymysql.connect(host=os.getenv('MYSQL_HOST'),
                                     port=int(os.getenv('MYSQL_PORT')),
                                     user=os.getenv('MYSQL_USER'),
                                     passwd=os.getenv('MYSQL_PASS'),
                                     db=os.getenv('MYSQL_DB'))


@app.on_event('shutdown')
def shutdown_event():
    sql_connection.close()


class Iresponse_product(BaseModel):
    barcode: str
    name:str
    price:float

@app.get("/_api/product/{barcode}",response_model=Iresponse_product)
def get_product(barcode: str):
    sql_connection.ping(reconnect=True)
    with sql_connection.cursor(cursor=DictCursor) as cursor:
        query_product = ("SELECT *"
                         "FROM Product "
                         "WHERE id = %s ")
        cursor.execute(query_product, (int(barcode)))
        product = cursor.fetchone()

    return {
        'barcode': barcode,
        'name':product['name'],
        'price':float(product['price']),
    }

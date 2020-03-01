# fastapi
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

# pydantic for Model
from pydantic import BaseModel

# List for Model
from typing import List, Set, Dict

# sql
import pymysql
from pymysql.cursors import DictCursor

import os

# logging
import logging
logger = logging.getLogger('api')

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
    product_name: str
    price: float


class Irequest_transaction(BaseModel):
    time: int
    branch_id: int = None
    customer_id: int = None


class Iresponse_transaction(BaseModel):
    transaction_id: int


class IProduct(BaseModel):
    barcode: str
    product_name: str
    price: float
    quantity: int


class Irequest_product_transaction(BaseModel):
    transaction_id: int
    product_list: List[IProduct]


class Irequest_transaction_faceimage(BaseModel):
    transaction_id: int
    face_image_id: int


class Iresponse_get_transaction(BaseModel):
    id: int
    time: int
    branch_id: int
    customer_id: int
    products: List[Dict]


@app.get("/_api/product/{barcode}", response_model=Iresponse_product)
def get_product(barcode: str):
    sql_connection = pymysql.connect(host=os.getenv('MYSQL_HOST'),
                                     port=int(os.getenv('MYSQL_PORT')),
                                     user=os.getenv('MYSQL_USER'),
                                     passwd=os.getenv('MYSQL_PASS'),
                                     db=os.getenv('MYSQL_DB'))
    sql_connection.ping(reconnect=True)
    with sql_connection.cursor(cursor=DictCursor) as cursor:
        query_product = ("SELECT *"
                         "FROM Product "
                         "WHERE id = %s ")
        cursor.execute(query_product, (int(barcode)))
        product = cursor.fetchone()
    sql_connection.close()
    return {
        'barcode': barcode,
        'product_name': product['name'],
        'price': float(product['price']),
    }


@app.post("/_api/transaction/", response_model=Iresponse_transaction)
def add_transaction(item: Irequest_transaction):
    sql_connection = pymysql.connect(host=os.getenv('MYSQL_MASTER_HOST'),
                                     port=int(os.getenv('MYSQL_MASTER_PORT')),
                                     user=os.getenv('MYSQL_MASTER_USER'),
                                     passwd=os.getenv('MYSQL_MASTER_PASS'),
                                     db=os.getenv('MYSQL_MASTER_DB'))

    with sql_connection.cursor() as cursor:
        query_product_with_customer = ("INSERT INTO `Transaction` (`time`,`branch_id`,`customer_id`) "
                                       "VALUES (%(time)s,%(branch_id)s,%(customer_id)s)")
        query_product = ("INSERT INTO `Transaction` (`time`,`branch_id`) "
                         "VALUES (%(time)s,%(branch_id)s)")
        if item.customer_id is None:
            cursor.execute(query_product, {
                'time': item.time,
                'branch_id': item.branch_id
            })
        else:
            cursor.execute(query_product_with_customer, {
                'time': item.time,
                'branch_id': item.branch_id,
                'customer_id': item.customer_id
            })

        sql_connection.commit()  # commit changes
        transaction_id = cursor.lastrowid
    sql_connection.close()
    return {
        'transaction_id': int(transaction_id)
    }


def query_transaction(transaction_id: int):
    sql_connection = pymysql.connect(host=os.getenv('MYSQL_MASTER_HOST'),
                                     port=int(os.getenv('MYSQL_MASTER_PORT')),
                                     user=os.getenv('MYSQL_MASTER_USER'),
                                     passwd=os.getenv('MYSQL_MASTER_PASS'),
                                     db=os.getenv('MYSQL_MASTER_DB'), autocommit=True)
    row = None
    with sql_connection.cursor(cursor=DictCursor) as cursor:
        query = ("SELECT id, time, branch_id, customer_id "
                 "FROM Transaction "
                 "WHERE id=%(transaction_id)s "
                 "LIMIT 1;")
        cursor.execute(query, {'transaction_id': transaction_id})
        cursor.fetchone()
    sql_connection.close()
    return row


def query_transaction_product(transaction_id: int):
    sql_connection = pymysql.connect(host=os.getenv('MYSQL_MASTER_HOST'),
                                     port=int(os.getenv('MYSQL_MASTER_PORT')),
                                     user=os.getenv('MYSQL_MASTER_USER'),
                                     passwd=os.getenv('MYSQL_MASTER_PASS'),
                                     db=os.getenv('MYSQL_MASTER_DB'), autocommit=True)
    rows = None
    with sql_connection.cursor(cursor=DictCursor) as cursor:
        query = ("SELECT "
                 "  TransactionProduct.product_id AS id, "
                 "  TransactionProduct.quantity, "
                 "  Product.name, "
                 "  Product.price "
                 "FROM "
                 "  TransactionProduct "
                 "  INNER JOIN Product ON TransactionProduct.product_id = Product.id "
                 "WHERE "
                 "   TransactionProduct.transaction_id = %(transaction_id)s ")
        cursor.execute(query, {'transaction_id': transaction_id})
        rows = cursor.fetchall()
    sql_connection.close()
    return rows


@app.post("/_api/transaction/product/")
def add_product_transaction(item: Irequest_product_transaction):
    query_transaction_product = ("INSERT INTO `TransactionProduct` (`transaction_id`,`product_id`,`quantity`) "
                                 "VALUES (%(transaction_id)s,%(product_id)s,%(quantity)s)")

    sql_connection = pymysql.connect(host=os.getenv('MYSQL_MASTER_HOST'),
                                     port=int(os.getenv('MYSQL_MASTER_PORT')),
                                     user=os.getenv('MYSQL_MASTER_USER'),
                                     passwd=os.getenv('MYSQL_MASTER_PASS'),
                                     db=os.getenv('MYSQL_MASTER_DB'))

    with sql_connection.cursor() as cursor:

        for product in item.product_list:
            cursor.execute(query_transaction_product, {
                'transaction_id': item.transaction_id,
                'product_id': product.barcode,
                'quantity': product.quantity
            })
        sql_connection.commit()
    sql_connection.close()


@app.post("/_api/transaction/faceimage/")
def add_transaction_faceimage(item: Irequest_transaction_faceimage):
    query_transaction_product = ("INSERT INTO `TransactionFaceImage` (`transaction_id`,`face_image_id`) "
                                 "VALUES (%(transaction_id)s,%(face_image_id)s)")

    sql_connection = pymysql.connect(host=os.getenv('MYSQL_MASTER_HOST'),
                                     port=int(os.getenv('MYSQL_MASTER_PORT')),
                                     user=os.getenv('MYSQL_MASTER_USER'),
                                     passwd=os.getenv('MYSQL_MASTER_PASS'),
                                     db=os.getenv('MYSQL_MASTER_DB'))

    with sql_connection.cursor() as cursor:

        cursor.execute(query_transaction_product, {
            'transaction_id': item.transaction_id,
            'face_image_id': item.face_image_id,
        })

        sql_connection.commit()
    sql_connection.close()


@app.get("/_api/transaction/{transaction_id}", response_model=Iresponse_get_transaction)
def get_transaction(transaction_id: int):
    logger.info("Transaction ID: {}".format(transaction_id))
    transaction_result = query_transaction(transaction_id)

    # If transaction is not found, return 404
    if not transaction_result:
        raise HTTPException(status_code=404, detail="Transaction not found")

    product_results = query_transaction_product(transaction_id)
    transaction_result['products'] = product_results
    return transaction_result

# For check with probe in openshift
@app.get('/healthz')
def health_check():
    return

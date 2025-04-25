from fastapi import FastAPI, HTTPException
from postgres_interaction import crt_engine, test_connection, is_postgres_table_exists, get_first_handle_trn, upd_rows_by_condition, run_query, insert_custom_transaction
import os
from pydantic import BaseModel
from typing import Dict
import logging
from dotenv import load_dotenv
load_dotenv()


logging.basicConfig(
    level=logging.INFO,  # Рівень логів (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(levelname)s : %(asctime)s : %(name)s : %(funcName)s : %(message)s",  # Формат повідомлень
    datefmt="%Y-%m-%d %H:%M:%S",  # Формат дати
)


pg_conn_data = {
    'PG_USER': os.getenv('POSTGRES_USER'),
    'PG_PASS': os.getenv('POSTGRES_PASSWORD'),
    'PG_HOST': os.getenv('POSTGRES_HOST'),
    'PG_PORT': os.getenv('POSTGRES_PORT'),
    'PG_DB': os.getenv('POSTGRES_DATABASE')
}


SCHEMA = os.getenv('SCHEMA')
STG_TABLE = os.getenv('STG_TABLE')


app = FastAPI()

@app.get("/get_last_trn")
def get_last_trn():
    """
        EP return 1st transaction 
            WHERE handle_marker = 'true'
            ORDER BY tinestamp ASC
    """
    try:
        engine = crt_engine(pg_conn_data)

        if not test_connection(engine):
            logging.error("Database connection failed")
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        if not is_postgres_table_exists(engine, STG_TABLE, SCHEMA):
            logging.error(f"Table {SCHEMA}.{STG_TABLE} not found")
            raise HTTPException(status_code=404, detail=f"Table {SCHEMA}.{STG_TABLE} not found")

        query = f"""
            SELECT
                trn_id
                , TO_CHAR(ts, 'YYYY-MM-DD HH24:MI') AS dt
                , amount
                , bank_description
                , mcc_group_description
                , mcc_short_description
            FROM {SCHEMA}.{STG_TABLE}
            WHERE handle_marker = 'true'
            ORDER BY trn_unix
            LIMIT 1
        """
        resp = run_query(engine, query)
        resp_dict = dict(resp.mappings().first()) if resp.rowcount > 0 else {}
        logging.info(f'/get_last_trn API resp: {resp_dict}')
        return resp_dict
    except Exception as e:
        logging.error(f'/get_last_trn API error: {e}')


@app.get("/get_categories")
def get_categories():
    """ Return all categories in order of popularity """
    
    query = f"""
        SELECT category
        FROM mono_data.stg_transactions
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY COUNT(*) DESC
    """

    pg_engine = crt_engine(pg_conn_data)

    if test_connection(pg_engine) \
        and is_postgres_table_exists(pg_engine, STG_TABLE, SCHEMA):

        res = run_query(pg_engine, query)
        result_list = [dict(row)['category'] for row in res.mappings()]
        return result_list
    else:
        return None


@app.get("/get_sub_categories/{category}")
def get_sub_categories(category: str):
    """ Return all sub-categities for category in order of popularity """

    query = f"""
        SELECT sub_category
        FROM mono_data.stg_transactions
        WHERE category = '{category}'
            AND sub_category IS NOT NULL
        GROUP BY sub_category
        ORDER BY COUNT(*) DESC
    """

    pg_engine = crt_engine(pg_conn_data)

    if test_connection(pg_engine) \
        and is_postgres_table_exists(pg_engine, STG_TABLE, SCHEMA):

        res = run_query(pg_engine, query)
        result_list = [dict(row)['sub_category'] for row in res.mappings()]
        if len(result_list) == 0:
            result_list.append(category)

        return result_list
    else:
        return None



class Item(BaseModel):
    set_dict: Dict[str, str]

@app.put("/update_trn/{trn_id}")
def update_trn(trn_id: str, item: Item):
    """ Upd new data into trn by trn_id """
    condition_dict = {
        'trn_id': trn_id
    }

    item = item.dict()
    pg_engine = crt_engine(pg_conn_data)

    if test_connection(pg_engine) \
        and is_postgres_table_exists(pg_engine, STG_TABLE, SCHEMA):
        resp = upd_rows_by_condition(pg_engine, STG_TABLE, SCHEMA, item['set_dict'], condition_dict)
    else:
        resp = None
    
    return resp


@app.put("/insert_custom_trn")
def insert_custom_trn(item: Item):
    """ Inserting trn with data in PG tbl """
    try:
        logging.info('*'*100)

        engine = crt_engine(pg_conn_data)

        if not test_connection(engine):
            logging.error("Database connection failed")
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        if not is_postgres_table_exists(engine, STG_TABLE, SCHEMA):
            logging.error(f"Table {SCHEMA}.{STG_TABLE} not found")
            raise HTTPException(status_code=404, detail=f"Table {SCHEMA}.{STG_TABLE} not found")

        item = item.dict()
        logging.info(f'item_dict: {item}')

        insert_custom_transaction(engine, STG_TABLE, SCHEMA, item['set_dict'])
        return 'RESPONSE'

    except Exception as e:
        logging.error(f'/insert_custom_trn ERROR: {e}')
        
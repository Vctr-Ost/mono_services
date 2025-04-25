import requests
import json
import time

import asyncio
import aiohttp
import logging

logger = logging.getLogger(__name__)


async def query_get_json_async(URI):
    logging.info(f'GET request to {URI}')
    async with aiohttp.ClientSession() as session:
        async with session.get(URI) as response:
            logging.info(f'GET response status code: {response.status}')
            if response.status == 200:
                resp_text = await response.text()
                logging.info(f'Response text: {resp_text}')
                resp_dict = json.loads(resp_text)
                logging.info(f'Response dict: {resp_dict}')
                return resp_dict   
            else:
                return None     
    

async def query_put(URI, data):
    logging.info(f'PUT request to {URI}')
    async with aiohttp.ClientSession() as session:
        async with session.put(URI, json=data) as response:
            logging.info(f'PUT response status code: {response.status}')
            if response.status == 200:
                return True   
            else:
                return False


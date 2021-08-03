import asyncio
import csv
import math
import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()

FIELDS = [
    "ИМТ",
    "ИМТ Поставщика",
    "Объект",
    "Предмет",
    "Страна производства",
    "Артикул Поставщика",
    "Артикул WB",
    "Код поставщика",
    "Код размера(chrt_id)",
    "Штрихкод",
    "Ошибки",
]
URL = "https://suppliers-api.wildberries.ru/card/list"
LIMIT = 50
TOKEN = os.getenv("TOKEN")
SUPPLIER_ID = os.getenv("SUPPLIER_ID")


def _make_payload(offset: int) -> dict:
    return {
        "id": "1",
        "jsonrpc": "2.0",
        "params": {
            "filter": {"order": {"column": "createdAt", "order": "asc"}},
            "query": {"limit": LIMIT, "offset": offset},
            "supplierID": SUPPLIER_ID,
        },
    }


def _get_headers():
    return {"Content-Type": "application/json", "Authorization": TOKEN}


async def get_skus(session, offset: int):
    async with session.post(URL, headers=_get_headers(), json=_make_payload(offset)) as resp:
        print(f"Request with offset {offset}")
        ret = await resp.json()
        save_skus(ret)
        return ret


# Save results into CSV file
def save_skus(data):
    with open("skus.csv", "a") as f:
        writer = csv.writer(f)
        for sku in data["result"]["cards"]:
            writer.writerow(
                (
                    sku["imtId"],
                    sku["imtSupplierId"],
                    sku["object"],
                    sku["parent"],
                    sku["countryProduction"],
                    sku["supplierVendorCode"],
                    sku["nomenclatures"][0]["nmId"],
                    sku["nomenclatures"][0]["vendorCode"],
                    sku["nomenclatures"][0]["variations"][0]["chrtId"],
                    sku["nomenclatures"][0]["variations"][0]["barcodes"][0],
                    str(sku["nomenclatures"][0]["variations"][0].get("errors")),
                )
            )


async def run():
    tasks = []
    with open("skus.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow(*FIELDS)

    async with aiohttp.ClientSession(raise_for_status=True) as session:
        data = await get_skus(session, 0)
        all_skus_count = math.ceil(data["result"]["cursor"]["total"] / LIMIT) * LIMIT + 1

        for offset in range(LIMIT, all_skus_count, LIMIT):
            task = asyncio.create_task(get_skus(session, offset))
            tasks.append(task)
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(run())

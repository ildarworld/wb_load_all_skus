import asyncio
import csv
import math
import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()

FIELDS = (
    "Бренд",
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
)
URL = "https://suppliers-api.wildberries.ru/card/list"
LIMIT = 100
TOKEN = os.getenv("TOKEN")
SUPPLIER_ID = os.getenv("SUPPLIER_ID")
WITH_ERRORS = os.getenv("WITH_ERRORS", "False").upper() == "TRUE"

FILENAME = "skus.csv" if not WITH_ERRORS else "skus_with_errors.csv"


def _make_payload(offset: int) -> dict:
    payload = {
        "id": "1",
        "jsonrpc": "2.0",
        "params": {
            "filter": {"order": {"column": "createdAt", "order": "asc"}},
            "query": {"limit": LIMIT, "offset": offset},
            "supplierID": SUPPLIER_ID,
        },
    }
    if WITH_ERRORS:
        payload["params"]["withError"] = True

    return payload


def _get_headers():
    return {"Content-Type": "application/json", "Authorization": TOKEN}


async def get_skus(session, offset: int):
    async with session.post(URL, headers=_get_headers(), json=_make_payload(offset)) as resp:
        print(f"Request with offset {offset}")
        ret = await resp.json()
        save_skus(ret)
        return ret


def get_param(addin: list, name) -> str:
    for add in addin:
        if add["type"] == name:
            return add["params"][0].get("value")


# Save results into CSV file
def save_skus(data):
    with open(FILENAME, "a") as f:
        writer = csv.writer(f)
        for imt in data["result"]["cards"]:
            brand = get_param(imt["addin"], "Бренд")

            for sku in imt["nomenclatures"]:
                for variant in sku["variations"]:
                    writer.writerow(
                        (
                            brand,
                            imt["imtId"],
                            imt["imtSupplierId"],
                            imt["object"],
                            imt["parent"],
                            imt["countryProduction"],
                            imt["supplierVendorCode"],
                            sku["nmId"],
                            sku["vendorCode"],
                            variant["chrtId"],
                            variant.get("barcodes")[0]
                            if variant.get("barcodes")
                            else variant.get("barcode"),
                            str(variant.get("errors")),
                        )
                    )


async def run():
    tasks = []

    with open(FILENAME, "a") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)

    async with aiohttp.ClientSession(raise_for_status=True) as session:
        data = await get_skus(session, 0)
        all_skus_count = math.ceil(data["result"]["cursor"]["total"] / LIMIT) * LIMIT + 1
        for offset in range(LIMIT, all_skus_count, LIMIT):
            task = asyncio.create_task(get_skus(session, offset))
            tasks.append(task)
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(run())

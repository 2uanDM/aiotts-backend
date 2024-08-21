import json
import logging
import os
import tempfile
import traceback
from datetime import datetime
from typing import List

import gspread
import pandas as pd
import polars as pl
from fastapi import APIRouter, Response
from oauth2client.service_account import ServiceAccountCredentials

from app.utils import const, setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)


class GoogleSheetWorker:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(self, workbook_name: str) -> None:
        self.workbook_name = workbook_name

        # Get the path to the secret file
        with tempfile.TemporaryDirectory() as tmpdirname:
            with open(os.path.join(tmpdirname, "sheet_secret_key.json"), "w") as f:
                json.dump(const.SHEET_SECRET_KEY, f, indent=4, ensure_ascii=False)

            # Get the credentials
            self.creds = ServiceAccountCredentials.from_json_keyfile_name(
                filename=os.path.join(tmpdirname, "sheet_secret_key.json"),
                scopes=self.scopes,  # type: ignore
            )
        # Authorize the client
        self.files = gspread.authorize(self.creds)

    def read_sheet_data(self, sheet_name: str) -> list:
        logger.info(f"Reading data from sheet: {sheet_name}")

        try:
            workbook = self.files.open(self.workbook_name)
            sheet = workbook.worksheet(sheet_name)

            if sheet_name.find("PHONGKD") != -1:
                table = sheet.get("A1:J200000")
            else:
                table = sheet.get_all_records()

            # Convert the table to a dataframe (skip the first row)
            data = pd.DataFrame(table[1:], columns=table[0], dtype=str)
            data_pl = pl.from_pandas(data)
            data_pl_rows = data_pl.rows(named=True)

            return {
                "status": "success",
                "data": data_pl_rows,
            }
        except Exception:
            logger.error(
                f"Error when reading data from sheet: {sheet_name}", exc_info=True
            )

            err_str = traceback.format_exc()

            return {
                "status": "error",
                "message": f"Error when reading data from Google Sheet: {err_str}",
            }

    def insert_new_sku(self, name: str, sale_department_id: int, new_sku_data: list):
        try:
            workbook = self.files.open(self.workbook_name)

            # Get the coresponding sheet name
            if sale_department_id == 0:
                sheet_name = "Team Test"
            else:
                sheet_name = f"PHONGKD{sale_department_id}"

            sheet: gspread.Worksheet = workbook.worksheet(sheet_name)

            # Get the last row of the sheet
            last_row = len(sheet.get("A1:H900000")) + 1

            # Create a new dict to store the row to insert for each sku
            row_to_insert = {}
            for index, sku_data in enumerate(new_sku_data):
                row_to_insert[sku_data[0]] = last_row + index

            color_of_row = {}
            light_green = {"red": 0.8, "green": 1, "blue": 0.8}
            light_blue = {"red": 0.8, "green": 0.9, "blue": 1}
            is_light_green = False

            for i, sku_data in enumerate(new_sku_data):
                current_color = light_green if is_light_green else light_blue
                sku_id = sku_data[0]
                color = sku_data[1]
                product_type = sku_data[2]
                seller_sku = sku_data[4]

                color_of_row[sku_id] = current_color

                # Variant has changed then change the color for easier distinguish
                if i < len(new_sku_data) - 1 and (
                    seller_sku != new_sku_data[i + 1][4]
                    or color != new_sku_data[i + 1][1]
                    or product_type != new_sku_data[i + 1][2]
                ):
                    is_light_green = not is_light_green

            sheet.batch_format(
                [
                    {
                        "range": f"A{row_to_insert[sku_id]}:H{row_to_insert[sku_id]}",
                        "format": {"backgroundColor": color},
                    }
                    for sku_id, color in color_of_row.items()
                ]
            )

            data_to_insert = []

            for sku, row in row_to_insert.items():
                # Search for sku data
                current_data = None
                for sku_data in new_sku_data:
                    if sku_data[0] == sku:
                        current_data = sku_data
                        break

                if current_data is None:
                    continue

                color = current_data[1]
                product_type = current_data[2]
                size = current_data[3]
                seller_sku = current_data[4]
                product_name = current_data[5]

                time_now = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
                data_to_insert.append(
                    {
                        "range": f"A{row}:L{row}",
                        "values": [
                            [
                                sku,
                                product_name,
                                f"Seller SKU: {seller_sku} | Color {color} | Product type {product_type} | Size {size}",
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                time_now,
                                name,
                            ]
                        ],
                    }
                )

            sheet.batch_update(data_to_insert)
        except Exception:
            logger.error(
                f"Error when inserting new SKU to sheet: {sheet_name}", exc_info=True
            )
            return {
                "status": "error",
            }
        else:
            return {
                "status": "success",
            }


router = APIRouter()


@router.get("/design/read")
def read_google_sheet(workbook_name: str, sheet_name: str):
    sheet_worker = GoogleSheetWorker(workbook_name)

    result = sheet_worker.read_sheet_data(sheet_name)

    if result["status"] == "error":
        return Response(
            content=json.dumps(result, ensure_ascii=False, indent=4),
            status_code=400,
        )

    return Response(
        content=json.dumps(result, ensure_ascii=False, indent=4),
        status_code=200,
        media_type="application/json",
    )


@router.post("/design/sku/search")
def search_design_by_sku_id(body: List[str], workbook_name: str, sheet_name: str):
    sheet_worker = GoogleSheetWorker(workbook_name)

    result = sheet_worker.read_sheet_data(sheet_name)

    if result["status"] == "error":
        return Response(
            content=json.dumps(result, ensure_ascii=False, indent=4),
            status_code=400,
        )

    # Create a mapping from SKU to row data
    mapping = {}
    for row in result["data"]:
        if row["SKU"]:
            if row["SKU"].strip != "":
                mapping[row["SKU"]] = row

    # Remove duplicates
    sku_ids: list = body
    sku_ids = list(set(sku_ids))

    result_data = {}

    for sku_id in sku_ids:
        if sku_id in mapping:
            result_data[sku_id] = mapping[sku_id]
        else:
            result_data[sku_id] = None

    return Response(
        content=json.dumps(result_data, ensure_ascii=False, indent=4),
        status_code=200,
        media_type="application/json",
    )

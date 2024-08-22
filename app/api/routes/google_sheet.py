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
from dotenv import load_dotenv
from fastapi import APIRouter, Response
from oauth2client.service_account import ServiceAccountCredentials

from app.api.schema.google_sheet import SKUSToInsert
from app.utils import setup_logger, validate_apikey

load_dotenv(override=True)

logger = logging.getLogger(__name__)
setup_logger(logger)


class GoogleSheetWorker:
    """
    A class that provides methods to interact with Google Sheets.

    Attributes:
        scopes (list): A list of Google API scopes required for accessing Google Sheets and Drive.
        workbook_name (str): The name of the Google Sheets workbook.

    Methods:
        __init__(self, workbook_name: str) -> None: Initializes a new instance of the GoogleSheetWorker class.
        read_sheet_data(self, sheet_name: str) -> dict: Reads data from a specific sheet in the workbook.
        insert_new_sku(self, seller_name: str, sheet_name: str, new_sku_data: list) -> dict: Inserts new SKU data into a specific sheet.
        delete_rows(self, sheet_name: str, sku_ids: List[str]): Deletes rows from a specific sheet based on SKU IDs.
    """

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(self, workbook_name: str) -> None:
        """
        Initializes a new instance of the GoogleSheetWorker class.

        Args:
            workbook_name (str): The name of the Google Sheets workbook.
        """
        self.workbook_name = workbook_name

        # Get the path to the secret file
        with tempfile.TemporaryDirectory() as tmpdirname:
            with open(os.path.join(tmpdirname, "sheet_secret_key.json"), "w") as f:
                json.dump(
                    json.loads(os.getenv("SHEET_SECRET_KEY")),
                    f,
                    indent=4,
                    ensure_ascii=False,
                )

            # Get the credentials
            self.creds = ServiceAccountCredentials.from_json_keyfile_name(
                filename=os.path.join(tmpdirname, "sheet_secret_key.json"),
                scopes=self.scopes,  # type: ignore
            )
        # Authorize the client
        self.files = gspread.authorize(self.creds)

    def read_sheet_data(self, sheet_name: str) -> dict:
        """
        Reads data from a specific sheet in the workbook.

        Args:
            sheet_name (str): The name of the sheet to read data from.

        Returns:
            dict: A dictionary containing the status of the operation and the retrieved data.
        """
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

    def insert_new_sku(
        self, seller_name: str, sheet_name: str, new_sku_data: list
    ) -> dict:
        """
        Inserts new SKU data into a specific sheet.

        Args:
            seller_name (str): The name of the seller.
            sheet_name (str): The name of the sheet to insert data into.
            new_sku_data (list): A list of dictionaries containing the new SKU data.

        Returns:
            dict: A dictionary containing the status of the operation and the inserted SKU data.
        """
        try:
            workbook = self.files.open(self.workbook_name)

            sheet: gspread.Worksheet = workbook.worksheet(sheet_name)

            # Get the last row of the sheet
            last_row = len(sheet.get("A1:J200000")) + 1

            # Create a new dict to store the position to insert for each sku
            row_to_insert = {}
            for index, sku_data in enumerate(new_sku_data):
                sku_id = sku_data.get("sku_id", "")
                row_to_insert[sku_id] = last_row + index

            color_of_row = {}
            light_green = {"red": 0.8, "green": 1, "blue": 0.8}
            light_blue = {"red": 0.8, "green": 0.9, "blue": 1}
            is_light_green = False

            for i, sku_data in enumerate(new_sku_data):
                sku_id = sku_data.get("sku_id", "")
                color = sku_data.get("color", "")
                product_type = sku_data.get("product_type", "")
                seller_sku = sku_data.get("seller_sku", "")

                current_color = light_green if is_light_green else light_blue

                color_of_row[sku_id] = current_color

                # Variant has changed then change the color for easier distinguish
                if i < len(new_sku_data) - 1 and (
                    seller_sku != new_sku_data[i + 1].get("seller_sku", "")
                    or color != new_sku_data[i + 1].get("color", "")
                    or product_type != new_sku_data[i + 1].get("product_type", "")
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
                    if sku_data.get("sku_id", "") == sku:
                        current_data = sku_data
                        break

                if current_data is None:
                    continue

                color = current_data.get("color", "")
                product_type = current_data.get("product_type", "")
                size = current_data.get("size", "")
                seller_sku = current_data.get("seller_sku", "")
                product_name = current_data.get("product_name", "")

                image_1_front = current_data.get("image_1_front")
                image_2_back = current_data.get("image_2_back")
                mockup_front = current_data.get("mockup_front")
                mockup_back = current_data.get("mockup_back")
                mockup_onos = current_data.get("mockup_onos")
                image_front_beefun = current_data.get("image_front_beefun")
                image_back_beefun = current_data.get("image_back_beefun")

                time_now = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
                data_to_insert.append(
                    {
                        "range": f"A{row}:L{row}",
                        "values": [
                            [
                                sku,
                                product_name,
                                f"{seller_sku}; {color}; {product_type}; {size}",
                                image_1_front,  # Image 1 (front)
                                image_2_back,  # Image 2 (back)
                                mockup_front,  # Mockup Front
                                mockup_back,  # Mockup Back
                                mockup_onos,  # Mockup (For Onos)
                                image_front_beefun,  # Image front (Beefun)
                                image_back_beefun,  # Image back (Beefun)
                                time_now,  # Created at
                                seller_name,  # User
                            ]
                        ],
                    }
                )
            sheet.batch_update(data_to_insert)
        except Exception:
            logger.error(
                f"Error when inserting new SKU to sheet: {sheet_name}", exc_info=True
            )

            error_message = traceback.format_exc()
            return {
                "status": "error",
                "message": f"Error when inserting new SKU to sheet: {error_message}",
            }
        else:
            return {
                "status": "success",
                "message": "Insert new SKU to sheet successfully",
                "data": [x["values"][0][0] for x in data_to_insert],
            }

    def delete_rows(self, sheet_name: str, sku_ids: List[str]):
        """
        Deletes rows from a specific sheet based on SKU IDs.

        Args:
            sheet_name (str): The name of the sheet to delete rows from.
            sku_ids (List[str]): A list of SKU IDs to delete.

        Returns:
            dict: A dictionary containing the status of the operation and the deleted rows information.
        """
        try:
            # Read the sheet
            workbook = self.files.open(self.workbook_name)
            sheet = workbook.worksheet(sheet_name)

            logger.info(f"Reading data from sheet: {sheet_name}")

            if sheet_name.find("PHONGKD") != -1:
                table = sheet.get("A1:J200000")
            else:
                table = sheet.get_all_records()

            data = pd.DataFrame(table[1:], columns=table[0], dtype=str)
            data_pl = pl.from_pandas(data)
            data_pl_rows = data_pl.rows(named=True)

            # Get the dict that mapping from SKU ID to row index
            sku_infos = {}

            # Remove duplicates
            sku_ids = list(set(sku_ids))

            for sku_id in sku_ids:
                for idx, row in enumerate(data_pl_rows):
                    if row["SKU"] == sku_id:
                        print(f"Found SKU ID at index {idx + 3}")
                        sku_infos[sku_id] = {
                            "index": idx
                            + 3,  # Skip 2 rows, and google sheet index starts from 1
                            "data": row,
                        }
                        break

            logger.info(f"Deleting rows with SKU IDs: {sku_ids}")

            if len(sku_infos) == 0:
                return {
                    "status": "success",
                    "message": "No matched SKU ID to delete",
                }

            # Sort the rows to delete from the last row to the first row
            sku_infos = dict(
                sorted(sku_infos.items(), key=lambda x: x[1]["index"], reverse=True)
            )

            # Delete the rows
            for sku_id, row_info in sku_infos.items():
                sheet.delete_row(row_info["index"])  # Since we skip 2 rows
                print(f"Deleted row at index {row_info['index']} with SKU ID: {sku_id}")

            return {
                "status": "success",
                "message": "Delete rows successfully",
                "deleted_rows": sku_infos,
            }

        except Exception:
            logger.error("Error when deleting", exc_info=True)

            error_str = traceback.format_exc()
            return {
                "status": "error",
                "message": f"Error when deleting row: {error_str}",
            }


router = APIRouter()


@router.get("/design/read")
def read_google_sheet(workbook_name: str, sheet_name: str, api_key: str = ""):
    validate_apikey(api_key)

    sheet_worker = GoogleSheetWorker(workbook_name)

    result = sheet_worker.read_sheet_data(sheet_name)

    if result["status"] == "error":
        return Response(
            content=json.dumps(result, ensure_ascii=False, indent=4),
            status_code=400,
            media_type="application/json",
        )

    return Response(
        content=json.dumps(result, ensure_ascii=False, indent=4),
        status_code=200,
        media_type="application/json",
    )


@router.post("/design/sku/search")
def search_design_by_sku_id(
    body: List[str], workbook_name: str, sheet_name: str, api_key: str = ""
):
    validate_apikey(api_key)

    sheet_worker = GoogleSheetWorker(workbook_name)

    result = sheet_worker.read_sheet_data(sheet_name)

    if result["status"] == "error":
        return Response(
            content=json.dumps(result, ensure_ascii=False, indent=4),
            status_code=400,
            media_type="application/json",
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


@router.post("/design/sku/insert")
def insert_new_sku_ids(
    body: List[SKUSToInsert],
    workbook_name: str,
    sheet_name: str,
    seller_name: str,
    api_key: str = "",
):
    validate_apikey(api_key)

    sheet_worker = GoogleSheetWorker(workbook_name)

    # Validate when model dump to json
    new_sku_data = []
    error_sku_data = []

    for item in body:
        sku_id = item.sku_id
        try:
            item_json = item.model_dump()
        except Exception:
            logger.error("Error when dumping model to json", exc_info=True)
            error_sku_data.append(sku_id)
        else:
            new_sku_data.append(item_json)

    result = sheet_worker.insert_new_sku(
        seller_name=seller_name,
        sheet_name=sheet_name,
        new_sku_data=new_sku_data,
    )

    if result["status"] == "error":
        return Response(
            content=json.dumps(result, ensure_ascii=False, indent=4),
            status_code=400,
            media_type="application/json",
        )

    if len(error_sku_data) > 0:
        result["error_sku_data"] = error_sku_data

    return Response(
        content=json.dumps(result, ensure_ascii=False, indent=4),
        status_code=200,
        media_type="application/json",
    )


@router.post("/design/sku/move-down")
def move_designs_to_last_row(
    body: List[str], workbook_name: str, sheet_name: str, api_key: str = ""
):
    validate_apikey(api_key)

    sheet_worker = GoogleSheetWorker(workbook_name)

    logger.info(f"Start deleting rows: {body}")

    result = sheet_worker.delete_rows(sheet_name, body)
    # print(f"==>> result: {result}")

    if result["status"] == "error":
        return Response(
            content=json.dumps(result, ensure_ascii=False, indent=4),
            status_code=400,
            media_type="application/json",
        )
    else:
        if not result.get("deleted_rows"):
            return Response(
                content=json.dumps(result, ensure_ascii=False, indent=4),
                status_code=200,
                media_type="application/json",
            )
        else:
            # Insert new sku to the last row:
            new_sku_data = []

            logger.info(f"Start inserting rows: {list(result['deleted_rows'].keys())}")

            seller_name = list(result["deleted_rows"].values())[0]["data"]["User"]
            print(f"==>> seller_name: {seller_name}")

            for sku_id, row_info in result["deleted_rows"].items():
                new_sku_data.append(
                    {
                        "sku_id": sku_id,
                        "color": "",
                        "product_name": row_info["data"]["Product Name"],
                        "product_type": "",
                        "size": "",
                        "seller_sku": row_info["data"]["Variation"],
                        "image_1_front": row_info["data"]["Image 1 (front)"],
                        "image_2_back": row_info["data"]["Image 2 (back)"],
                        "mockup_front": row_info["data"]["Mockup Front"],
                        "mockup_back": row_info["data"]["Mockup Back"],
                        "mockup_onos": row_info["data"]["Mockup (For Onos)"],
                        "image_front_beefun": row_info["data"]["Image front (Beefun)"],
                        "image_back_beefun": row_info["data"]["Image back (Beefun)"],
                    }
                )

            # Call insert new sku
            result_insert = sheet_worker.insert_new_sku(
                seller_name=seller_name,
                sheet_name=sheet_name,
                new_sku_data=new_sku_data,
            )

            if result_insert["status"] == "error":
                return Response(
                    content=json.dumps(result_insert, ensure_ascii=False, indent=4),
                    status_code=400,
                    media_type="application/json",
                )

            # Update the message
            result_insert["message"] = "Move designs to the last row successfully"

            return Response(
                content=json.dumps(result_insert, ensure_ascii=False, indent=4),
                status_code=200,
                media_type="application/json",
            )

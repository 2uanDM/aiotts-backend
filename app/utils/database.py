import logging
import os
import sys
import time
from functools import wraps


import psycopg2
from dotenv import load_dotenv

from app.utils.logger import setup_logging

load_dotenv(override=True)
logger = logging.getLogger("src.database")
setup_logging(logger, level=logging.INFO)


class Postgres(object):
    def __init__(self):
        print("==>> Connecting to Postgres...")

    def connect(self):
        if os.path.exists("./host"):
            with open("./host", "r") as f:
                host = f.read().strip()
        else:
            host = os.getenv("DB_HOST")

        # If there is a file host in the root directory, use it to be the host (for backup the database)
        self.conn = psycopg2.connect(
            host=host,
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            connect_timeout=5,
        )

        logger.info(f"Connected to Postgres with host: {host}")

    def get_connection(self):
        max_retries = 10

        while max_retries > 0:
            try:
                self.connect()
                break
            except Exception:
                logger.warning("Kết nối tới database thất bại. Thử lại sau 1 giây")
                max_retries -= 1
                time.sleep(1)
                continue

        if max_retries == 0:
            raise Exception(
                "Kết nối tới database thất bại. Hãy thử tắt tường lửa hoặc kiểm tra lại kết nối internet của bạn"
            )

        return self.conn


def server_connection(func):
    @wraps(func)  # Preserve the metadata of the original function
    def wrapper(*args, **kwargs):
        try:
            conn = Postgres().get_connection()
            return func(*args, **kwargs, conn=conn)
        except Exception as e:
            logger.error("Error occurred when server connection", exc_info=True)
            raise e  # Re-raise the exception
        finally:
            if conn is not None:
                conn.close()

    return wrapper

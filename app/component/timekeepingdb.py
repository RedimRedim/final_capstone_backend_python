import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
import pandas as pd
import pandasql as psql
from utils.db_connection import MongoDbConnection

dotenv_path = os.path.join(os.path.dirname(__file__), "../config/.env")
load_dotenv(dotenv_path)


class TimekeepingDb:
    def __init__(self, mongoDbConnectionInstance: MongoDbConnection):
        self.client = None
        self.collection = None
        self.mongoDbInstance = mongoDbConnectionInstance
        self.dateInfo = None

    def cutoff_date(self, year, month):
        self.dateInfo = {
            "year": int(year),
            "month": int(month),
            "date": pd.to_datetime(f"{year}-{month}-01"),
        }

    def write_db(self, jsonData):
        self.collection = self.mongoDbInstance.get_collection(
            os.getenv("COLLECTION_TIMEKEEPING_NAME")
        )

        print(jsonData)

        # clear all timekeeping 1st
        self.collection.delete_many(
            {"year": self.dateInfo["year"], "month": self.dateInfo["month"]}
        )
        print("Deleted timekeeping data")
        # insert
        self.collection.insert_many(jsonData)
        print("Timekeeping data has been added")

    def get_timekeeping_data(self):
        self.collection = self.mongoDbInstance.get_collection(
            os.getenv("COLLECTION_TIMEKEEPING_NAME")
        )
        timekeepingData = list(
            self.collection.find(
                {"year": self.dateInfo["year"], "month": self.dateInfo["month"]},
                {"_id": False},
            )
        )
        timekeepingDf = pd.DataFrame(timekeepingData)
        # Replace NaN with None for JSON serialization timekeepingDf = timekeepingDf.where(pd.notnull(timekeepingDf), None
        timekeepingDf = timekeepingDf.where(pd.notnull(timekeepingDf), None)

        query = """SELECT uuid, month,year,COUNT(case when status like "%RD%" then 1 end) as restDay, sum(finishedwork) as finishedWork, sum(late) as late , sum(absent) as absent
        FROM timekeepingDf GROUP BY uuid,month,year"""

        timekeepingDf = psql.sqldf(query, locals())

        return timekeepingDf


# if __name__ == "__main__":
#     timekeepingDb = TimekeepingDb()
#     timekeepingData = timekeepingDb.get_timekeeping_data()
#     print(timekeepingData)

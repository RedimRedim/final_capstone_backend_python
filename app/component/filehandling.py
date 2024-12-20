import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
import pandas as pd
import pandasql as psql
import json
from component.employees import Employees
from component.timekeepingdb import TimekeepingDb
from calendar import monthrange


dotenv_path = os.path.join(os.path.dirname(__file__), "../config/.env")
load_dotenv(dotenv_path)


class FileHandling:
    def __init__(
        self, employeesInstance: Employees, timekeepingDbInstance: TimekeepingDb
    ):
        self.filePath = None
        self.timekeepingDf = None
        self.restDf = None
        self.employees = employeesInstance
        self.timekeepingDbInstance = timekeepingDbInstance

    def init_file(self, file):
        self.filePath = file
        self._read_file()
        self._query_file()  # its joining with employee collection
        self._calculate_file()

        jsonData = self._convert_to_json()

        return jsonData

    def _read_file(self):
        self.timekeepingDf = self._timekeeping_with_absent_data()
        self.restDf = pd.read_excel(self.filePath, sheet_name="RD").dropna()
        # Drop rows where 'uuid' is None or empty
        self.timekeepingDf = self.timekeepingDf[
            self.timekeepingDf["uuid"].notna() & (self.timekeepingDf["uuid"] != "")
        ]

    def _timekeeping_with_absent_data(self):
        self.timekeepingDf = pd.read_excel(self.filePath).fillna("")
        employeeData = self.employees.get_employees_data()[
            ["uuid", "isResign", "resignDate"]
        ]
        self.timekeepingDf = self.timekeepingDf.merge(
            employeeData, on="uuid", how="left"
        )

        return self.timekeepingDf

    def _formatting_variable(self):
        self.timekeepingDf["workingTime"] = pd.to_datetime(
            self.timekeepingDf["workingTime"], errors="coerce"
        )
        self.timekeepingDf["month"] = self.timekeepingDf["workingTime"].dt.month
        self.timekeepingDf["year"] = self.timekeepingDf["workingTime"].dt.year

        if any(
            self.timekeepingDbInstance.dateInfo["month"] != self.timekeepingDf["month"]
        ) or any(
            self.timekeepingDbInstance.dateInfo["year"] != self.timekeepingDf["year"]
        ):
            raise ValueError(
                "Selected Month & Year with workingTime Data are different"
            )

        self.timekeepingDf["workingTime"] = pd.to_datetime(
            self.timekeepingDf["workingTime"], errors="coerce"
        )
        self.timekeepingDf["timeIn"] = pd.to_datetime(
            self.timekeepingDf["timeIn"], errors="coerce"
        )
        self.timekeepingDf["timeOut"] = pd.to_datetime(
            self.timekeepingDf["timeOut"], errors="coerce"
        )

        self.timekeepingDf["resignDate"] = pd.to_datetime(
            self.timekeepingDf["resignDate"], errors="coerce"
        ).dt.date

    def _calculate_file(self):
        self._formatting_variable()

        self.timekeepingDf["endOfMonthDay"] = self.timekeepingDf.apply(
            lambda row: monthrange(row["year"], row["month"])[1], axis=1
        )
        # Calculate Employee Timekeeping
        self.timekeepingDf["totalWorkHours"] = self.timekeepingDf.apply(
            lambda row: (
                (row["timeOut"] - row["timeIn"]).total_seconds() / 60
                if pd.notnull(row["timeOut"]) & pd.notnull(row["timeIn"])
                else 0
            ),
            axis=1,
        )

        self.timekeepingDf["finishedWork"] = self.timekeepingDf.apply(
            lambda row: (
                0
                if row["isResign"]
                and isinstance(row["resignDate"], pd.Timestamp)
                and row["resignDate"].date()
                >= self.timekeepingDbInstance.dateInfo["date"]
                else 1 if row["totalWorkHours"] > 320 else 0
            ),
            axis=1,
        )

        self.timekeepingDf["totalRestDays"] = self.timekeepingDf.apply(
            lambda row: row["status"].count("RD") if row["status"] else 0,
            axis=1,
        )

        self.timekeepingDf["late"] = self.timekeepingDf.apply(
            lambda row: (
                (row["timeIn"] - row["workingTime"]).total_seconds() / 60
                if pd.notnull(row["timeIn"])
                and pd.notnull(row["timeOut"])
                and row["timeIn"] > row["workingTime"]
                else 0
            ),
            axis=1,
        )

        self.timekeepingDf["absent"] = self.timekeepingDf.apply(
            lambda row: (
                0
                if row["status"] == "RD"
                or (
                    row["isResign"] == 1
                    and row["workingTime"].date() > row["resignDate"]
                )
                else (
                    1
                    if (row["finishedWork"] == 0) or (row["totalWorkHours"] <= 320)
                    else 0
                )
            ),
            axis=1,
        )

        self.timekeepingDf["totalWorkHours"] = self.timekeepingDf[
            "totalWorkHours"
        ].apply(lambda x: (int(x) if pd.notnull(x) and x != "" else 0))

        self.timekeepingDf["late"] = self.timekeepingDf["late"].apply(
            lambda x: (int(x) if pd.notnull(x) and x != "" else 0)
        )

        self.timekeepingDf.to_csv("./data/timekeeping.csv")

    def _query_file(self):
        # merging all employees dates with timeIn timeOut
        restDf = self.restDf
        timekeepingDf = self.timekeepingDf

        query = """
            SELECT timekeepingDf.*,
            restDf.status
            FROM timekeepingDf
            LEFT JOIN restDf
            on DATE(restDf.date) = DATE(timekeepingDf.workingTime) and restDf.uuid = timekeepingDf.uuid
            """

        self.timekeepingDf = psql.sqldf(query, locals())

    # implementing SQL query to join and merging

    def _convert_to_json(self):
        # Format datetime as ISO 8601 strings
        self.timekeepingDf["workingTime"] = self.timekeepingDf[
            "workingTime"
        ].dt.strftime("%Y-%m-%dT%H:%M:%S")
        self.timekeepingDf["timeIn"] = self.timekeepingDf["timeIn"].dt.strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        self.timekeepingDf["timeOut"] = self.timekeepingDf["timeOut"].dt.strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        self.timekeepingDf["resignDate"] = self.timekeepingDf["resignDate"].astype(str)

        data = self.timekeepingDf.to_json(orient="records")

        return json.loads(data)

import sys
import os
import pandas as pd
from datetime import datetime
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.transform_data import calculate_working_rest_days
from utils.db_connection import MongoDbConnection
from component.employees import Employees
from component.timekeepingdb import TimekeepingDb
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), "../config/.env")
load_dotenv(dotenv_path)


class CalculateMonthlySalary:
    def __init__(
        self,
        employeesInstance: Employees,
        timekeepingDbInstance: TimekeepingDb,
        mongoDbConnectionInstance: MongoDbConnection,
    ) -> None:
        self.employees = employeesInstance
        self.timekeepingDbInstance = timekeepingDbInstance
        self.mongoDbInstance = mongoDbConnectionInstance
        self.employeesDf = pd.DataFrame()  # Initialize as empty DataFrame
        self.timekeepingDf = pd.DataFrame()  # Initialize as empty DataFrame

    def transform_data(self):
        self.merging_data()
        self.post_to_db()
        print("Uploading employees.csv")
        self.employeesDf.to_csv("./data/employees.csv")

    def merging_data(self):

        self.employeesDf = self.employees.get_employees_data()
        self.timekeepingDf = self.timekeepingDbInstance.get_timekeeping_data()

        print("employeesDf")
        print(self.employeesDf)
        print("timekeepingDf")
        print(self.timekeepingDf)

        self.employeesDf = self.employeesDf.merge(
            self.timekeepingDf, on="uuid", how="inner"
        )
        print("after processing")
        print(self.employeesDf)

        self.employeesDf = self.employeesDf[
            (
                (self.employeesDf["isResign"] == True)
                & (
                    self.employeesDf["resignDate"]
                    >= self.timekeepingDbInstance.dateInfo["date"]
                )
            )
            | ((self.employeesDf["isResign"] == False))
        ]

        self.employeesDf["requiredWorkDays"] = self.employeesDf.apply(
            lambda row: calculate_working_rest_days(
                self.timekeepingDbInstance.dateInfo["year"],
                self.timekeepingDbInstance.dateInfo["month"],
                row["dayOff"],
                row["resignDate"],
            )[0],
            axis=1,  # workingDays
        )

        self.employeesDf["requiredRestDays"] = self.employeesDf.apply(
            lambda row: calculate_working_rest_days(
                self.timekeepingDbInstance.dateInfo["year"],
                self.timekeepingDbInstance.dateInfo["month"],
                row["dayOff"],
                row["resignDate"],
            )[1],
            axis=1,  # restDays
        )

        self.employeesDf["dailySalary"] = self.employeesDf.apply(
            lambda row: (row["basicSalary"] / 31), axis=1
        ).round(2)

        self.employeesDf["baseSalary"] = self.employeesDf.apply(
            lambda row: (
                row["dailySalary"] * row["resignDate"].day
                if row["isResign"]
                and row["resignDate"] > self.timekeepingDbInstance.dateInfo["date"]
                else row["dailySalary"]
                * (row["finishedWork"] + row["restDay"] + row["absent"])
            ),
            axis=1,
        ).astype(int)

        self.employeesDf["lateDeduction"] = self.employeesDf.apply(
            lambda row: ((row["dailySalary"] / 8 / 60) * row["late"]), axis=1
        ).round(2)

        self.employeesDf["absentDeduction"] = self.employeesDf.apply(
            lambda row: (row["dailySalary"] * row["absent"]), axis=1
        ).round(2)

        self.employeesDf["totalReleasedSalary"] = self.employeesDf.apply(
            lambda row: (
                (row["baseSalary"] if pd.notnull(row["baseSalary"]) else 0)
                - (row["lateDeduction"] if pd.notnull(row["lateDeduction"]) else 0)
                - (row["absentDeduction"] if pd.notnull(row["absentDeduction"]) else 0)
            ),
            axis=1,
        ).astype(int)

        self.employeesDf = self.employeesDf.fillna("")

    def post_to_db(self):
        self.collection = self.mongoDbInstance.get_collection(
            os.getenv("COLLECTION_SALARY_NAME")
        )

        print(
            f'Deleting salary data, Year: {self.timekeepingDbInstance.dateInfo["year"]} Month: {self.timekeepingDbInstance.dateInfo["month"]} '
        )

        self.collection.delete_many(
            {
                "year": self.timekeepingDbInstance.dateInfo["year"],
                "month": self.timekeepingDbInstance.dateInfo["month"],
            }
        )

        self.collection.insert_many(self.employeesDf.to_dict("records"))
        print("Salary has been uploaded to MongoDB")

    def get_salary_data(self):
        self.collection = self.mongoDbInstance.get_collection(
            os.getenv("COLLECTION_SALARY_NAME")
        )
        salaryData = list(self.collection.find({}, {"_id": False}))
        return salaryData

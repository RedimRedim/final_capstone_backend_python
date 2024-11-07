from component.employees import Employees
from component.filehandling import FileHandling
from component.calculate_salary import CalculateMonthlySalary
from component.timekeepingdb import TimekeepingDb
from utils.db_connection import MongoDbConnection

mongoDbConnectionInstance = MongoDbConnection()
print("MongoDbConnection instance created:", mongoDbConnectionInstance)

employeesInstance = Employees(mongoDbConnectionInstance)
print("Employees instance created with MongoDbConnection:", employeesInstance)

timekeepingDbInstance = TimekeepingDb(mongoDbConnectionInstance)

fileHandlingInstance = FileHandling(employeesInstance, timekeepingDbInstance)

calculateMonthlySalaryInstance = CalculateMonthlySalary(
    employeesInstance, timekeepingDbInstance, mongoDbConnectionInstance
)

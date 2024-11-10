from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import logging
import io
import traceback
from datetime import datetime
from component.instance_setup import (
    calculateMonthlySalaryInstance,
    fileHandlingInstance,
    timekeepingDbInstance,
)

logging.basicConfig(level=logging.INFO)
app = FastAPI()


def main(year, month, file):
    try:
        timekeepingDbInstance.cutoff_date(year, month)  # setup cutoff_date
        jsonData = fileHandlingInstance.init_file(file)  # generate timekeeping
        timekeepingDbInstance.write_db(jsonData)
        calculateMonthlySalaryInstance.transform_data()
        salaryJsonData = calculateMonthlySalaryInstance.get_salary_data()

        return salaryJsonData
    except:
        logging.error(traceback.format_exc())
        raise


@app.post("/upload")
async def upload_timekeeping(
    file: UploadFile = File(...),
    timekeepingYear: str = Form(...),  # Request Param
    timekeepingMonth: str = Form(...),  # Request Param
):

    if not timekeepingYear or not timekeepingMonth:
        raise HTTPException(status_code=404, detail="Year and month are required")

    if file.filename == "":
        raise HTTPException(status_code=400, detail="No file selected")

    try:
        file_content = await file.read()
        # Create a BytesIO object to mimic a file object for pandas
        file_stream = io.BytesIO(file_content)

        salaryJsonData = main(timekeepingYear, timekeepingMonth, file_stream)
        # run timekeeping and calculate monthly salary to push into "salary" collection
        return {"calculateTime": datetime.now(), "data": salaryJsonData}
    except Exception as e:
        logging.error("Error processing file:")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

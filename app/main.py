from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import logging
import os
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

origins = [
    "https://final-capstone-frontend-khaki.vercel.app",  # Allow your specific frontend URL
    "http://localhost:3000",  # Local development URL (change to match your local URL and port)
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


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


@app.get("/")
def testing():
    return {"message": "API is working"}


@app.get("/download-sample-file")
async def download_sample_file():
    file_path = "static/sample.xlsx"
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="sample.xlsx",
    )


@app.get("/timekeeping/download")
async def download_timekeeping():
    file_path = "data/timekeeping.csv"

    if not os.path.exists(file_path):
        return HTTPException(status_code=404, detail="timekeeping file not found")

    return FileResponse(file_path, media_type="text/csv", filename="timekeeping.csv")


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


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=8000)

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import json
import logging
import traceback
from datetime import datetime
from component.instance_setup import (
    calculateMonthlySalaryInstance,
    fileHandlingInstance,
    timekeepingDbInstance,
)

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app)  # enable cors


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


@app.route("/upload", methods=["POST"])
def upload_timekeeping():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    year = request.form.get("timekeepingYear")
    month = request.form.get("timekeepingMonth")

    if not year or not month:
        return jsonify({"error": "Year and month are required"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        salaryJsonData = main(year, month, file)
        # run timekeeping and calculate monthly salary to push into "salary" collection
        return jsonify({"calculateTime": datetime.now(), "data": salaryJsonData}), 200
    except Exception as e:
        logging.error("Error processing file:")
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# running timekeeping data
if __name__ == "__main__":
    app.run(host=0.0.0.0,port=8000)

import calendar
from datetime import datetime, timedelta
import pandas as pd
from datetime import date


def calculate_working_rest_days(year, month, offDaysInput, resignDate=None):
    days_map = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6,
    }

    try:
        off_days_list = [days_map[day.strip()] for day in offDaysInput.split("&")]
    except:
        off_days_list = []  # condition when not day off then mark as 31days

    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])

    # change lastDay logic if got resignDate > monthly last_Day
    if (
        resignDate
        and isinstance(resignDate, pd.Timestamp)
        and resignDate.date() != date(1970, 1, 1)
        and last_day >= resignDate
    ):
        print(resignDate)
        last_day = resignDate

    working_days = 0
    rest_days = 0
    current_day = first_day

    for day in range(first_day.day, last_day.day + 1):
        # cond when doesnt have off_day
        if not off_days_list:
            working_days = last_day.day
            break

        current_day = datetime(year, month, day)
        if current_day.weekday() not in off_days_list:
            working_days += 1
        else:
            rest_days += 1

    return working_days, rest_days

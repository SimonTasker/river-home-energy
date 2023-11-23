import calendar
import math

def get_ordinal_date(x):
    return {'ordinal_date': x.toordinal()}

def get_month(x):
    return {
        calendar.month_name[month]: month == x.month
        for month in range(1, 13)
    }

def get_month_distances(x):
    return {
        calendar.month_name[month]: math.exp(-(x.month - month) ** 2)
        for month in range(1, 13)
    }

def get_day(x):
    return {
        calendar.day_name[day]: day == x.weekday()
        for day in range(0, 7)
    }

def get_hour_distances(x):
    return {
        'Morning': x.hour >=5 and x.hour <= 12,
        'Afternoon': x.hour >= 12 and x.hour <= 17,
        'Evening': x.hour >= 17 and x.hour <= 21,
        'Night' : x.hour >= 21 or x.hour <=5
    }

def get_hour(x):
    return {
        '00': x.hour == 0,
        '01': x.hour == 1,
        '02': x.hour == 2,
        '03': x.hour == 3,
        '04': x.hour == 4,
        '05': x.hour == 5,
        '06': x.hour == 6,
        '07': x.hour == 7,
        '08': x.hour == 8,
        '09': x.hour == 9,
        '10': x.hour == 10,
        '11': x.hour == 11,
        '12': x.hour == 12,
        '13': x.hour == 13,
        '14': x.hour == 14,
        '15': x.hour == 15,
        '16': x.hour == 16,
        '17': x.hour == 17,
        '18': x.hour == 18,
        '19': x.hour == 19,
        '20': x.hour == 20,
        '21': x.hour == 21,
        '22': x.hour == 22,
        '23': x.hour == 23,
    }

def get_weekday(x):
    return {
        'Weekday': x.weekday() < 5,
        'Weekend': x.weekday() >= 5
    }
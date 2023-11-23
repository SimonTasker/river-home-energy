from river import metrics
from river import linear_model
from river import optim
from river import preprocessing
from river import utils
from river import compose
import matplotlib.pyplot as plt
import datetime as dt
import csv
import calendar
import math

file_location = './Processed_Data_Daily_CSV/House_2_daily_totals.csv'
# file_location = './home_kettle_today_daily_processed.csv'
time_row_name = 'Time'
time_format = '%Y-%m-%d %H:%M:%S'
value_row_name = 'Appliance8'
# value_row_name = 'Value'

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

def get_day_distances(x):
    return {

    }

def get_day(x):
    return {
        calendar.day_name[day]: day == x.weekday()
        for day in range(0, 7)
    }

def get_weekday(x):
    return {
        'Weekday': x.weekday() < 5,
        'Weekend': x.weekday() >= 5
    }

def make_model(alpha):

    features = compose.TransformerUnion(
        get_ordinal_date,
        get_month,
        # get_month_distances,
        get_day,
        get_weekday
    )

    scale = preprocessing.StandardScaler()

    learn = linear_model.LinearRegression(
        intercept_lr=0.3,
        optimizer=optim.SGD(0.005),
        loss=optim.losses.Quantile(alpha=alpha)
    )

    model = features | scale | learn
    model = preprocessing.TargetStandardScaler(regressor=model)

    return model

metric = metrics.MSE()

models = {
    'center': make_model(0.5),
    'upper': make_model(0.9)
}

dates = []
y_trues = []
y_preds = {
    'center': [],
    'upper': []
}

with open(file_location, 'r') as csvfile:
    d_reader = csv.DictReader(csvfile)
    
    for row in d_reader:

        x = dt.datetime.strptime(row[time_row_name], time_format)
        y = float(row[value_row_name])

        for name, model in models.items():
            y_preds[name].append(model.predict_one(x))
            model.learn_one(x, y)

        metric.update(y, y_preds['center'][-1])

        dates.append(x)
        y_trues.append(y)

# Plot the results
fig, ax = plt.subplots(figsize=(10, 6))
ax.grid(alpha=0.75)
ax.plot(dates, y_trues, linestyle='--', marker='x', lw=1, color='#2ecc71', alpha=1, label='Ground truth')
# ax.plot(dates, y_preds['center'], linestyle='--', marker='o', lw=3, color='#e74c3c', alpha=0.8, label='Prediction')
ax.fill_between(dates, y_preds['center'], y_preds['upper'], color='#e74c3c', alpha=0.3, label='Prediction interval')

# Loop through the points and add circles with dynamically calculated radius
for date, y_true, y_pred in zip(dates, y_trues, y_preds['upper']):
    if y_true > y_pred:
        ax.scatter(date, y_true, color='red', marker='D', s=50)

ax.legend()
ax.set_title(metric)
# plt.ylim(0,5)
plt.show()
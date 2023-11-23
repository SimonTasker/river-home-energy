import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from models.daily_nowcasting.model import make_model

from river import metrics
import matplotlib.pyplot as plt
import pickle
import datetime

# Specify the file path where the pickled data is stored
file_path = "/mnt/data/Documents/Dissertation/river-home-energy/test/output_5d.pkl"

# Load the pickled data from the file
with open(file_path, "rb") as file:
    pickled_data = file.read()

# Unpickle the data
output = pickle.loads(pickled_data)

def FormatData(data):
    _time = datetime.datetime.strptime(data['Time'], '%Y-%m-%dT%H:%M:%S')
    _data = data['ENERGY']

    return _time, _data['Today']

# Data Format:
# Time : datetime
# TotalStartTime : datetime
# Total : number
# Yesterday : number
# Today : number
# Period : number
# Power : number
# ApparentPower : number
# ReactivePower : number
# Factor : number
# Voltage : number
# Current : number

metric = metrics.MSE()

models = {
    'center': make_model(0.5),
    'upper': make_model(0.9)
}

x_vals = []
y_trues = []
y_preds = {
    'center': [],
    'upper': []
}

delta = datetime.timedelta(days=1)

# Initial day predictions before actuals come in
prev_x, prev_y = FormatData(output[0])
for name, model in models.items():
    y_preds[name].append(model.predict_one(prev_x))

# Loop all actuals
for val in output:

    # Format into acceptable format
    x, y = FormatData(val)

    offset = x.date() - prev_x.date()

    if (offset.days > 0) :

        for name, model in models.items():
            # Learn from last day
            model.learn_one(prev_x, prev_y)
            # Predict next day
            y_preds[name].append(model.predict_one(x))

        metric.update(prev_y, y_preds['center'][-1])

        x_vals.append(prev_x.date())
        y_trues.append(prev_y)

    prev_x = x
    prev_y = y

    #for name, model in models.items():
    #    model.learn_one(x, y)
    #    y_preds[name].append(model.predict_one(x))

    # Update the error metric
    #metric.update(y, y_preds['center'][-1])

    # Store the true value and the prediction
    #x_vals.append(count)
    #y_trues.append(y)

# Pickle the data
# x_vals_pickled_data = pickle.dumps(x_vals)
# y_trues_pickled_data = pickle.dumps(y_trues)
# y_preds_pickled_data = pickle.dumps(y_preds)

# # Save the pickled data to the file
# with open('x_vals.pkl', "wb") as file:
#     file.write(x_vals_pickled_data)

# with open('y_trues.pkl', "wb") as file:
#     file.write(y_trues_pickled_data)

# with open('y_preds.pkl', "wb") as file:
#     file.write(y_preds_pickled_data)

y_preds['center'].pop()
y_preds['upper'].pop()

fig, ax = plt.subplots(figsize=(10, 6))
ax.grid(alpha=0.75)
ax.plot(x_vals, y_trues, linestyle='--', marker='x', lw=1, color='#2ecc71', alpha=1, label='Ground truth')
# ax.plot(dates, y_preds['center'], linestyle='--', marker='o', lw=3, color='#e74c3c', alpha=0.8, label='Prediction')
ax.fill_between(x_vals, y_preds['center'], y_preds['upper'], color='#e74c3c', alpha=0.3, label='Prediction interval')

# Loop through the points and add circles with dynamically calculated radius
for date, y_true, y_pred in zip(x_vals, y_trues, y_preds['upper']):
    if y_true > y_pred:
        ax.scatter(date, y_true, color='red', marker='D', s=50)

ax.legend()
ax.set_title(metric)
# plt.ylim(0,5)
plt.show()
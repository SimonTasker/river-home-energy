import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from models.daily_nowcasting.model import make_model

from river import metrics
import matplotlib.pyplot as plt
import pickle
import datetime

# Trains an river model - directly from pickled data

# Pickled data
#file_path = "./output_kettle_30d.pkl"
file_path = "/Users/simontasker/Documents/MSc Software Engineering/Dissertation/Source/river-home-energy/tools/output_kettle_30d.pkl"

# Load the pickled data from the file
with open(file_path, "rb") as file:
    pickled_data = file.read()

# Unpickle the data
output = pickle.loads(pickled_data)

# Formats the JSON data into the x, y format required by the model
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

# Creates the models, given the seleted daily nowcasting model
models = {
    'center': make_model(0.5),
    'upper': make_model(0.9)
}

# Storage values
x_vals = []
y_trues = []
y_preds = {
    'center': [],
    'upper': []
}

# Initial day predictions before actuals come in
prev_x, prev_y = FormatData(output[0])
for name, model in models.items():
    y_preds[name].append(model.predict_one(prev_x))

# Loop all actuals
for val in output:

    # Format into acceptable format
    x, y = FormatData(val)

    # Get offset between current and previous value
    offset = x.date() - prev_x.date()

    # If we've crossed into the next day - update model
    if (offset.days > 0) :
        # Next day, isn't the next sample (i.e. x)
        # But is full day step (i.e. next time this model)
        # Will be updated
        next_x = prev_x + datetime.timedelta(days=1)

        # Need to update each model
        for name, model in models.items():
            # Learn from last day
            model.learn_one(prev_x, prev_y)
            # Predict next day
            y_preds[name].append(model.predict_one(next_x))

        # Update metrics (N.B. update from previous prediction - 
        # not the one we just made, hence -2) 
        metric.update(prev_y, y_preds['center'][-2])

        x_vals.append(prev_x.date())
        y_trues.append(prev_y)

    prev_x = x
    prev_y = y

next_day = prev_x + datetime.timedelta(days=1)
x_vals.append(next_day.date())
y_trues.append(0)

fig, ax = plt.subplots(figsize=(10, 6))
ax.grid(alpha=0.75)
ax.plot(x_vals, y_trues, linestyle='--', marker='x', lw=1, color='#2ecc71', alpha=1, label='Ground truth')
ax.fill_between(x_vals, y_preds['center'], y_preds['upper'], color='#e74c3c', alpha=0.3, label='Prediction interval')

# Loop through the points and add circles with dynamically calculated radius
for date, y_true, y_pred in zip(x_vals, y_trues, y_preds['upper']):
    if y_true > y_pred:
        ax.scatter(date, y_true, color='red', marker='D', s=50)

ax.legend()
ax.set_title(metric)
plt.show()
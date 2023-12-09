# River imports
import pickle
from river import metrics

# Application imports
import os
import logging
import datetime

# River model import
import sys
import os.path
# sys.path.append(
#     os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from models.daily_nowcasting.model import make_model
from mediator import MediatedComponent

# ================================================
class RiverModel(MediatedComponent):
    # ================================================
    # Class Constructor
    def __init__(self, data_dir, config):
        MediatedComponent.__init__(self)

        # Get model file path from config
        self.model_file = data_dir + '/' + config['River Settings']['Model File']

        # Define loggers
        self.river_logger = logging.getLogger('River')

        # Models
        self.models = {
            'center': make_model(0.5),
            'upper': make_model(0.9)
        }

        self.river_logger.info('Looking for existing model at ' + self.model_file)
        # Try and load any existing model
        if os.path.exists(self.model_file):
            self.river_logger.info('Found and loading existing model')
            with open(self.model_file, 'rb') as f:
                self.models = pickle.load(f)
        else:
            self.river_logger.info('No existing model found')

        # Metrics
        #self.metric = metrics.MSE()

        self.x_vals  = []
        self.y_trues = []
        self.y_preds = {
            'center': [],
            'upper': []
        }

        self.prev_x = datetime.datetime.now()
        self.prev_y = 0

        # Initial day predictions before actuals come in
        for name, model in self.models.items():
            self.y_preds[name].append(model.predict_one(self.prev_x))

    # ================================================
    def train(self, x, y):
        offset = x.date() - self.prev_x.date()

        if (offset.days > 0):
            self.river_logger.debug("Training models with %s %s", self.prev_x, self.prev_y)
            
            for name, model in self.models.items():
                # Learn from the previous day
                # N.B. this is delayed from the initial prediction
                model.learn_one(self.prev_x, self.prev_y)
                # Make a prediction for next day (i.e. this day)
                pred = model.predict_one(x)
                self.river_logger.info("Model " + name + "'s Prediction for " + str(x.date()) + " = " + str(pred))
                self.mediator.notify_model_prediction(x, name, pred)
                self.y_preds[name].append(pred)

            # Update metrics (N.B. update from previous prediction - 
            # not the one we just made, hence -2) 
            #self.metric.update(self.prev_y, self.y_preds['center'][-2])

            self.x_vals.append(self.prev_x.date())
            self.y_trues.append(self.prev_y)

            # Update saved model
            with open(self.model_file, 'wb') as f:
                pickle.dump(self.models, f)
        
        self.prev_x = x
        self.prev_y = y
    
    # ================================================
    def attach_observer(self, observer):
        self._observers.append(observer)

    # ================================================
    def get_y_trues(self):
        return self.y_trues
    
    # ================================================
    def get_y_preds(self):
        return self.y_preds
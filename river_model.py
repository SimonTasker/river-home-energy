# River imports
from river import linear_model
from river import preprocessing
from river import optim
from river import metrics
from river 
import pickle

# Application imports
import os
import logging

# ================================================
class RiverModel:
    # ================================================
    # Class Constructor
    def __init__(self, data_dir, config):
        # Get model file path from config
        self.model_file = data_dir + '/' + config['River Settings']['Model File']

        # Define loggers
        self.river_logger = logging.getLogger('River')

        # Default model parameters
        scale = preprocessing.StandardScaler()
        learn = linear_model.LinearRegression(
            intercept_lr=0,
            optimizer=optim.SGD(lr=0.01))

        
        self.model = scale | learn

        # Metrics
        self.metric = metrics.MAE()

        self.river_logger.info('Looking for existing model at ' + self.model_file)
        # Try and load any existing model
        if os.path.exists(self.model_file):
            self.river_logger.info('Found and loading existing model')
            with open(self.model_file, 'rb') as f:
                self.model = pickle.load(f)
        else:
            self.river_logger.info('No existing model found')

        self.y_trues = []
        self.y_preds = []
    
    # ================================================
    def train(self, x, y):
        self.river_logger.debug("Training model with %s %s", x, y)

        # Make a prediction given current model
        y_pred = self.model.predict_one(x)
        # Learn from new data
        self.model.learn_one(x, y)

        # Update metrics based on prediction to actual
        self.metric.update(y, y_pred)

        self.y_trues.append(y)
        self.y_preds.append(y_pred)

        # Update saved model
        with open(self.model_file, 'wb') as f:
            pickle.dump(self.model, f)

    # ================================================
    def predict_one(self, x):
        return self.model.predict_one(x)
    
    # ================================================
    def get_y_trues(self):
        return self.y_trues
    
    # ================================================
    def get_y_preds(self):
        return self.y_preds
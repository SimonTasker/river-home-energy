# Pikle Imports
from datetime import datetime
import json
import pickle

# Application imports
import logging

# ================================================
class PickleJSONRiverTrainer:
    # ================================================
    # Class Constructor
    def __init__(self, river_model):
        self.river_model = river_model

        # Define logger
        self.logger = logging.getLogger('Pickle')

        # Set pickle config
        self.pickle_file = "output_5d.pkl"

    def Train():
        print("train")
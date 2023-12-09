from models.utils import *

from river import linear_model
from river import optim
from river import preprocessing
from river import compose

def make_model(alpha):
    
    features = compose.TransformerUnion(
        get_ordinal_date,
        get_month,
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
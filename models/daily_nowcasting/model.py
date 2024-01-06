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
        optimizer=optim.Adam(
            lr=.01,
            beta_1=.9,
            beta_2=.99
        ),
        loss=optim.losses.Quantile(alpha=alpha),
        l1=.1,
        intercept_lr=.01,
        initializer=optim.initializers.Zeros()
    )

    model = features | scale | learn
    
    return model
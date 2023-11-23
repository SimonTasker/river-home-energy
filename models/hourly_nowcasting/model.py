from models.utils import *

from river import linear_model
from river import optim
from river import preprocessing
from river import compose

def make_model(alpha):

    features = compose.TransformerUnion(
        get_ordinal_date,
        get_day,
        get_hour,
        get_hour_distances,
        get_weekday
    )

    scale = preprocessing.StandardScaler()

    learn = linear_model.LinearRegression(
        intercept_lr=0.1,
        optimizer=optim.SGD(0.05),
        loss=optim.losses.Quantile(alpha=alpha)
    )

    model = features | scale | learn
    model = preprocessing.TargetStandardScaler(regressor=model)

    return model

models = {
    'center': make_model(0.5),
    'upper': make_model(0.95)
}
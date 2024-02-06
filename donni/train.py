"""
Module for training and tuning MVEnn with dadi-simulated data
"""
import logging
import os
from multiprocessing import Pool
import numpy as np

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # FATAL
logging.getLogger("tensorflow").setLevel(logging.FATAL)

import tensorflow as tf
from tensorflow import keras
from keras.models import Model
from keras.layers import Dense, Input
from keras.callbacks import EarlyStopping
import keras.backend as K
import pickle
import keras_tuner as kt

def prep_data(data: dict, single_output=True):
    """
    Helper method for outputing X and y from input data dict
    Input: data dict generated by generate_fs() method
    Output: X_input as a list of flattened fs datasets
            y_label_unpack as a list of list, where each inner list
            is the label of one single demographic param by default,
            If single_output=False, y_label_unpack will be a list of one list,
            with this one inner list containing tuples of all dem params.
    """

    # require dict to be ordered (Python 3.7+)
    X_input = [np.array(fs).flatten() for fs in data.values()]
    y_label = list(data.keys())

    # parse labels into single list for each param (required for single_output)
    y_label_unpack = list(zip(*y_label)) if single_output else [y_label]

    return np.array(X_input), y_label_unpack


def regression_nll_loss(sigma_sq, epsilon=1e-6):
    """Custom loss function to train both mean and variance"""
    def nll_loss(y_true, y_pred):
        return 0.5 * K.mean(
            K.log(sigma_sq + epsilon) + K.square(y_true - y_pred) / (sigma_sq + epsilon)
            )
    return nll_loss


class CustomLayer(keras.layers.Layer):
    """Custom activation layer to scale the param output to the simulated range"""
    def __init__(self, p_range, **kwargs):
        super(CustomLayer, self).__init__(**kwargs)
        self.p_range = p_range

    def call(self, inputs):
        a, b, c = self.p_range
        return (K.sigmoid(inputs) * a + b) / c
    
    def get_config(self):
        return {'p_range': self.p_range}
        

def _train_worker_func(args):
    X_input, y_label, param_idx, param_range, outdir, tuning = args
    from tensorflow.python.framework.ops import disable_eager_execution
    disable_eager_execution()
    
    def model_builder(hp):
        """Hyperparam tuning"""
        inp = Input(shape=X_input.shape[1])
        x = Dense(
            units=hp.Int("units_1", min_value=16, max_value=64, step=16),
            activation="relu",
        )(inp)
        x = Dense(
            units=hp.Int("units_2", min_value=4, max_value=16, step=4),
            activation="relu",
        )(x)
        mean = Dense(1, activation=CustomLayer(param_range))(x)
        var = Dense(1, activation="softplus")(x)

        train_model = Model(inp, mean)
        lr = hp.Float(
            "lr", min_value=1e-4, max_value=1e-2, sampling="log", default=0.001
        )
        train_model.compile(
            loss=regression_nll_loss(var),
            optimizer=keras.optimizers.legacy.Adam(learning_rate=lr),
            metrics=[keras.metrics.RootMeanSquaredError()],
        )
        return train_model

    if tuning:  # run tuning to return best_hp
        # instantiate the Hyperband tuner
        tuner = kt.Hyperband(
            model_builder,
            objective="val_loss",
            max_epochs=100, # default is 100
            directory="tuning_outdir",
            project_name=f"mvenn_tuning_{param_idx}",
            overwrite=True,
        )

        # Run the hyperparameter search
        tuner.search(
            X_input,
            y_label,
            validation_split=0.2,
            verbose=0,
            )
        # print tuner results to stdout
        tuner.results_summary()  # to do: print this to specified file path

        # Get the optimal hyperparameters
        best_hp = tuner.get_best_hyperparameters()[0]
        
        # fix the layer sizes and tune the learning rate some more
        hp = kt.HyperParameters()
        hp.Fixed("units_1", value=best_hp.get("units_1"))
        hp.Fixed("units_2", value=best_hp.get("units_2"))
        
        tuner = kt.RandomSearch(
            model_builder,
            hyperparameters=hp,
            tune_new_entries=True, # retune the learning rate (not fixed)
            objective="val_loss",
            max_trials=100, # default to 10
            directory="tuning_outdir",
            project_name=f"lr_random_{param_idx}",
            overwrite=True,
            )
        
        tuner.search(
            X_input,
            y_label,
            epochs=50,
            validation_split=0.2,
            verbose=0,
            )
            
        # print tuner results to stdout
        tuner.results_summary()  # to do: print this to specified file path
            
        # Get the final optimal hyperparameters
        best_hp = tuner.get_best_hyperparameters()[0]

    else:
        # use default hyperparams if not tuning
        best_hp = kt.HyperParameters()
        best_hp.Choice(name="units_1", values=[32])
        best_hp.Choice(name="units_2", values=[16])
        best_hp.Choice(name="lr", values=[0.001])

    # initiate model from chosen hyperparams and train

    inp = Input(shape=X_input.shape[1])
    x = Dense(best_hp.get("units_1"), activation="relu")(inp)
    x = Dense(best_hp.get("units_2"), activation="relu")(x)

    mean = Dense(1, activation=CustomLayer(param_range))(x)
    var = Dense(1, activation="softplus")(x)

    train_model = Model(inp, mean)
    pred_model = Model(inp, [mean, var])

    lr = best_hp.get("lr")
    train_model.compile(
        loss=regression_nll_loss(var),
        optimizer=keras.optimizers.legacy.Adam(learning_rate=lr),
        metrics=[keras.metrics.RootMeanSquaredError()],
    )

    train_model.fit(
        X_input,
        np.array(y_label),
        epochs=100,
        validation_split=0.2,
        callbacks=[EarlyStopping(monitor="val_loss", patience=5)],
        verbose=0,
    )
    
    pred_model.save(f"{outdir}/param_{param_idx+1:02d}_predictor.keras")
    
def get_param_range(param_type):
    range_dict = {"nu": (4, -2, 1),
                    "T": (1.99, 0.01, 1),
                    "m": (10, 0, 1),
                    "s": (0.98, 0.01, 1),
                    "F": (1, 0, 1),
                    "f": (1, 0, 1),
                    "misid": (1, 0, 4)}
    return range_dict[param_type]

def train(X_input, all_y_label, param_names, outdir: str, tuning: bool):
    args_list = []
    for param_idx, (y_label, label_name) in enumerate(zip(all_y_label, param_names)):
        # process special case labels
        if label_name.startswith("nu"):
            param_type = "nu"
        elif label_name == "misid": # to separate from param m
            param_type = "misid"
        else:
            param_type = label_name[0]
        p_range = get_param_range(param_type) # tuple of a,b,c
        args_list.append((X_input, np.array(y_label), param_idx, p_range, outdir, tuning))
    with Pool(processes=len(all_y_label)) as pool:
        pool.map(_train_worker_func, args_list)

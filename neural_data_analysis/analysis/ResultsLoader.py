#!/usr/bin/env python3

"""
ResultsLoader.py

Description:
This module provides functionality for loading in results.

Classes:
- ResultsLoader

Functions:

Author: Kevin J. M. Le
Date: 2024-06-19
"""

import glob
import pickle
from pathlib import Path
import yaml
from ..utils import (
    recursive_dict_update,
    add_default_repr,
    setup_default_logger,
)
import pandas as pd
import logging


@add_default_repr
class ResultsLoader(object):
    """
    Expect a path to a results directory with a config.yaml file and a results.pkl file.
    """

    def __init__(self, directory, logger: logging.Logger = None):
        if logger is None:
            self.logger = setup_default_logger()
        else:
            self.logger = logger

        self.logger.info(
            "============== Initializing ResultsLoader class =============="
        )
        self.directory = Path(directory)
        self.config = self.load_config()
        self.predictions = self.load_predictions()
        self.shap_values = self.load_shap()

    def load_config(self, changes=None):
        yaml_file = glob.glob(f"{self.directory}/*.yaml")[0]
        logging.info(f"Loading config file [{yaml_file}]...")
        config = yaml.load(open(yaml_file, "r"), Loader=yaml.FullLoader)
        if changes is not None:
            recursive_dict_update(config, changes)
        logging.info(f"COMPLETED: config file [{yaml_file}] loaded.")
        return config

    def load_predictions(self):
        pickle_file = glob.glob(f"{self.directory}/*results.pkl")[0]
        logging.info(f"Loading results file [{pickle_file}]...")
        results = pickle.load(open(pickle_file, "rb"))
        logging.info(f"COMPLETED: results file [{pickle_file}] loaded.")
        return results

    def load_shap(self):
        try:
            shap_file = glob.glob(f"{self.directory}/*shap_values.csv")[0]
            logging.info(f"Loading SHAP file [{shap_file}]...")
            shap_values = pd.read_csv(shap_file)
            logging.info(f"COMPLETED: SHAP file [{shap_file}] loaded.")
            return shap_values
        except IndexError:
            logging.info(f"No SHAP file found in [{self.directory}].")
            return None


if __name__ == "__main__":
    result_name = "2023-06-16_results_per_PC"
    result_loader = ResultsLoader(result_name)

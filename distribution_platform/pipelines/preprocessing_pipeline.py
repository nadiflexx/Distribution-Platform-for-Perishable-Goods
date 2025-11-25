# pipelines/preprocessing_pipeline.py

import pandas as pd

from ..utils.correaltions import get_significant_features
from ..utils.data_loaders import load_data, save_dataframe_to_csv
from ..utils.enums import DataTypesEnum
from ..config.paths import DATA_RAW, DATA_PROCESSED

import numpy as np


def run_preprocessing(csv_name):

    # 1) Load CSV
    df_raw = load_data(DataTypesEnum.CSV, DATA_RAW / f"{csv_name}.csv")

    # 2) Validate rows using Pydantic
    #fruits = load_fruit_objects(df_raw)

    # 3) Convert validated objects to DataFrame
    #df_valid = fruits_to_dataframe(fruits)

    # 4) Clean dataset (encoding, scaling, outliers, imputation…)
    #cleaner = DataCleaner(df_raw)
    df_clean = cleaner.clean()

    # 5 Export csv content
    save_dataframe_to_csv(df_clean, DATA_PROCESSED / f"{csv_name}.csv")

    # 7) Select significant features (correlation + p-value)
    features = get_significant_features(df_clean, "")

    print("🔍 Features seleccionadas:", features)

    return df_clean, cleaner, features
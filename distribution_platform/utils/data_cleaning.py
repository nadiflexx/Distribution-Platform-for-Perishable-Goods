import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import re


# -------------------------------------------------------------
def normalize_column_names(self):
    self.df.columns = (
        self.df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("[^a-z0-9_]", "", regex=True)
    )


# -------------------------------------------------------------
def detect_types(self):
    for col in self.df.columns:
        if col in self.excluded_cols:
            continue

        if np.issubdtype(self.df[col].dtype, np.datetime64):
            self.datetime_cols.append(col)

        elif np.issubdtype(self.df[col].dtype, np.number):
            self.numeric_cols.append(col)

        else:
            self.categorical_cols.append(col)


# -------------------------------------------------------------
def auto_impute(self):
    for col in self.numeric_cols:
        # reemplazar valores vacíos → NaN (sin warnings)
        self.df[col] = self.df[col].replace(["", " ", "null", "None"], np.nan)

        # convertir a float
        self.df[col] = self.df[col].astype(float)

        # imputar con la mediana
        self.df[col] = self.df[col].fillna(self.df[col].median())
    for col in self.categorical_cols:
        self.df[col] = self.df[col].replace(["", " ", "null", "None"], np.nan)
        self.df[col] = self.df[col].fillna(self.df[col].mode()[0])


# -------------------------------------------------------------
def auto_encode(self):
    for col in self.categorical_cols:
        if col in self.excluded_cols:
            continue

        le = LabelEncoder()
        self.df[col] = le.fit_transform(self.df[col].astype(str))
        self.label_encoders[col] = le


# -------------------------------------------------------------
def auto_outliers(self, z_thresh=4):
    if not self.numeric_cols:
        return

    df_no_outliers = self.df.copy()
    for col in self.numeric_cols:
        z = np.abs((self.df[col] - self.df[col].mean()) / self.df[col].std())
        df_no_outliers = df_no_outliers[z < z_thresh]

    self.df = df_no_outliers.reset_index(drop=True)


# -------------------------------------------------------------
def auto_scale(self):
    if not self.numeric_cols:
        return

    self.scaler = StandardScaler()
    self.df[self.numeric_cols] = self.scaler.fit_transform(self.df[self.numeric_cols])


# -------------------------------------------------------------
def encode_target(self):
    if not self.target:
        return

    le = LabelEncoder()
    self.df[self.target] = le.fit_transform(self.df[self.target].astype(str))
    self.label_encoders[self.target] = le


# -------------------------------------------------------------
def to_snake_case(df: pd.DataFrame) -> pd.DataFrame:
    def snake(col):
        # Reemplaza caracteres no alfanuméricos por espacios
        col = re.sub(r"[^0-9a-zA-Z]+", " ", col)
        # Inserta guiones bajos entre minúsculas-seguidas-de-mayúsculas (CamelCase → camel_case)
        col = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", col)
        # Convierte a snake case
        col = col.strip().replace(" ", "_").lower()
        return col

    df = df.copy()
    df.columns = [snake(c) for c in df.columns]
    return df


# --------------------------------------------------------------
def clean(self) -> pd.DataFrame:
    self.normalize_column_names()
    self.detect_types()
    self.auto_impute()
    self.auto_outliers()
    self.auto_encode()
    self.encode_target()
    self.auto_scale()
    return self.df

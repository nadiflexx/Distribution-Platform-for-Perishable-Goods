import os

from distribution_platform.config import paths
from distribution_platform.utils import data_cleaning, data_loaders, enums
from distribution_platform.utils.geolocator import get_coordinates
from distribution_platform.models.order import Order
import pandas as pd


class ETLProcessor:
    """ETL processor for distribution platform data pipeline.

    Handles loading, cleaning, transforming, and saving perishable goods
    distribution data from raw CSV files to processed format.

    Attributes
    ----------
    paths : Config paths
        Configuration paths for data directories.
    df_clientes : pd.DataFrame
        Clients data.
    df_lineas_pedido : pd.DataFrame
        Order lines data.
    df_pedidos : pd.DataFrame
        Orders data.
    df_productos : pd.DataFrame
        Products data.
    df_provincias : pd.DataFrame
        Provinces data.
    df_destinos : pd.DataFrame
        Destinations data.
    df_final : pd.DataFrame
        Final processed dataframe.
    """

    def __init__(self):
        self.paths = paths
        self.df_clientes = None
        self.df_lineas_pedido = None
        self.df_pedidos = None
        self.df_productos = None
        self.df_provincias = None
        self.df_destinos = None
        self.df_final = None

    # ------------------------------------------------------------------
    # 1. LOAD
    # ------------------------------------------------------------------
    def load_raw_data(self):
        """Load all datasets from DATA_RAW folder."""
        self.df_clientes = data_loaders.load_data(
            enums.DataTypesEnum.CSV, self.paths.DATA_RAW / "dboClientes.csv"
        )
        self.df_lineas_pedido = data_loaders.load_data(
            enums.DataTypesEnum.CSV, self.paths.DATA_RAW / "dboLineasPedido.csv"
        )
        self.df_pedidos = data_loaders.load_data(
            enums.DataTypesEnum.CSV, self.paths.DATA_RAW / "dboPedidos.csv"
        )
        self.df_productos = data_loaders.load_data(
            enums.DataTypesEnum.CSV, self.paths.DATA_RAW / "dboProductos.csv"
        )
        self.df_provincias = data_loaders.load_data(
            enums.DataTypesEnum.CSV, self.paths.DATA_RAW / "dboProvincias.csv"
        )
        self.df_destinos = data_loaders.load_data(
            enums.DataTypesEnum.CSV, self.paths.DATA_RAW / "dboDestinos.csv"
        )

    # ------------------------------------------------------------------
    # 2. CLEAN
    # ------------------------------------------------------------------
    def clean_comas(self):
        """Replace commas with dots in numeric columns and convert to float."""
        # Call replace comas for distancia and precio_venta columns
        self.df_destinos["distancia_km"] = (
            self.df_destinos["distancia_km"].apply(self.replace_comas).astype(float)
        )
        self.df_productos["precio_venta"] = (
            self.df_productos["precio_venta"].apply(self.replace_comas).astype(float)
        )

    def replace_comas(self, value):
        """Helper function to replace commas with dots in a string."""
        if isinstance(value, str):
            return value.replace(",", ".")
        return value

    def clean_destinos(self):
        """Normalize destinos and calculate GPS coordinates."""
        self.df_destinos["nombre_completo"] = self.df_destinos[
            "nombre_completo"
        ].str.replace("Destino ", "", regex=False)

        # check coordeinates only for those values while coodenadas_gps is null or empty or \N
        while (
            self.df_destinos["coordenadas_gps"].isnull().any()
            or (
                self.df_destinos["coordenadas_gps"].str.split().str.join("") == ""
            ).any()
            or (self.df_destinos["coordenadas_gps"] == "\\N").any()
        ):
            # Filter only those rows that need coordinates
            mask = (
                self.df_destinos["coordenadas_gps"].isnull()
                | (self.df_destinos["coordenadas_gps"].str.split().str.join("") == "")
                | (self.df_destinos["coordenadas_gps"] == "\\N")
            )
            self.df_destinos.loc[mask, "coordenadas_gps"] = self.df_destinos.loc[
                mask, "nombre_completo"
            ].apply(get_coordinates)
        self.df_destinos = self.df_destinos.drop(columns="provincia_id")

    def normalize_column_names(self):
        """Convert all DF column names to snake_case."""
        self.df_clientes = data_cleaning.to_snake_case(self.df_clientes)
        self.df_lineas_pedido = data_cleaning.to_snake_case(self.df_lineas_pedido)
        self.df_pedidos = data_cleaning.to_snake_case(self.df_pedidos)
        self.df_productos = data_cleaning.to_snake_case(self.df_productos)
        self.df_provincias = data_cleaning.to_snake_case(self.df_provincias)
        self.df_destinos = data_cleaning.to_snake_case(self.df_destinos)

    # ------------------------------------------------------------------
    # 3. TRANSFORM (MERGE)
    # ------------------------------------------------------------------
    def merge_datasets(self):
        """Perform all the merging logic step by step."""
        self.df_pedidos = self.df_pedidos.rename(
            columns={"destino_entrega_id": "destino_id"}, errors="raise"
        )

        df_pedidos_clientes = self.df_pedidos.merge(
            self.df_clientes, on="cliente_id", how="left"
        )
        df_pedidos_clientes = df_pedidos_clientes.drop(
            columns=["cliente_id", "nombre", "fecha_registro"]
        )

        df_pedidos_clientes_destinos = df_pedidos_clientes.merge(
            self.df_destinos, on="destino_id", how="left"
        )

        df_lineas = self.df_lineas_pedido.merge(
            df_pedidos_clientes_destinos, on="pedido_id", how="left"
        )

        df_final = df_lineas.merge(self.df_productos, on="producto_id", how="left")
        df_final = df_final.drop(
            columns=["linea_pedido_id", "producto_id", "destino_id"]
        )

        df_final = df_final.rename(
            columns={
                "nombre_completo": "destino",
                "nombre": "producto",
                "cantidad": "cantidad_producto",
                "email": "email_cliente",
            }
        )

        df_final = df_final.reindex(
            [
                "pedido_id",
                "fecha_pedido",
                "producto",
                "cantidad_producto",
                "precio_venta",
                "tiempo_fabricacion_medio",
                "caducidad",
                "destino",
                "distancia_km",
                "coordenadas_gps",
                "email_cliente",
            ],
            axis=1,
        )

        self.df_final = df_final

    # ------------------------------------------------------------------
    # 4. SAVE
    # ------------------------------------------------------------------
    def save_processed(self):
        """Save final dataframe into processed folder."""
        out_path = self.paths.DATA_PROCESSED / "pedidos.csv"
        data_loaders.save_dataframe_to_csv(self.df_final, out_path)

    # ------------------------------------------------------------------
    # 5. PIPELINE
    # ------------------------------------------------------------------
    def run(self):
        """High-level method to run the entire ETL."""
        output_path = self.paths.DATA_PROCESSED / "pedidos.csv"

        # If already processed, return directly
        if os.path.exists(output_path):
            return data_loaders.load_data(enums.DataTypesEnum.CSV, output_path)

        # Otherwise run full ETL
        self.load_raw_data()
        self.normalize_column_names()
        self.clean_destinos()
        self.clean_comas()
        self.merge_datasets()
        self.save_processed()

        return self.df_final

    def transform_to_orders(self, df_pedidos):
        """Transform DataFrame of orders into list of Order objects.
        List should be a list inside a list order which each order is grouped by 'pedido_id'. Example: [[order_pedido_1], [order_pedido_2]]. where order pedido 1 should contain all the lines of that pedido_id order by caducity ascending.

        Args:
            df_pedidos (pd.DataFrame): DataFrame containing order data.


        Returns:
            List[List[Order]]: List of orders grouped by 'pedido_id'.
        """

        orders_grouped = []
        grouped = df_pedidos.sort_values(by="caducidad").groupby("pedido_id")

        for pedido_id, group in grouped:
            order_lines = []
            for _, row in group.iterrows():
                order_line = Order(
                    pedido_id=row["pedido_id"],
                    fecha_pedido=row["fecha_pedido"],
                    producto=row["producto"],
                    cantidad_producto=row["cantidad_producto"],
                    precio_venta=row["precio_venta"],
                    tiempo_fabricacion_medio=row["tiempo_fabricacion_medio"],
                    caducidad=row["caducidad"],
                    destino=row["destino"],
                    distancia_km=row["distancia_km"],
                    coordenadas_gps=row["coordenadas_gps"],
                    email_cliente=row["email_cliente"],
                )
                order_lines.append(order_line)
            orders_grouped.append(order_lines)

        return orders_grouped

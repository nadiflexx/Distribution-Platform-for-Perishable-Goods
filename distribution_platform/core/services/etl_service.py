"""
ETL Service.
Orchestrates the entire data ingestion pipeline: Load -> Clean -> Merge -> Transform.
"""

import pandas as pd

from distribution_platform.config.enums import DataTypesEnum
from distribution_platform.config.logging_config import log as logger
from distribution_platform.config.settings import Paths
from distribution_platform.core.logic.data_cleaner import DataCleaner
from distribution_platform.core.models.order import Order
from distribution_platform.infrastructure.database.sql_client import (
    load_full_dataset,
    load_provinces_names,
)
from distribution_platform.infrastructure.external.geocoding import fetch_coordinates
from distribution_platform.infrastructure.persistence.coordinates import (
    CoordinateCache,
)
from distribution_platform.infrastructure.persistence.file_reader import FileReader


class ETLService:
    """
    Core Service for Data Processing.
    Handles both File-based and Database-based ingestion flows.
    """

    def __init__(self):
        self.paths = Paths()
        self.coord_cache = CoordinateCache()

        self.df_clientes = None
        self.df_lineas = None
        self.df_pedidos = None
        self.df_productos = None
        self.df_provincias = None
        self.df_destinos = None

        self.df_final: pd.DataFrame | None = None

    def run(
        self, uploaded_files: dict | None = None, use_database: bool = False
    ) -> list[list[Order]]:
        """
        Main execution point for the ETL pipeline.

        Returns:
            List of Lists of Orders (Grouped by Order ID).
        """
        logger.info(f"Starting ETL. Mode: {'Database' if use_database else 'Files'}")

        if use_database:
            self._pipeline_database()
        else:
            self._pipeline_files(uploaded_files)

        self._save_processed_data()

        logger.info("Transforming DataFrame to Domain Objects...")
        return self._transform_to_orders(self.df_final)

    # ---------------------------------------------------------
    # PIPELINE FLOWS
    # ---------------------------------------------------------

    def _pipeline_database(self):
        """Execution flow for SQL source."""
        logger.info("Loading merged dataset from Database...")
        df = load_full_dataset()
        self.df_provincias = load_provinces_names()

        df = df.rename(
            columns={
                "nombre_completo": "destino",
                "nombre": "producto",
                "cantidad": "cantidad_producto",
                "email": "email_cliente",
            }
        )

        df["destino"] = (
            df["destino"]
            .astype(str)
            .str.replace("Destino ", "", regex=False)
            .str.strip()
        )

        df = df.drop(columns=["coordenadas_gps"], errors="ignore")

        target_cols = [
            "pedido_id",
            "fecha_pedido",
            "producto",
            "cantidad_producto",
            "precio_venta",
            "tiempo_fabricacion_medio",
            "caducidad",
            "destino",
            "distancia_km",
            "email_cliente",
        ]
        df = df.reindex(target_cols, axis=1)

        self.df_final = self._compute_caducidad(df)

        self._build_geo_cache(self.df_provincias, col_name="nombre")

    def _pipeline_files(self, files_dict: dict | None):
        """Execution flow for File source (CSV/Excel)."""

        if files_dict:
            logger.info("Loading from User Uploads...")
            self._load_uploads(files_dict)
        else:
            processed_path = self.paths.DATA_PROCESSED / "pedidos.csv"
            if processed_path.exists():
                logger.info("Loading from pre-processed CSV...")
                self.df_final = FileReader.load_data(DataTypesEnum.CSV, processed_path)
                return

            logger.info("Loading raw CSV files from disk...")
            self._load_raw_csvs()

        logger.info("Cleaning and Normalizing data...")
        self._normalize_all()
        self.df_destinos = DataCleaner.normalize_destinations(self.df_destinos)
        self.df_destinos = DataCleaner.clean_numeric_commas(
            self.df_destinos, ["distancia_km"]
        )
        self.df_productos = DataCleaner.clean_numeric_commas(
            self.df_productos, ["precio_venta"]
        )

        logger.info("Merging datasets...")
        self._merge_datasets()

        logger.info("Updating Coordinate Cache...")
        self._build_geo_cache(self.df_provincias, col_name="nombre")

    # ---------------------------------------------------------
    # LOADING HELPERS
    # ---------------------------------------------------------

    def _load_raw_csvs(self):
        raw = self.paths.DATA_RAW
        self.df_clientes = FileReader.load_data(
            DataTypesEnum.CSV, raw / "dboClientes.csv"
        )
        self.df_lineas = FileReader.load_data(
            DataTypesEnum.CSV, raw / "dboLineasPedido.csv"
        )
        self.df_pedidos = FileReader.load_data(
            DataTypesEnum.CSV, raw / "dboPedidos.csv"
        )
        self.df_productos = FileReader.load_data(
            DataTypesEnum.CSV, raw / "dboProductos.csv"
        )
        self.df_provincias = FileReader.load_data(
            DataTypesEnum.CSV, raw / "dboProvincias.csv"
        )
        self.df_destinos = FileReader.load_data(
            DataTypesEnum.CSV, raw / "dboDestinos.csv"
        )

    def _load_uploads(self, files: dict):
        def _get(key):
            return files.get(key, [])

        def _proc(f_list):
            f_list = f_list if isinstance(f_list, list) else [f_list]
            return FileReader.safe_concat(
                [FileReader.load_uploaded_file(f) for f in f_list]
            )

        self.df_clientes = _proc(_get("clientes"))
        self.df_lineas = _proc(_get("lineas_pedido"))
        self.df_pedidos = _proc(_get("pedidos"))
        self.df_productos = _proc(_get("productos"))
        self.df_provincias = _proc(_get("provincias"))
        self.df_destinos = _proc(_get("destinos"))

    # ---------------------------------------------------------
    # PROCESSING LOGIC (Preserved Exactly)
    # ---------------------------------------------------------

    def _normalize_all(self):
        self.df_clientes = DataCleaner.to_snake_case(self.df_clientes)
        self.df_lineas = DataCleaner.to_snake_case(self.df_lineas)
        self.df_pedidos = DataCleaner.to_snake_case(self.df_pedidos)
        self.df_productos = DataCleaner.to_snake_case(self.df_productos)
        self.df_provincias = DataCleaner.to_snake_case(self.df_provincias)
        self.df_destinos = DataCleaner.to_snake_case(self.df_destinos)

    def _merge_datasets(self):
        self.df_pedidos = self.df_pedidos.rename(
            columns={"destino_entrega_id": "destino_id"}
        )

        df = self.df_pedidos.merge(self.df_clientes, on="cliente_id", how="left")
        df = df.drop(
            columns=["cliente_id", "nombre", "fecha_registro"], errors="ignore"
        )

        df = df.merge(self.df_destinos, on="destino_id", how="left")

        df = self.df_lineas.merge(df, on="pedido_id", how="left")

        df = df.merge(self.df_productos, on="producto_id", how="left")

        df = df.drop(
            columns=["linea_pedido_id", "producto_id", "destino_id", "coordenadas_gps"],
            errors="ignore",
        )

        df = df.rename(
            columns={
                "nombre_completo": "destino",
                "nombre": "producto",
                "cantidad": "cantidad_producto",
                "email": "email_cliente",
            }
        )

        df["destino"] = (
            df["destino"]
            .astype(str)
            .str.replace("Destino ", "", regex=False)
            .str.strip()
        )

        target_cols = [
            "pedido_id",
            "fecha_pedido",
            "producto",
            "cantidad_producto",
            "precio_venta",
            "tiempo_fabricacion_medio",
            "caducidad",
            "destino",
            "distancia_km",
            "email_cliente",
        ]
        df = df.reindex(target_cols, axis=1)

        self.df_final = self._compute_caducidad(df)

    def _compute_caducidad(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates expiration dates logic."""
        df["fecha_pedido"] = pd.to_datetime(df["fecha_pedido"], errors="coerce")
        df["tiempo_fabricacion_medio"] = pd.to_numeric(
            df["tiempo_fabricacion_medio"], errors="coerce"
        )
        df["caducidad"] = pd.to_numeric(df["caducidad"], errors="coerce")

        df["dias_totales_caducidad"] = (
            1 + df["tiempo_fabricacion_medio"] + df["caducidad"]
        )

        df["fecha_caducidad_final"] = df["fecha_pedido"] + pd.to_timedelta(
            df["dias_totales_caducidad"], unit="D"
        )
        return df

    def _build_geo_cache(self, df: pd.DataFrame, col_name: str):
        """Populates coordinate cache from unique values in DF."""
        if df is None or df.empty:
            return

        destinos = df[col_name].dropna().astype(str).str.strip().unique()
        full_list = list(destinos) + ["Mataró"]

        for dest in full_list:
            if not dest:
                continue

            if self.coord_cache.get(dest) is None:
                coords = fetch_coordinates(dest)
                self.coord_cache.set(dest, coords)

        self.coord_cache.save()

    def _save_processed_data(self):
        """Persist intermediate result."""
        if self.df_final is not None:
            out = self.paths.DATA_PROCESSED / "pedidos.csv"
            FileReader.save_csv(self.df_final, out)

    def _transform_to_orders(self, df: pd.DataFrame) -> list[list[Order]]:
        """Maps DataFrame rows to Order Entity objects, grouped by ID."""
        if df is None or df.empty:
            return []

        grouped = df.sort_values("dias_totales_caducidad").groupby("pedido_id")
        result = []

        for _, group in grouped:
            current_order_lines = []
            for _, row in group.iterrows():
                order = Order(
                    pedido_id=row["pedido_id"],
                    fecha_pedido=row["fecha_pedido"],
                    producto=row["producto"],
                    cantidad_producto=row["cantidad_producto"],
                    precio_venta=row["precio_venta"],
                    tiempo_fabricacion_medio=row["tiempo_fabricacion_medio"],
                    caducidad=row["caducidad"],
                    destino=row["destino"],
                    distancia_km=row["distancia_km"],
                    email_cliente=row["email_cliente"],
                    dias_totales_caducidad=row["dias_totales_caducidad"],
                    fecha_caducidad_final=row["fecha_caducidad_final"],
                )
                current_order_lines.append(order)
            result.append(current_order_lines)

        return result


def run_etl(uploaded_files=None, use_database=False):
    service = ETLService()
    return service.run(uploaded_files, use_database)

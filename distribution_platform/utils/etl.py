import pandas as pd

from distribution_platform.config import paths
from distribution_platform.dashboard.database.repository import (
    load_full_dataset,
    load_provinces,
)
from distribution_platform.models.order import Order
from distribution_platform.utils import data_cleaning, data_loaders, enums
from distribution_platform.utils.coordinates_cache import CoordinateCache
from distribution_platform.utils.data_loaders import (
    load_uploaded_file,
    safe_concat_dataframes,
)
from distribution_platform.utils.geolocator import get_coordinates


class ETLProcessor:
    """
    ETLProcessor handles the Extract, Transform, and Load (ETL) pipeline for processing
    perishable goods distribution data, including loading, cleaning, merging datasets,
    building coordinate caches, and transforming data into Order objects.
    """

    def __init__(self):
        self.paths = paths

        self.df_clientes = None
        self.df_lineas_pedido = None
        self.df_pedidos = None
        self.df_productos = None
        self.df_provincias = None
        self.df_destinos = None

        self.df_final: pd.DataFrame | None = None
        self.coord_cache = CoordinateCache()

    # ----------------------------------------------------------
    # 1) LOAD DATA
    # ----------------------------------------------------------
    def load_raw_data(self):
        """Load raw data from CSV files into the corresponding dataframes."""
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

    def load_from_uploaded_files(self, files_dict):
        """Load data from uploaded files.

        Parameters
        ----------
        files_dict : dict
            Dictionary containing lists of uploaded files with keys:
            'clientes', 'lineas_pedido', 'pedidos', 'productos',
            'provincias', 'destinos'.
        """

        def to_list(v):
            return [] if v is None else (v if isinstance(v, list) else [v])

        def concat(files):
            return safe_concat_dataframes(
                [load_uploaded_file(f) for f in to_list(files)]
            )

        self.df_clientes = concat(files_dict["clientes"])
        self.df_lineas_pedido = concat(files_dict["lineas_pedido"])
        self.df_pedidos = concat(files_dict["pedidos"])
        self.df_productos = concat(files_dict["productos"])
        self.df_provincias = concat(files_dict["provincias"])
        self.df_destinos = concat(files_dict["destinos"])

    def load_from_database(self):
        """Carga ya mergado desde SQL; luego limpiamos y construimos cache."""
        df = load_full_dataset()
        self.df_provincias = load_provinces()

        df = df.rename(
            columns={
                "nombre_completo": "destino",
                "nombre": "producto",
                "cantidad": "cantidad_producto",
                "email": "email_cliente",
            },
            errors="ignore",
        )

        # Normalizar destino (quita "Destino ")
        df["destino"] = (
            df["destino"]
            .astype(str)
            .str.replace("Destino ", "", regex=False)
            .str.strip()
        )

        # No queremos coordenadas en pedidos.csv → ignorar columna si viene de SQL
        df = df.drop(columns=["coordenadas_gps"], errors="ignore")

        # Ordenar y seleccionar columnas finales
        df = df.reindex(
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
                "email_cliente",
            ],
            axis=1,
        )

        df = self.compute_caducidad_fields(df)

        self.df_final = df

        # Construir/actualizar cache en base a provincias
        self.build_coordinates_cache_from_df(self.df_provincias, destino_col="nombre")
        # self.build_coordinates_cache_from_df(self.df_final, destino_col="destino")

    # ----------------------------------------------------------
    # 2) CLEANING (solo CSV)
    # ----------------------------------------------------------
    def normalize_all_column_names(self):
        """Normalize all dataframe column names to snake_case format."""
        self.df_clientes = data_cleaning.to_snake_case(self.df_clientes)
        self.df_lineas_pedido = data_cleaning.to_snake_case(self.df_lineas_pedido)
        self.df_pedidos = data_cleaning.to_snake_case(self.df_pedidos)
        self.df_productos = data_cleaning.to_snake_case(self.df_productos)
        self.df_provincias = data_cleaning.to_snake_case(self.df_provincias)
        self.df_destinos = data_cleaning.to_snake_case(self.df_destinos)

    def clean_numeric_commas(self):
        """Convert numeric columns with comma separators to float format."""
        self.df_destinos["distancia_km"] = (
            self.df_destinos["distancia_km"]
            .astype(str)
            .str.replace(",", ".")
            .astype(float)
        )
        self.df_productos["precio_venta"] = (
            self.df_productos["precio_venta"]
            .astype(str)
            .str.replace(",", ".")
            .astype(float)
        )

    def normalize_destinos_table(self):
        """
        Remove 'Destino ' prefix from the nombre_completo column in the destinations
        table.
        """
        self.df_destinos["nombre_completo"] = (
            self.df_destinos["nombre_completo"]
            .astype(str)
            .str.replace("Destino ", "", regex=False)
            .str.strip()
        )

    # ----------------------------------------------------------
    def merge_datasets(self):
        """Merge all dataframes on common keys to create a final unified dataset."""
        self.df_pedidos = self.df_pedidos.rename(
            columns={"destino_entrega_id": "destino_id"}, errors="raise"
        )

        df_pc = self.df_pedidos.merge(self.df_clientes, on="cliente_id", how="left")
        df_pc = df_pc.drop(columns=["cliente_id", "nombre", "fecha_registro"])

        df_pcd = df_pc.merge(self.df_destinos, on="destino_id", how="left")

        df_lineas = self.df_lineas_pedido.merge(df_pcd, on="pedido_id", how="left")

        df_final = df_lineas.merge(self.df_productos, on="producto_id", how="left")

        df_final = df_final.drop(
            columns=["linea_pedido_id", "producto_id", "destino_id", "coordenadas_gps"],
            errors="ignore",
        )

        df_final = df_final.rename(
            columns={
                "nombre_completo": "destino",
                "nombre": "producto",
                "cantidad": "cantidad_producto",
                "email": "email_cliente",
            }
        )

        # Normalizar destino también aquí por si acaso
        df_final["destino"] = (
            df_final["destino"]
            .astype(str)
            .str.replace("Destino ", "", regex=False)
            .str.strip()
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
                "email_cliente",
            ],
            axis=1,
        )

        df_final = self.compute_caducidad_fields(df_final)

        self.df_final = df_final

    def compute_caducidad_fields(self, df: pd.DataFrame):
        """
        Calcula:
        - dias_totales_caducidad
        - fecha_caducidad_final
        """

        # Convertir fecha
        df["fecha_pedido"] = pd.to_datetime(df["fecha_pedido"], errors="coerce")

        # Convertir numéricos
        df["tiempo_fabricacion_medio"] = pd.to_numeric(
            df["tiempo_fabricacion_medio"], errors="coerce"
        )
        df["caducidad"] = pd.to_numeric(df["caducidad"], errors="coerce")

        # Calcular días totales: 1 día (fabricación empieza mañana) + fabricación + caducidad
        df["dias_totales_caducidad"] = (
            1 + df["tiempo_fabricacion_medio"] + df["caducidad"]
        )

        # Fecha final
        df["fecha_caducidad_final"] = df["fecha_pedido"] + pd.to_timedelta(
            df["dias_totales_caducidad"], unit="D"
        )

        return df

    # ----------------------------------------------------------
    # 4) BUILD COORDINATES CACHE (usa df_provincias)
    # ----------------------------------------------------------
    def build_coordinates_cache_from_df(self, df: pd.DataFrame, destino_col="nombre"):
        """Build coordinates cache without modifying the DataFrame.

        Solo:
        - Obtiene destinos únicos
        - Para cada uno mira el cache
        - Si no existe → llama a geocoder una vez
        - Guarda en coordinates.json
        """
        destinos = df[destino_col].dropna().astype(str).str.strip().unique()

        for destino in destinos:
            if not destino:
                continue

            # Ya existe en cache → no llamamos de nuevo
            if self.coord_cache.get(destino) is not None:
                continue

            coord = get_coordinates(destino)
            self.coord_cache.set(destino, coord)

        self.coord_cache.save()

    def save_processed(self):
        """Save the processed df to a CSV file in the processed data directory."""
        out_path = self.paths.DATA_PROCESSED / "pedidos.csv"
        data_loaders.save_dataframe_to_csv(self.df_final, out_path)

    # ----------------------------------------------------------
    # 6) MAIN PIPELINE
    # ----------------------------------------------------------
    def run(self, uploaded_files=None, use_database=False):
        """
        Run the ETL pipeline to process and merge data from various sources.

        Parameters
        ----------
        uploaded_files : dict, optional
            Dictionary of uploaded files to use as data sources.
            If None, loads from raw CSV files.
        use_database : bool, optional
            If True, loads data from the database instead of files.

        Returns
        -------
        pd.DataFrame
            The final processed DataFrame.
        """
        if use_database:
            self.load_from_database()

        else:
            # CSV (raw o uploaded) → mismo pipeline
            if uploaded_files is not None:
                self.load_from_uploaded_files(uploaded_files)
            else:
                processed_file = self.paths.DATA_PROCESSED / "pedidos.csv"
                if processed_file.exists():
                    return data_loaders.load_data(
                        enums.DataTypesEnum.CSV, processed_file
                    )
                self.load_raw_data()

            self.normalize_all_column_names()
            self.normalize_destinos_table()
            self.clean_numeric_commas()
            self.merge_datasets()

            # Construir/actualizar cache a partir de provincias
            self.build_coordinates_cache_from_df(
                self.df_provincias, destino_col="nombre"
            )

        # Guardar pedidos SIN coordenadas
        self.save_processed()
        return self.df_final

    # ----------------------------------------------------------
    # 7) TRANSFORM TO ORDER OBJECTS
    #    (si Order ya no tiene coordenadas_gps, elimínalo aquí también)
    # ----------------------------------------------------------
    def transform_to_orders(self, df_pedidos: pd.DataFrame):
        """
        Transform a DataFrame of pedidos into grouped lists of Order objects.
        """

        orders_grouped = []
        grouped = df_pedidos.sort_values(by="dias_totales_caducidad").groupby(
            "pedido_id"
        )

        for _, group in grouped:
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
                    email_cliente=row["email_cliente"],
                    dias_totales_caducidad=row["dias_totales_caducidad"],
                    fecha_caducidad_final=row["fecha_caducidad_final"],
                )
                order_lines.append(order_line)

            orders_grouped.append(order_lines)

        return orders_grouped

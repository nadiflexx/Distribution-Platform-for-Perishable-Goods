from distribution_platform.utils.etl import ETLProcessor


def run_etl(uploaded_files=None, use_database=False):
    """Run the ETL preprocessing pipeline.

    Initializes and executes the ETL processor to transform and load data.
    """
    etl = ETLProcessor()
    df_pedidos = etl.run(uploaded_files=uploaded_files, use_database=use_database)

    print(df_pedidos.columns.tolist())

    orders = etl.transform_to_orders(df_pedidos)

    return orders

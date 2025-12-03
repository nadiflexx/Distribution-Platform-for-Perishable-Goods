from distribution_platform.utils.etl import ETLProcessor


def run_etl(uploaded_files=None):
    """Run the ETL preprocessing pipeline.

    Initializes and executes the ETL processor to transform and load data.
    """
    etl = ETLProcessor()
    df_pedidos = etl.run(uploaded_files=uploaded_files)

    print(df_pedidos.columns.tolist())

    # Transform into Object orders
    orders = etl.transform_to_orders(df_pedidos)

    print(f"ETL process completed. Processed {len(orders)} orders.")
    return orders

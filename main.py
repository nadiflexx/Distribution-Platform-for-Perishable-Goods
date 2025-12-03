from distribution_platform.pipelines import etl_pipeline


def main():
    """Run the ETL pipeline for preprocessing perishable goods distribution data."""
    orders_list = etl_pipeline.run_etl()

    print(f"ETL process completed. Processed {len(orders_list)} orders.")


if __name__ == "__main__":
    main()

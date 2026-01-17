"""
Export Service.
Handles data transformation from Optimization Results to Pandas DataFrames/CSVs.
Formats data for European Power BI (semicolon separator, comma decimals).
"""

import pandas as pd


class ExportService:
    @staticmethod
    def _format_floats(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts all float columns to string with comma decimal separator
        to ensure compatibility with European Excel/Power BI.
        """
        # Copia para no mutar el original
        df_formatted = df.copy()

        # Identificar columnas flotantes
        float_cols = df_formatted.select_dtypes(include=["float", "float64"]).columns

        for col in float_cols:
            # Redondear a 2 decimales y reemplazar punto por coma
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x:.2f}".replace(".", ",") if pd.notnull(x) else ""
            )

        return df_formatted

    @staticmethod
    def generate_financials_df(result: dict) -> pd.DataFrame:
        """Generates High-Level Financial KPI Table."""
        data = []
        trucks = [
            v
            for k, v in result["resultados_detallados"].items()
            if k != "pedidos_no_entregables"
        ]

        for t in trucks:
            weight = sum(p.cantidad_producto for p in t.lista_pedidos_ordenada)
            revenue = sum(p.precio_venta for p in t.lista_pedidos_ordenada)

            data.append(
                {
                    "Truck_ID": f"UNIT-{t.camion_id:03d}",
                    "Total_Stops": len(t.lista_pedidos_ordenada),
                    "Total_Distance_KM": t.distancia_total_km,
                    "Total_Weight_KG": weight,
                    "Total_Revenue_EUR": revenue,
                    "Fuel_Consumed_L": t.consumo_litros,
                    "Fuel_Cost_EUR": t.coste_combustible,
                    "Driver_Cost_EUR": t.coste_conductor,
                    "Total_Op_Cost_EUR": t.coste_total_ruta,
                    "Net_Profit_EUR": t.beneficio_neto,
                    "Profit_Margin_Percent": (t.beneficio_neto / revenue * 100)
                    if revenue > 0
                    else 0,
                    "Cost_Per_KM": (t.coste_total_ruta / t.distancia_total_km)
                    if t.distancia_total_km > 0
                    else 0,
                }
            )

        df = pd.DataFrame(data)
        return ExportService._format_floats(df)

    @staticmethod
    def generate_detailed_routes_df(result: dict) -> pd.DataFrame:
        """Generates Stop-by-Stop Detailed Route Plan."""
        data = []
        trucks = [
            v
            for k, v in result["resultados_detallados"].items()
            if k != "pedidos_no_entregables"
        ]

        for t in trucks:
            coords = t.ruta_coordenadas
            for i, order in enumerate(t.lista_pedidos_ordenada):
                eta = t.tiempos_llegada[i] if i < len(t.tiempos_llegada) else "N/A"

                lat, lon = 0.0, 0.0
                if i + 1 < len(coords):
                    lat, lon = coords[i + 1]

                data.append(
                    {
                        "Truck_ID": f"UNIT-{t.camion_id:03d}",
                        "Stop_Sequence": i + 1,
                        "Order_ID": order.pedido_id,
                        "Destination_City": order.destino,
                        "Latitude": lat,
                        "Longitude": lon,
                        "Weight_KG": float(order.cantidad_producto),
                        "ETA_Hours": eta,  # ETA suele ser string "HH:MM", no lo tocamos
                        "Client_Email": getattr(order, "email_cliente", "N/A"),
                        "Priority": getattr(order, "prioridad", "Normal"),
                        "Order_Value_EUR": float(getattr(order, "precio_venta", 0)),
                    }
                )

        df = pd.DataFrame(data)
        return ExportService._format_floats(df)

    @staticmethod
    def generate_failed_orders_df(result: dict) -> pd.DataFrame:
        """Generates list of unassigned orders."""
        data = []
        if "pedidos_no_entregables" in result:
            if isinstance(result["pedidos_no_entregables"], list):
                for order in result["pedidos_no_entregables"]:
                    data.append(
                        {
                            "Order_ID": order.pedido_id,
                            "Destination": order.destino,
                            "Reason": "Impossible Destination / No Road Access",
                            "Weight_KG": float(order.cantidad_producto),
                            "Value_EUR": float(getattr(order, "precio_venta", 0)),
                        }
                    )
            elif isinstance(result["pedidos_no_entregables"], pd.DataFrame):
                df = result["pedidos_no_entregables"]
                return ExportService._format_floats(df)

        df = pd.DataFrame(data)
        return ExportService._format_floats(df)

"""
Export Hub Component.
Isolates the UI logic for downloading reports.
"""

import pandas as pd
import streamlit as st

from distribution_platform.app.services.export_service import ExportService


class ExportHub:
    @staticmethod
    def render(result: dict):
        """Renders the Export Popover in the UI."""

        with st.popover("📥 EXPORT DATA CENTER", width="stretch"):
            st.markdown("### 📊 Exports (EU Format)")
            st.caption("Structured datasets to download for external analysis")

            # 1. Fleet Financials
            df_financials = ExportService.generate_financials_df(result)
            ExportHub._download_btn(
                df_financials, "fleet_financials.csv", "💰 Fleet Financials (KPIs)"
            )

            # 2. Detailed Route Plan
            df_routes = ExportService.generate_detailed_routes_df(result)
            ExportHub._download_btn(
                df_routes, "detailed_route_plan.csv", "📍 Detailed Route Plan"
            )

            # 3. Unassigned Orders
            if "pedidos_no_entregables" in result and result["pedidos_no_entregables"]:
                df_failed = ExportService.generate_failed_orders_df(result)
                ExportHub._download_btn(
                    df_failed, "unassigned_orders.csv", "🚫 Unassigned Orders"
                )

    @staticmethod
    def _download_btn(df: pd.DataFrame, filename: str, label: str):
        """Helper to create download buttons with correct encoding and separator."""
        csv = df.to_csv(index=False, sep=";").encode("utf-8-sig")

        st.download_button(
            label=label,
            data=csv,
            file_name=filename,
            mime="text/csv",
            width="stretch",
        )

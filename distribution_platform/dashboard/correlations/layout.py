import io
import logging

import pandas as pd
import plotly.express as px
import streamlit as st

from .bridge_loader import clean_dataframe, load_generic_data
from .registry import PLOT_TYPES
from .visualizations import generate_plot
from config.config_dashboard import DashboardConfig
from ..utils.correaltions import (
    correlation_matrix,
    correlation_pvalue_matrix,
    correlation_with_pvalue,
)
from ..utils.enums import CorrelationsEnums, DataTypesEnum

logger = logging.getLogger(__name__)


def show_dashboard(config: DashboardConfig | None):
    """
    Shows the dashboard and sets all the graphics were desired.

    Parameters
    ----------
    config : DashboardConfig | None
        Checks the configuration process for the dashboard for data and titles.
    """
    if config is None:
        logger.warning(
            "Dashboard config is None — cannot generate personalized dashboard."
        )
        raise ValueError("DashboardConfig is None — dashboard cannot be generated.")

    st.set_page_config(page_title=config.title, layout=config.layout)
    st.title(config.title)

    # Sidebar: carga de datos
    st.sidebar.header("Datos")
    uploaded = st.sidebar.file_uploader(
        "📂 Subir archivo", type=["csv", "json", "xlsx"]
    )
    mode_map = {
        "csv": DataTypesEnum.CSV,
        "json": DataTypesEnum.JSON,
        "xlsx": DataTypesEnum.EXCEL,
    }

    if uploaded:
        ext = uploaded.name.split(".")[-1]
        buffer = io.BytesIO(uploaded.read())
        data = load_generic_data(mode=mode_map.get(ext, DataTypesEnum.CSV), path=buffer)
    elif config.default_data_path:
        data = load_generic_data(mode=DataTypesEnum.CSV, path=config.default_data_path)
    else:
        st.warning("Sube un archivo para continuar.")
        return

    data = clean_dataframe(data)

    # Preview
    st.subheader("📋 Vista previa")
    st.dataframe(data.head())

    # Selección de columnas
    cols = data.columns.tolist()
    x_col = st.selectbox("Eje X", cols)
    y_col = st.selectbox("Eje Y", ["(ninguno)"] + cols)
    y_col = None if y_col == "(ninguno)" else y_col
    plot_type = st.selectbox("Tipo de gráfico", list(config_plot_types(data)))

    # Renderizado
    if st.button("Generar gráfico"):
        fig = generate_plot(data, plot_type, x_col, y_col)
        st.plotly_chart(fig, width="stretch")


def config_plot_types(df: pd.DataFrame):
    """
    Returns the type of valid graphics according to the DataFrame content.

    Paramters
    ---------
    df : pd.DataFrame
        Data to show and config plots.
    """
    numeric_cols = df.select_dtypes(include=["number"]).columns
    categorical_cols = df.select_dtypes(exclude=["number"]).columns

    for name in PLOT_TYPES:
        # Ejemplo de lógica básica:
        if name in {"Line", "Scatter", "Box"} and len(numeric_cols) == 0:
            continue  # necesita columnas numéricas
        if name in {"Pie", "Bar"} and len(categorical_cols) == 0:
            continue  # necesita categorías
        yield name


def show_correlation_dashboard(config: DashboardConfig | None):
    """
    Displays a dedicated dashboard for correlation analysis.

    Parameters
    ----------
    config : DashboardConfig | None
        Dashboard configuration object.
    """
    if config is None:
        logger.warning("Dashboard config is None — cannot generate dashboard.")
        raise ValueError("DashboardConfig is required.")

    st.set_page_config(page_title=config.title, layout=config.layout)
    st.title(config.title)

    # Sidebar: carga de datos
    st.sidebar.header("📂 Load data")
    uploaded = st.sidebar.file_uploader("Upload file", type=["csv", "json", "xlsx"])
    mode_map = {
        "csv": DataTypesEnum.CSV,
        "json": DataTypesEnum.JSON,
        "xlsx": DataTypesEnum.EXCEL,
    }

    # Load
    if uploaded:
        ext = uploaded.name.split(".")[-1]
        buffer = io.BytesIO(uploaded.read())
        data = load_generic_data(mode=mode_map.get(ext, DataTypesEnum.CSV), path=buffer)
    elif config.default_data_path:
        data = load_generic_data(mode=DataTypesEnum.CSV, path=config.default_data_path)
    else:
        st.warning("Upload a dataset to continue.")
        return

    data = clean_dataframe(data)

    st.subheader("📋 Data Preview")
    st.dataframe(data.head())

    numeric_cols = data.select_dtypes(include=["number"]).columns.tolist()

    if len(numeric_cols) < 2:
        st.error("Dataset must contain at least 2 numeric columns.")
        return

    # --- TAB NAV ---
    tab1, tab2 = st.tabs(["🔵 Full Correlation Matrix", "🟢 Compare Two Variables"])

    # TAB 1 --------
    with tab1:
        st.subheader("🔵 Full Correlation Matrix")

        method = st.selectbox(
            "Correlation method",
            list(CorrelationsEnums),
            format_func=lambda x: x.name.capitalize(),
        )

        if st.button("Compute full matrix"):
            corr = correlation_matrix(
                data,
                metodo=method,
                columnas=numeric_cols,
                heatmap=False,
            )

            pvals = correlation_pvalue_matrix(
                data[numeric_cols],
                method=method,
            )

            st.write("### 🔵 Correlation matrix")
            fig1 = px.imshow(
                corr,
                text_auto=True,
                color_continuous_scale="RdBu_r",
                title=f"Correlation Matrix ({method.value})",
            )
            st.plotly_chart(fig1,  width="stretch")

            st.write("### 🧪 P-value matrix (significance)")
            fig2 = px.imshow(
                pvals,
                text_auto=True,
                color_continuous_scale="Viridis",
                title=f"P-value Matrix ({method.value})",
            )
            st.plotly_chart(fig2,  width="stretch")

            st.info("""
    Interpretación:
    - P-value < 0.05 → correlación estadísticamente significativa
    - P-value < 0.01 → muy significativa
    - P-value ≥ 0.05 → la correlación puede ser debida al azar
    """)

    # TAB 2 --------
    with tab2:
        st.subheader("🟢 Compare Two Variables")

        col1 = st.selectbox("Column X", numeric_cols)
        col2 = st.selectbox("Column Y", numeric_cols)

        method2 = st.selectbox(
            "Correlation method (pairwise)",
            list(CorrelationsEnums),
            format_func=lambda x: x.name.capitalize(),
        )

        if st.button("Compute pair correlation"):
            corr, p = correlation_with_pvalue(data, col1, col2, method=method2)

            st.write(f"### Correlation = **{corr:.4f}**")
            st.write(f"### P-value = **{p:.4f}**")

            interpretation = "Significant ✔" if p < 0.05 else "Not significant ❌"
            st.write(f"### Interpretation: **{interpretation}**")

            fig = px.scatter(
                data,
                x=col1,
                y=col2,
                trendline="ols",
                title=f"{method2.value.capitalize()} correlation: {corr:.4f}",
            )
            st.plotly_chart(fig,  width="stretch")

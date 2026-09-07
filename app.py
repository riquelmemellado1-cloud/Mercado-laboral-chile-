import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import StringIO

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Mercado Laboral en Chile",
    page_icon="🇨🇱",
    layout="wide"
)

ANIOS = [2022, 2023, 2024, 2025, 2026]

API_DESOCUPACION = (
    "https://sdmx.ine.gob.cl/rest/data/"
    "CL01,DF_TDES_SEXO,1.0?format=csv"
)

API_OCUPACION = (
    "https://sdmx.ine.gob.cl/rest/data/"
    "CL01,DF_TOCU_SEXO,1.0?format=csv"
)

REGIONES = {
    "01": "Arica y Parinacota",
    "02": "Tarapacá",
    "03": "Antofagasta",
    "04": "Atacama",
    "05": "Coquimbo",
    "06": "Valparaíso",
    "07": "Metropolitana",
    "08": "O'Higgins",
    "09": "Maule",
    "10": "Ñuble",
    "11": "Biobío",
    "12": "La Araucanía",
    "13": "Los Ríos",
    "14": "Los Lagos",
    "15": "Aysén",
    "16": "Magallanes",
    "_T": "Chile"
}


# ============================================================
# TÍTULO
# ============================================================

st.title("🇨🇱 Mercado Laboral en Chile")

st.subheader(
    "Análisis comparativo 2022–2026"
)

st.write(
    """
    Aplicación interactiva desarrollada con datos oficiales
    del Instituto Nacional de Estadísticas (INE).
    
    Se analizan las tasas de ocupación y desocupación
    correspondientes al período móvil mayo–julio de cada
    año entre 2022 y 2026.
    """
)

st.divider()


# ============================================================
# FUNCIÓN PARA DESCARGAR DATOS
# ============================================================

@st.cache_data(ttl=3600)
def descargar_datos(url):

    respuesta = requests.get(
        url,
        timeout=30
    )

    respuesta.raise_for_status()

    return pd.read_csv(
        StringIO(respuesta.text)
    )


# ============================================================
# OBTENER DATOS
# ============================================================

with st.spinner("Obteniendo datos oficiales del INE..."):

    try:

        df_des = descargar_datos(
            API_DESOCUPACION
        )

        df_ocu = descargar_datos(
            API_OCUPACION
        )

    except Exception as error:

        st.error(
            "❌ No fue posible obtener los datos desde la API del INE."
        )

        st.exception(error)

        st.stop()


# ============================================================
# PROCESAR DESOCUPACIÓN
# ============================================================

try:

    des = df_des[
        (df_des["SEXO"] == "AS") &
        (df_des["TIME_PERIOD"].str.contains(
            "05-01/P3M",
            na=False
        ))
    ].copy()

    des["Año"] = (
        des["TIME_PERIOD"]
        .str[:4]
        .astype(int)
    )

    des = des[
        des["Año"].isin(ANIOS)
    ]

    des["Región"] = (
        des["AREA_REF"].map(REGIONES)
    )

    des = des[
        ["Región", "Año", "OBS_VALUE"]
    ].rename(
        columns={
            "OBS_VALUE": "Desocupación"
        }
    )

    # ========================================================
    # PROCESAR OCUPACIÓN
    # ========================================================

    ocu = df_ocu[
        (df_ocu["SEXO"] == "AS") &
        (df_ocu["TIME_PERIOD"].str.contains(
            "05-01/P3M",
            na=False
        ))
    ].copy()

    ocu["Año"] = (
        ocu["TIME_PERIOD"]
        .str[:4]
        .astype(int)
    )

    ocu = ocu[
        ocu["Año"].isin(ANIOS)
    ]

    ocu["Región"] = (
        ocu["AREA_REF"].map(REGIONES)
    )

    ocu = ocu[
        ["Región", "Año", "OBS_VALUE"]
    ].rename(
        columns={
            "OBS_VALUE": "Ocupación"
        }
    )

    # ========================================================
    # UNIR LOS DATOS
    # ========================================================

    df = pd.merge(
        des,
        ocu,
        on=["Región", "Año"],
        how="inner"
    )

    df["Desocupación"] = pd.to_numeric(
        df["Desocupación"],
        errors="coerce"
    )

    df["Ocupación"] = pd.to_numeric(
        df["Ocupación"],
        errors="coerce"
    )

    df = df.dropna()

    df = df.sort_values(
        ["Región", "Año"]
    )

except Exception as error:

    st.error(
        "❌ Ocurrió un error al procesar los datos."
    )

    st.exception(error)

    st.stop()


# ============================================================
# COMPROBACIÓN
# ============================================================

if df.empty:

    st.error(
        "La API respondió, pero no se encontraron datos "
        "para el período seleccionado."
    )

    st.stop()


# ============================================================
# FILTROS
# ============================================================

st.sidebar.header("⚙️ Filtros")

indicador = st.sidebar.selectbox(
    "Indicador",
    [
        "Desocupación",
        "Ocupación"
    ]
)

anio = st.sidebar.selectbox(
    "Año",
    ANIOS,
    index=len(ANIOS) - 1
)

regiones = sorted(
    [
        r
        for r in df["Región"].dropna().unique()
        if r != "Chile"
    ]
)

region = st.sidebar.selectbox(
    "Región",
    ["Chile"] + regiones
)


# ============================================================
# DATOS NACIONALES
# ============================================================

dato_chile = df[
    (df["Región"] == "Chile") &
    (df["Año"] == anio)
]

if dato_chile.empty:

    st.error(
        "No se encontró información nacional para el año seleccionado."
    )

    st.stop()


# ============================================================
# INDICADORES
# ============================================================

st.header("📊 Indicadores nacionales")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Desocupación",
    f"{dato_chile['Desocupación'].iloc[0]:.2f}%"
)

col2.metric(
    "Ocupación",
    f"{dato_chile['Ocupación'].iloc[0]:.2f}%"
)

col3.metric(
    "Período analizado",
    "Mayo–Julio"
)


# ============================================================
# EVOLUCIÓN NACIONAL
# ============================================================

st.header(
    f"📈 Evolución nacional de {indicador.lower()}"
)

df_chile = df[
    df["Región"] == "Chile"
].sort_values("Año")

fig, ax = plt.subplots(
    figsize=(10, 5)
)

ax.plot(
    df_chile["Año"].astype(int),
    df_chile[indicador].astype(float),
    marker="o",
    linewidth=2
)

ax.set_xlabel("Año")
ax.set_ylabel("Porcentaje (%)")
ax.set_xticks(ANIOS)

ax.set_title(
    f"Evolución nacional de la tasa de {indicador.lower()}"
)

ax.grid(
    True,
    alpha=0.3
)

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# ============================================================
# COMPARACIÓN REGIONAL
# ============================================================

st.header(
    f"🗺️ Comparación regional — {anio}"
)

df_regiones = df[
    (df["Año"] == anio) &
    (df["Región"] != "Chile")
].sort_values(
    indicador,
    ascending=True
)

fig, ax = plt.subplots(
    figsize=(11, 7)
)

ax.barh(
    df_regiones["Región"],
    df_regiones[indicador]
)

ax.set_xlabel(
    "Porcentaje (%)"
)

ax.set_ylabel(
    "Región"
)

ax.set_title(
    f"Tasa de {indicador.lower()} por región — {anio}"
)

ax.grid(
    axis="x",
    alpha=0.3
)

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# ============================================================
# REGIÓN SELECCIONADA
# ============================================================

st.header(
    f"📍 Resultado de {region}"
)

dato_region = df[
    (df["Región"] == region) &
    (df["Año"] == anio)
]

if not dato_region.empty:

    col4, col5 = st.columns(2)

    col4.metric(
        "Desocupación",
        f"{dato_region['Desocupación'].iloc[0]:.2f}%"
    )

    col5.metric(
        "Ocupación",
        f"{dato_region['Ocupación'].iloc[0]:.2f}%"
    )


# ============================================================
# TABLA
# ============================================================

st.header(
    "📋 Datos utilizados"
)

tabla = df[
    df["Año"] == anio
][
    [
        "Región",
        "Desocupación",
        "Ocupación"
    ]
].sort_values(
    "Desocupación",
    ascending=False
)

st.dataframe(
    tabla,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# FUENTE
# ============================================================

st.divider()

st.caption(
    "Fuente: Instituto Nacional de Estadísticas (INE), "
    "Encuesta Nacional de Empleo (ENE). "
    "Datos obtenidos mediante API REST."
)

st.caption(
    "Período móvil mayo–julio | 2022–2026"
)

st.caption(
    "Elaboración propia — Taller de Programación I, Solemne II."
)

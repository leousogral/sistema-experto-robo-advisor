import json
import pandas as pd
import streamlit as st

from motor_experto import ejecutar_motor


st.set_page_config(
    page_title="Robo-Advisor Experto",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Robo-Advisor basado en Sistema Experto")
st.caption(
    "MVP académico con Streamlit + Experta. "
    "Motor determinístico, explicable y con traza de reglas."
)

st.warning(
    "Prototipo académico. No constituye asesoramiento financiero ni valida en tiempo real "
    "la vigencia regulatoria de instrumentos. El catálogo debe ser mantenido por un administrador/compliance."
)

with st.sidebar:
    st.header("Perfil del inversor")

    capital = st.number_input(
        "Monto a invertir",
        min_value=1.0,
        value=1_000_000.0,
        step=10_000.0,
    )

    moneda = st.selectbox("Moneda base", ["ARS", "USD"])

    horizonte = st.slider(
        "Horizonte temporal (meses)",
        min_value=1,
        max_value=120,
        value=24,
    )

    objetivo_label = st.selectbox(
        "Objetivo de inversión",
        [
            "Preservación de capital",
            "Renta periódica",
            "Crecimiento de capital",
        ],
    )
    objetivo_map = {
        "Preservación de capital": "PRESERVACION",
        "Renta periódica": "RENTA",
        "Crecimiento de capital": "CRECIMIENTO",
    }

    tolerancia = st.slider(
        "Tolerancia máxima a pérdida temporal (%)",
        min_value=0,
        max_value=50,
        value=10,
    )

    liquidez = st.slider(
        "Liquidez mínima requerida en 24/48 h (%)",
        min_value=0,
        max_value=100,
        value=20,
    )

st.subheader("Contexto de mercado")
c1, c2, c3 = st.columns(3)

with c1:
    tasa = st.number_input(
        "Tasa de referencia anual (%)",
        min_value=0.0,
        max_value=300.0,
        value=35.0,
        step=0.5,
    )
    inflacion = st.number_input(
        "Inflación esperada anual (%)",
        min_value=0.0,
        max_value=500.0,
        value=45.0,
        step=0.5,
    )

with c2:
    tendencia_fx_label = st.selectbox(
        "Tendencia cambiaria",
        ["Estable", "Alcista", "Bajista"],
    )
    fx_map = {
        "Estable": "ESTABLE",
        "Alcista": "ALCISTA",
        "Bajista": "BAJISTA",
    }

    volatilidad = st.slider(
        "Índice de volatilidad del escenario (0-100)",
        min_value=0,
        max_value=100,
        value=35,
    )

with c3:
    ciclo_label = st.selectbox(
        "Ciclo macroeconómico",
        ["Expansión", "Desaceleración", "Recesión"],
    )
    ciclo_map = {
        "Expansión": "EXPANSION",
        "Desaceleración": "DESACELERACION",
        "Recesión": "RECESION",
    }

    antiguedad = st.number_input(
        "Antigüedad de los datos de mercado (horas)",
        min_value=0,
        max_value=168,
        value=2,
        step=1,
    )


def construir_entrada():
    inv = {
        "capital": float(capital),
        "moneda": moneda,
        "horizonte_meses": int(horizonte),
        "objetivo": objetivo_map[objetivo_label],
        "tolerancia_perdida": float(tolerancia),
        "liquidez_minima": float(liquidez),
    }

    mercado = {
        "tasa_referencia": float(tasa),
        "inflacion_esperada": float(inflacion),
        "tendencia_fx": fx_map[tendencia_fx_label],
        "volatilidad": float(volatilidad),
        "ciclo": ciclo_map[ciclo_label],
        "antiguedad_horas": int(antiguedad),
    }

    return inv, mercado


if st.button("Ejecutar sistema experto", type="primary", use_container_width=True):
    inv, mercado = construir_entrada()
    resultado = ejecutar_motor(inv, mercado)

    st.session_state["resultado"] = resultado
    st.session_state["entrada"] = {
        "inversor": inv,
        "mercado": mercado,
    }

if "resultado" in st.session_state:
    resultado = st.session_state["resultado"]
    entrada = st.session_state["entrada"]

    st.divider()

    if resultado["estado"] == "RECOMENDACION_EXITOSA":
        st.success("RECOMENDACION_EXITOSA")

        m1, m2, m3 = st.columns(3)
        m1.metric("Perfil consolidado", resultado["perfil_riesgo"])
        m2.metric("Capital", f'{entrada["inversor"]["capital"]:,.2f} {entrada["inversor"]["moneda"]}')
        m3.metric(
            "Total asignado",
            f'{sum(resultado["asset_allocation"].values()):.2f}%',
        )

        st.subheader("Asset Allocation")
        df_alloc = pd.DataFrame(
            [
                {"Clase de activo": k, "Porcentaje": v}
                for k, v in resultado["asset_allocation"].items()
            ]
        )
        st.dataframe(df_alloc, use_container_width=True, hide_index=True)
        st.bar_chart(df_alloc.set_index("Clase de activo")["Porcentaje"])

        st.subheader("Canasta sugerida")
        st.dataframe(
            pd.DataFrame(resultado["canasta_instrumentos"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.error("DERIVADO_ASESOR_MANUAL")
        st.write(
            "El motor detectó una condición que impide emitir una recomendación automática."
        )
        if resultado["errores"]:
            st.dataframe(
                pd.DataFrame(resultado["errores"]),
                use_container_width=True,
                hide_index=True,
            )

    tab1, tab2, tab3 = st.tabs(
        ["Explicabilidad", "Fired rules", "JSON"]
    )

    with tab1:
        for i, texto in enumerate(resultado["justificaciones"], start=1):
            st.write(f"{i}. {texto}")

    with tab2:
        st.write("**Reglas disparadas:**")
        for r in resultado["reglas_disparadas"]:
            st.code(r)

        with st.expander("Ver catálogo de reglas evaluadas"):
            for r in resultado["reglas_evaluadas"]:
                st.write(f"- {r}")

    with tab3:
        st.json(
            {
                "entrada": entrada,
                "salida": resultado,
            },
            expanded=False,
        )

        payload = json.dumps(
            {
                "entrada": entrada,
                "salida": resultado,
            },
            ensure_ascii=False,
            indent=2,
        )

        st.download_button(
            "Descargar resultado JSON",
            data=payload,
            file_name="resultado_robo_advisor.json",
            mime="application/json",
        )

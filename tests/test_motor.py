from motor_experto import ejecutar_motor


def mercado_base(**kwargs):
    base = {
        "tasa_referencia": 35.0,
        "inflacion_esperada": 45.0,
        "tendencia_fx": "ESTABLE",
        "volatilidad": 30.0,
        "ciclo": "EXPANSION",
        "antiguedad_horas": 2,
    }
    base.update(kwargs)
    return base


def inversor_base(**kwargs):
    base = {
        "capital": 1_000_000.0,
        "moneda": "ARS",
        "horizonte_meses": 24,
        "objetivo": "RENTA",
        "tolerancia_perdida": 10.0,
        "liquidez_minima": 20.0,
    }
    base.update(kwargs)
    return base


def test_suma_100():
    r = ejecutar_motor(inversor_base(), mercado_base())
    assert r["estado"] == "RECOMENDACION_EXITOSA"
    assert round(sum(r["asset_allocation"].values()), 2) == 100.0


def test_conservador_sin_renta_variable():
    r = ejecutar_motor(
        inversor_base(
            tolerancia_perdida=0,
            objetivo="PRESERVACION",
            horizonte_meses=6,
        ),
        mercado_base(),
    )
    assert r["estado"] == "RECOMENDACION_EXITOSA"
    assert r["perfil_riesgo"] == "CONSERVADOR"
    assert r["asset_allocation"]["RENTA_VARIABLE"] == 0.0


def test_contradiccion_deriva_manual():
    r = ejecutar_motor(
        inversor_base(
            tolerancia_perdida=0,
            objetivo="CRECIMIENTO",
        ),
        mercado_base(),
    )
    assert r["estado"] == "DERIVADO_ASESOR_MANUAL"


def test_volatilidad_extrema_deriva_manual():
    r = ejecutar_motor(
        inversor_base(),
        mercado_base(volatilidad=90),
    )
    assert r["estado"] == "DERIVADO_ASESOR_MANUAL"


def test_determinismo():
    inv = inversor_base()
    mkt = mercado_base(tendencia_fx="ALCISTA", volatilidad=55)

    r1 = ejecutar_motor(inv, mkt)
    r2 = ejecutar_motor(inv, mkt)

    assert r1["asset_allocation"] == r2["asset_allocation"]
    assert r1["reglas_disparadas"] == r2["reglas_disparadas"]

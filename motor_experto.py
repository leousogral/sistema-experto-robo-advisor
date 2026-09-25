from __future__ import annotations

from typing import Any, Dict, List, Optional

# Compatibilidad para Experta/frozendict en versiones modernas de Python.
import collections
import collections.abc
if not hasattr(collections, "Mapping"):
    collections.Mapping = collections.abc.Mapping
if not hasattr(collections, "MutableMapping"):
    collections.MutableMapping = collections.abc.MutableMapping
if not hasattr(collections, "Sequence"):
    collections.Sequence = collections.abc.Sequence

from experta import ( # type: ignore
    Fact,
    KnowledgeEngine,
    Rule,
    MATCH,
    TEST,
    AS,
    NOT,
)

from catalogo import seleccionar_canasta


CLASES = ("RF_INFLACION", "RF_DOLAR", "RENTA_VARIABLE", "LIQUIDEZ")

REGLAS_DISPONIBLES = [
    "R01_VALIDACION_BASICA",
    "R02_DATOS_MERCADO_VENCIDOS",
    "R03_VOLATILIDAD_EXTREMA",
    "R04_CONTRADICCION_RIESGO_OBJETIVO",
    "R05_CONTRADICCION_HORIZONTE_OBJETIVO",
    "R10_CLASIFICAR_PERFIL",
    "R20_BASE_CONSERVADOR",
    "R21_BASE_MODERADO",
    "R22_BASE_AGRESIVO",
    "R30_INFLACION_SUPERA_TASA",
    "R31_TENDENCIA_CAMBIARIA_ALCISTA",
    "R32_VOLATILIDAD_ALTA",
    "R33_CICLO_RECESIVO",
    "R40_FINALIZAR_CARTERA",
]


class Inversor(Fact):
    """Datos del inversor."""


class Mercado(Fact):
    """Datos del mercado."""


class Perfil(Fact):
    """Perfil de riesgo consolidado."""


class Stop(Fact):
    """Impide continuar la inferencia automática."""


class BaseAsignada(Fact):
    """Marca que ya existe una cartera base."""


class RoboAdvisorEngine(KnowledgeEngine):
    """
    Motor determinístico de reglas para un MVP académico.
    No ejecuta órdenes ni consulta cotizaciones en tiempo real.
    """

    def __init__(self):
        super().__init__()
        self.estado = "SIN_EJECUTAR"
        self.perfil: Optional[str] = None
        self.asignacion: Dict[str, float] = {k: 0.0 for k in CLASES}
        self.reglas_disparadas: List[str] = []
        self.justificaciones: List[str] = []
        self.errores: List[Dict[str, str]] = []
        self.canasta: List[Dict[str, Any]] = []

    def registrar(self, codigo: str, mensaje: str):
        self.reglas_disparadas.append(codigo)
        self.justificaciones.append(mensaje)

    def derivar(self, codigo_error: str, mensaje: str, regla: str):
        self.estado = "DERIVADO_ASESOR_MANUAL"
        self.errores.append({"codigo": codigo_error, "mensaje": mensaje})
        self.registrar(regla, mensaje)
        self.declare(Stop(motivo=codigo_error))

    @Rule(
        AS.inv << Inversor(
            capital=MATCH.capital,
            horizonte_meses=MATCH.h,
            tolerancia_perdida=MATCH.tol,
            liquidez_minima=MATCH.liq,
        ),
        salience=100,
    )
    def validar_basicos(self, capital, h, tol, liq, inv):
        errores = []
        if capital is None or float(capital) <= 0:
            errores.append(("ERR_CAPITAL_INVALIDO", "El capital debe ser mayor que cero."))
        if h is None or int(h) <= 0:
            errores.append(("ERR_HORIZONTE_INVALIDO", "El horizonte debe ser mayor que cero meses."))
        if tol is None or not (0 <= float(tol) <= 100):
            errores.append(("ERR_TOLERANCIA_INVALIDA", "La tolerancia a la pérdida debe estar entre 0% y 100%."))
        if liq is None or not (0 <= float(liq) <= 100):
            errores.append(("ERR_LIQUIDEZ_INVALIDA", "La liquidez mínima debe estar entre 0% y 100%."))

        if errores:
            for codigo, msg in errores:
                self.errores.append({"codigo": codigo, "mensaje": msg})
            self.estado = "DERIVADO_ASESOR_MANUAL"
            self.registrar("R01_VALIDACION_BASICA", "Se detectaron datos obligatorios inválidos.")
            self.declare(Stop(motivo="ERR_DATOS_ENTRADA"))

    @Rule(
        Mercado(antiguedad_horas=MATCH.age),
        TEST(lambda age: float(age) > 24),
        NOT(Stop()),
        salience=95,
    )
    def mercado_vencido(self, age):
        self.derivar(
            "ERR_DATOS_MERCADO_NO_DISPONIBLES",
            f"Los indicadores de mercado tienen {age} horas de antigüedad y superan la ventana permitida de 24 horas.",
            "R02_DATOS_MERCADO_VENCIDOS",
        )

    @Rule(
        Mercado(volatilidad=MATCH.vol),
        TEST(lambda vol: float(vol) >= 80),
        NOT(Stop()),
        salience=94,
    )
    def volatilidad_extrema(self, vol):
        self.derivar(
            "ERR_VOLATILIDAD_EXTREMA_MERCADO",
            f"La volatilidad informada ({vol}) se considera extrema para este MVP y requiere revisión humana.",
            "R03_VOLATILIDAD_EXTREMA",
        )

    @Rule(
        Inversor(tolerancia_perdida=MATCH.tol, objetivo="CRECIMIENTO"),
        TEST(lambda tol: float(tol) == 0),
        NOT(Stop()),
        salience=93,
    )
    def contradiccion_riesgo_objetivo(self, tol):
        self.derivar(
            "ERR_INCONSISTENCIA_PERFIL_HORIZONTE",
            "Existe una contradicción entre tolerancia nula a pérdidas y objetivo de crecimiento de capital.",
            "R04_CONTRADICCION_RIESGO_OBJETIVO",
        )

    @Rule(
        Inversor(horizonte_meses=MATCH.h, objetivo="CRECIMIENTO"),
        TEST(lambda h: int(h) < 3),
        NOT(Stop()),
        salience=92,
    )
    def contradiccion_horizonte_objetivo(self, h):
        self.derivar(
            "ERR_INCONSISTENCIA_PERFIL_HORIZONTE",
            "Un horizonte menor a 3 meses es incompatible con el objetivo de crecimiento dentro de las reglas del MVP.",
            "R05_CONTRADICCION_HORIZONTE_OBJETIVO",
        )

    @Rule(
        AS.inv << Inversor(),
        NOT(Perfil()),
        NOT(Stop()),
        salience=80,
    )
    def clasificar_perfil(self, inv):
        tol = float(inv["tolerancia_perdida"])
        h = int(inv["horizonte_meses"])
        liq = float(inv["liquidez_minima"])
        objetivo = inv["objetivo"]

        # Tabla determinística de idoneidad del MVP.
        # Se combinan pérdida tolerada, horizonte, necesidad de liquidez y objetivo.
        if tol <= 5 or liq >= 50 or (h <= 6 and objetivo != "CRECIMIENTO"):
            nivel = "CONSERVADOR"
        elif tol > 20 and h >= 24 and liq < 30 and objetivo == "CRECIMIENTO":
            nivel = "AGRESIVO"
        else:
            nivel = "MODERADO"

        self.perfil = nivel
        self.declare(Perfil(nivel=nivel))
        self.registrar(
            "R10_CLASIFICAR_PERFIL",
            f"Perfil consolidado: {nivel}, considerando tolerancia a pérdida, horizonte, liquidez y objetivo.",
        )

    @Rule(Perfil(nivel="CONSERVADOR"), NOT(Stop()), salience=60)
    def base_conservador(self):
        self.asignacion = {
            "RF_INFLACION": 45.0,
            "RF_DOLAR": 25.0,
            "RENTA_VARIABLE": 0.0,
            "LIQUIDEZ": 30.0,
        }
        self.declare(BaseAsignada())
        self.registrar(
            "R20_BASE_CONSERVADOR",
            "Se aplicó una cartera base conservadora con 0% de renta variable.",
        )

    @Rule(Perfil(nivel="MODERADO"), NOT(Stop()), salience=60)
    def base_moderado(self):
        self.asignacion = {
            "RF_INFLACION": 35.0,
            "RF_DOLAR": 25.0,
            "RENTA_VARIABLE": 20.0,
            "LIQUIDEZ": 20.0,
        }
        self.declare(BaseAsignada())
        self.registrar(
            "R21_BASE_MODERADO",
            "Se aplicó una cartera base moderada y diversificada.",
        )

    @Rule(Perfil(nivel="AGRESIVO"), NOT(Stop()), salience=60)
    def base_agresivo(self):
        self.asignacion = {
            "RF_INFLACION": 20.0,
            "RF_DOLAR": 20.0,
            "RENTA_VARIABLE": 50.0,
            "LIQUIDEZ": 10.0,
        }
        self.declare(BaseAsignada())
        self.registrar(
            "R22_BASE_AGRESIVO",
            "Se aplicó una cartera base agresiva con mayor peso de renta variable.",
        )

    @Rule(
        BaseAsignada(),
        Mercado(inflacion_esperada=MATCH.inf, tasa_referencia=MATCH.tasa),
        TEST(lambda inf, tasa: float(inf) - float(tasa) >= 5),
        NOT(Stop()),
        salience=40,
    )
    def inflacion_supera_tasa(self, inf, tasa):
        # Cobertura de inflación: +10 pp a CER.
        mover = min(10.0, self.asignacion["LIQUIDEZ"])
        self.asignacion["RF_INFLACION"] += mover
        self.asignacion["LIQUIDEZ"] -= mover
        self.registrar(
            "R30_INFLACION_SUPERA_TASA",
            f"La inflación esperada ({inf}%) supera a la tasa de referencia ({tasa}%) por al menos 5 pp; se incrementa cobertura CER.",
        )

    @Rule(
        BaseAsignada(),
        Mercado(tendencia_fx="ALCISTA"),
        NOT(Stop()),
        salience=39,
    )
    def tendencia_fx_alcista(self):
        # +10 pp a cobertura dólar, priorizando reducción de RV y luego CER.
        faltante = 10.0
        quitar_rv = min(faltante, max(0.0, self.asignacion["RENTA_VARIABLE"] - (0.0 if self.perfil == "CONSERVADOR" else 10.0)))
        self.asignacion["RENTA_VARIABLE"] -= quitar_rv
        faltante -= quitar_rv

        if faltante > 0:
            quitar_cer = min(faltante, self.asignacion["RF_INFLACION"])
            self.asignacion["RF_INFLACION"] -= quitar_cer
            faltante -= quitar_cer

        self.asignacion["RF_DOLAR"] += (10.0 - faltante)
        self.registrar(
            "R31_TENDENCIA_CAMBIARIA_ALCISTA",
            "La tendencia cambiaria es alcista; se aumenta la cobertura en instrumentos vinculados al dólar.",
        )

    @Rule(
        BaseAsignada(),
        Mercado(volatilidad=MATCH.vol),
        TEST(lambda vol: 50 <= float(vol) < 80),
        NOT(Stop()),
        salience=38,
    )
    def volatilidad_alta(self, vol):
        reducir = min(10.0, self.asignacion["RENTA_VARIABLE"])
        self.asignacion["RENTA_VARIABLE"] -= reducir
        self.asignacion["LIQUIDEZ"] += reducir
        self.registrar(
            "R32_VOLATILIDAD_ALTA",
            f"La volatilidad ({vol}) es alta; se reduce renta variable y se eleva liquidez.",
        )

    @Rule(
        BaseAsignada(),
        Mercado(ciclo="RECESION"),
        NOT(Stop()),
        salience=37,
    )
    def ciclo_recesivo(self):
        reducir = min(5.0, self.asignacion["RENTA_VARIABLE"])
        self.asignacion["RENTA_VARIABLE"] -= reducir
        self.asignacion["LIQUIDEZ"] += reducir
        self.registrar(
            "R33_CICLO_RECESIVO",
            "El ciclo informado es recesivo; se reduce tácticamente renta variable y se refuerza liquidez.",
        )

    @Rule(
        AS.inv << Inversor(liquidez_minima=MATCH.liq),
        BaseAsignada(),
        NOT(Stop()),
        salience=-100,
    )
    def finalizar(self, liq, inv):
        liquidez_min = float(liq)

        # Regla de idoneidad estricta para conservador.
        if self.perfil == "CONSERVADOR":
            rv = self.asignacion["RENTA_VARIABLE"]
            if rv > 0:
                self.asignacion["RENTA_VARIABLE"] = 0.0
                self.asignacion["LIQUIDEZ"] += rv

        # Cumplir el piso de liquidez declarado por el usuario.
        if self.asignacion["LIQUIDEZ"] < liquidez_min:
            deficit = liquidez_min - self.asignacion["LIQUIDEZ"]
            for clase in ["RENTA_VARIABLE", "RF_DOLAR", "RF_INFLACION"]:
                reducible = max(0.0, self.asignacion[clase])
                quitar = min(deficit, reducible)
                self.asignacion[clase] -= quitar
                self.asignacion["LIQUIDEZ"] += quitar
                deficit -= quitar
                if deficit <= 0.0001:
                    break

        # Normalización exacta a 100%.
        total = sum(self.asignacion.values())
        diferencia = round(100.0 - total, 10)
        self.asignacion["LIQUIDEZ"] += diferencia

        # Redondeo a 2 decimales y corrección final.
        self.asignacion = {k: round(v, 2) for k, v in self.asignacion.items()}
        total = round(sum(self.asignacion.values()), 2)
        if total != 100.0:
            self.asignacion["LIQUIDEZ"] = round(self.asignacion["LIQUIDEZ"] + (100.0 - total), 2)

        self.canasta = seleccionar_canasta(self.asignacion, tope_individual=25.0)
        self.estado = "RECOMENDACION_EXITOSA"
        self.registrar(
            "R40_FINALIZAR_CARTERA",
            "Se aplicaron restricciones de idoneidad, piso de liquidez y normalización; la cartera totaliza 100%.",
        )

    def resultado(self) -> Dict[str, Any]:
        return {
            "estado": self.estado,
            "perfil_riesgo": self.perfil,
            "asset_allocation": self.asignacion if self.estado == "RECOMENDACION_EXITOSA" else None,
            "canasta_instrumentos": self.canasta if self.estado == "RECOMENDACION_EXITOSA" else [],
            "reglas_evaluadas": REGLAS_DISPONIBLES,
            "reglas_disparadas": self.reglas_disparadas,
            "justificaciones": self.justificaciones,
            "errores": self.errores,
        }


def ejecutar_motor(datos_inversor: Dict[str, Any], datos_mercado: Dict[str, Any]) -> Dict[str, Any]:
    engine = RoboAdvisorEngine()
    engine.reset()
    engine.declare(Inversor(**datos_inversor))
    engine.declare(Mercado(**datos_mercado))
    engine.run()
    return engine.resultado()

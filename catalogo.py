from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Instrumento:
    codigo: str
    nombre: str
    clase: str
    vigente: bool = True
    autorizado_demo: bool = True


# IMPORTANTE:
# Este catálogo es académico/demostrativo. En una implementación real debe
# alimentarse de una nómina vigente y validada por el administrador/compliance.
CATALOGO: List[Instrumento] = [
    Instrumento("CER_DEMO_1", "Bono CER - ejemplo 1", "RF_INFLACION"),
    Instrumento("CER_DEMO_2", "Bono CER - ejemplo 2", "RF_INFLACION"),
    Instrumento("CER_DEMO_3", "Letra ajustable CER - ejemplo", "RF_INFLACION"),

    Instrumento("YCA6O", "ON Hard Dollar - ejemplo del brief", "RF_DOLAR"),
    Instrumento("ON_DEMO_2", "ON Hard Dollar - ejemplo 2", "RF_DOLAR"),
    Instrumento("AL30", "Bono soberano USD - ejemplo del brief", "RF_DOLAR"),

    Instrumento("SPY", "CEDEAR SPY - ejemplo del brief", "RENTA_VARIABLE"),
    Instrumento("AAPL", "CEDEAR Apple - ejemplo", "RENTA_VARIABLE"),
    Instrumento("KO", "CEDEAR Coca-Cola - ejemplo", "RENTA_VARIABLE"),

    Instrumento("FCI_BALANZ_AHORRO", "FCI Money Market - ejemplo del brief", "LIQUIDEZ"),
    Instrumento("MM_DEMO_2", "FCI Money Market - ejemplo 2", "LIQUIDEZ"),
]


def instrumentos_por_clase(clase: str) -> List[Instrumento]:
    return [
        x for x in CATALOGO
        if x.clase == clase and x.vigente and x.autorizado_demo
    ]


def seleccionar_canasta(asignacion: Dict[str, float], tope_individual: float = 25.0):
    """
    Distribuye cada clase entre los instrumentos demo disponibles.
    Intenta respetar un tope individual de 25% del portafolio.
    """
    resultado = []

    for clase, porcentaje_clase in asignacion.items():
        if porcentaje_clase <= 0:
            continue

        disponibles = instrumentos_por_clase(clase)
        if not disponibles:
            continue

        restante = round(float(porcentaje_clase), 2)
        idx = 0

        while restante > 0.0001 and disponibles:
            inst = disponibles[idx % len(disponibles)]
            peso = min(tope_individual, restante)

            existente = next(
                (r for r in resultado if r["codigo"] == inst.codigo), None
            )
            if existente:
                # No exceder el tope individual.
                disponible_para_inst = max(0.0, tope_individual - existente["porcentaje"])
                peso = min(peso, disponible_para_inst)

            if peso <= 0:
                idx += 1
                if idx > len(disponibles) * 3:
                    break
                continue

            if existente:
                existente["porcentaje"] = round(existente["porcentaje"] + peso, 2)
            else:
                resultado.append({
                    "codigo": inst.codigo,
                    "nombre": inst.nombre,
                    "clase": clase,
                    "porcentaje": round(peso, 2),
                })

            restante = round(restante - peso, 2)
            idx += 1

            if idx > 100:
                break

        if restante > 0.0001:
            resultado.append({
                "codigo": "REQUIERE_MAS_INSTRUMENTOS",
                "nombre": "Agregar instrumentos elegibles para respetar el tope individual",
                "clase": clase,
                "porcentaje": round(restante, 2),
            })

    return resultado

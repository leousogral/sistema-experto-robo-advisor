# Robo-Advisor experto con Streamlit + Experta

MVP académico de un sistema experto determinístico para recomendación táctica de carteras.

## Qué implementa

- Ingesta de perfil del inversor.
- Ingesta de variables de mercado.
- Clasificación de perfil: CONSERVADOR, MODERADO o AGRESIVO.
- Reglas de idoneidad.
- Asignación táctica por clases de activos.
- Normalización exacta al 100%.
- Derivación a `DERIVADO_ASESOR_MANUAL` en casos contradictorios o extremos.
- Trazabilidad de reglas disparadas (`fired rules`).
- Justificación en lenguaje natural.
- Salida estructurada JSON.
- Interfaz web con Streamlit.
- Motor de inferencia con Experta.

## Estructura

```text
robo_advisor_experto/
├── app.py
├── motor_experto.py
├── catalogo.py
├── requirements.txt
├── README.md
└── tests/
    └── test_motor.py
```

## Recomendación de entorno

Experta es una librería antigua. Para evitar incompatibilidades, se recomienda usar Python 3.9.

### Crear entorno virtual

Windows:

```bash
py -3.9 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux/macOS:

```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecutar

```bash
streamlit run app.py
```

## Ejecutar tests

```bash
pytest -q
```

## Reglas principales

- `R01` valida datos básicos.
- `R02` deriva si los datos de mercado tienen más de 24 h.
- `R03` deriva si la volatilidad es extrema.
- `R04` detecta tolerancia 0% + objetivo de crecimiento.
- `R05` detecta horizonte menor a 3 meses + objetivo de crecimiento.
- `R10` clasifica el perfil.
- `R20/R21/R22` aplican cartera base según perfil.
- `R30` aumenta cobertura CER si inflación esperada supera la tasa por 5 pp o más.
- `R31` aumenta cobertura dólar ante tendencia cambiaria alcista.
- `R32` reduce renta variable ante volatilidad alta.
- `R33` reduce renta variable en ciclo recesivo.
- `R40` aplica restricciones finales, liquidez mínima y suma exacta del 100%.

## Nota sobre instrumentos

`catalogo.py` contiene un catálogo demostrativo. No debe interpretarse como una lista regulatoria vigente.

En una versión productiva conviene reemplazar ese módulo por:

1. una tabla administrable,
2. versionado de instrumentos,
3. fechas de vigencia,
4. fuente de validación regulatoria,
5. control de compliance.

## Advertencia

Este proyecto es educativo. No constituye asesoramiento financiero ni ejecuta órdenes.

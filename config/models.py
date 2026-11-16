"""Configuracion de modelos. Un solo lugar: para agregar modelos, se edita esta lista.

Hoy hay UN modelo habilitado para alumnos. Los demas quedan listos pero apagados.
"""

MODELOS = [
    {
        "id": "deepseek-v4.1-flash",
        "visible": "Eros AI/Sin sensura",
        "motor_visible": "DeepSeek V4.1 Flash",
        "backend": "openrouter",
        "modelo_openrouter": "deepseek/deepseek-v4.1-flash-1017",
        "habilitado": True,
        "para_alumnos": True,
        "max_tokens": 4096,
        "reasoning": False,
        "provider": {
            "order": ["deepinfra"],
            "allow_fallbacks": True,
            "quantizations": ["fp8", "bf16"],
        },
    },
    {
        "id": "eros-local",
        "visible": "Eros local 9B",
        "backend": "local",
        "habilitado": True,
        "para_alumnos": False,
        "max_tokens": 2048,
        "provider": None,
    },
]


def por_id(modelo_id: str) -> dict:
    for m in MODELOS:
        if m["id"] == modelo_id:
            return m
    return MODELOS[0]


def activo(cfg: dict) -> dict:
    return por_id(cfg.get("MODELO_ACTIVO") or MODELOS[0]["id"])


def visibles_para_alumnos() -> list:
    return [m for m in MODELOS if m["habilitado"] and m["para_alumnos"]]

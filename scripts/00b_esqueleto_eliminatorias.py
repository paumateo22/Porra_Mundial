import sys
import json
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def inyectar_estado_semilla():
    print("=======================================================")
    print(" 🌱 [00B] INYECTANDO ESTADO SEMILLA GLOBAL (REALIDAD) 🌱")
    print("=======================================================")
    
    ruta_realidad = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    realidad = html_utils.cargar_json(ruta_realidad) or {"fase_grupos": {}, "clasificados_a_dieciseisavos": [], "eliminatorias": {}}

    # Cargar el nuevo archivo de fechas/horas
    ruta_horas = ROOT_DIR / "config" / "horas_partidos.json"
    horas_data = html_utils.cargar_json(ruta_horas) or {}
    horas_grupos = horas_data.get("fase_grupos_horas", {})
    horas_elim = horas_data.get("eliminatorias_horas", {})

    # ==========================================
    # 1. FASE DE GRUPOS (Desde pau_base.json)
    # ==========================================
    ruta_base = ROOT_DIR / "participantes" / "pau" / "pronosticos" / "grupos" / "pau_base.json"
    if ruta_base.exists():
        base_data = html_utils.cargar_json(ruta_base)
        fase_grupos_semilla = {}
        
        for grupo, partidos in base_data.get("fase_grupos", {}).items():
            fase_grupos_semilla[grupo] = []
            for p in partidos:
                # Generamos la clave para buscar la hora exacta
                clave_partido = f"{p['local']}_vs_{p['visitante']}"
                fecha_partido = horas_grupos.get(clave_partido, "")

                fase_grupos_semilla[grupo].append({
                    "local": p["local"],
                    "visitante": p["visitante"],
                    "fecha": fecha_partido,  # <-- Inyectamos la fecha
                    "goles_local": "",
                    "goles_visitante": "",
                    "estado": "notstarted"
                })
                
        realidad["fase_grupos"] = fase_grupos_semilla
        print("✅ Fase de grupos inyectada con equipos oficiales, fechas y estado 'notstarted'.")
    else:
        print(f"⚠️ Atención: No se encontró {ruta_base} para extraer la fase de grupos.")

    # ==========================================
    # 2. ELIMINATORIAS (Chuleta Oficial)
    # ==========================================
    dieciseisavos_cruces = [
        {"id": 73, "l": "1E", "v": "3A/3B/3C/3D/3F"},
        {"id": 74, "l": "1I", "v": "3C/3D/3F/3G/3H"},
        {"id": 75, "l": "2A", "v": "2B"},
        {"id": 76, "l": "1F", "v": "2C"},
        {"id": 77, "l": "2K", "v": "2L"},
        {"id": 78, "l": "1H", "v": "2J"},
        {"id": 79, "l": "1D", "v": "3B/3E/3F/3I/3J"},
        {"id": 80, "l": "1G", "v": "3A/3E/3H/3I/3J"},
        {"id": 81, "l": "1C", "v": "2F"},
        {"id": 82, "l": "2E", "v": "2I"},
        {"id": 83, "l": "1A", "v": "3C/3E/3F/3H/3I"},
        {"id": 84, "l": "1L", "v": "3E/3H/3I/3J/3K"},
        {"id": 85, "l": "1J", "v": "2H"},
        {"id": 86, "l": "2D", "v": "2G"},
        {"id": 87, "l": "1B", "v": "3E/3F/3G/3I/3J"}, 
        {"id": 88, "l": "1K", "v": "3D/3E/3I/3J/3L"}
    ]

    octavos_cruces = [
        {"id": 89, "l": "Ganador 73", "v": "Ganador 74"},
        {"id": 90, "l": "Ganador 75", "v": "Ganador 76"},
        {"id": 91, "l": "Ganador 77", "v": "Ganador 78"},
        {"id": 92, "l": "Ganador 79", "v": "Ganador 80"},
        {"id": 93, "l": "Ganador 81", "v": "Ganador 82"},
        {"id": 94, "l": "Ganador 83", "v": "Ganador 84"},
        {"id": 95, "l": "Ganador 85", "v": "Ganador 86"},
        {"id": 96, "l": "Ganador 87", "v": "Ganador 88"}
    ]

    cuartos_cruces = [
        {"id": 97, "l": "Ganador 89", "v": "Ganador 90"},
        {"id": 98, "l": "Ganador 91", "v": "Ganador 92"},
        {"id": 99, "l": "Ganador 93", "v": "Ganador 94"},
        {"id": 100, "l": "Ganador 95", "v": "Ganador 96"}
    ]

    semis_cruces = [
        {"id": 101, "l": "Ganador 97", "v": "Ganador 98"},
        {"id": 102, "l": "Ganador 99", "v": "Ganador 100"}
    ]

    def formatear_fase(cruces):
        resultado = []
        for c in cruces:
            # Buscamos la fecha por ID en tu nuevo JSON
            fecha_partido = horas_elim.get(str(c["id"]), "")
            resultado.append({
                "id_partido": c["id"], 
                "local": c["l"], 
                "visitante": c["v"], 
                "fecha": fecha_partido,  # <-- Inyectamos la fecha
                "estado": "notstarted", 
                "goles_local": "", 
                "goles_visitante": ""
            })
        return resultado

    realidad["eliminatorias"]["dieciseisavos"] = formatear_fase(dieciseisavos_cruces)
    realidad["eliminatorias"]["octavos"] = formatear_fase(octavos_cruces)
    realidad["eliminatorias"]["cuartos"] = formatear_fase(cuartos_cruces)
    realidad["eliminatorias"]["semifinales"] = formatear_fase(semis_cruces)
    
    # Tercer puesto y final
    fecha_tercer = horas_elim.get("103", "")
    fecha_final = horas_elim.get("104", "")
    realidad["eliminatorias"]["tercer_puesto"] = [{"id_partido": 103, "local": "Perdedor 101", "visitante": "Perdedor 102", "fecha": fecha_tercer, "estado": "notstarted", "goles_local": "", "goles_visitante": ""}]
    realidad["eliminatorias"]["final"] = [{"id_partido": 104, "local": "Ganador 101", "visitante": "Ganador 102", "fecha": fecha_final, "estado": "notstarted", "goles_local": "", "goles_visitante": ""}]

    with open(ruta_realidad, 'w', encoding='utf-8') as f:
        json.dump(realidad, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Esqueleto de eliminatorias inyectado con placeholders de formato y fechas.")
    print(f"💾 Guardado completado en: {ruta_realidad.relative_to(ROOT_DIR)}")

if __name__ == "__main__":
    inyectar_estado_semilla()
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# Mapeo estricto del torneo a valores numéricos
MAPEO_FASES = {
    "grupos": 0,
    "dieciseisavos": 1,
    "octavos": 2,
    "cuartos": 3,
    "semifinales": 4,
    "tercer_puesto": 4, # Cuenta como caer en semis según diseño
    "finales": 5,
    "final": 5
}

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

def guardar_json(datos, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def determinar_fase_caida_jugador(jugador, equipo, realidad_dict):
    """Escanea los archivos de un jugador para ver en qué fase exacta cae una selección."""
    dir_jugador = ROOT_DIR / "participantes" / jugador / "pronosticos"
    
    # 1. Comprobar si cayó en Fase de Grupos
    ruta_base = dir_jugador / "grupos" / f"{jugador}_base.json"
    if ruta_base.exists():
        base = cargar_json(ruta_base)
        if equipo not in base.get("clasificados_a_dieciseisavos", []):
            return 0

    # 2. Rastrear eliminatorias de atrás hacia adelante para ver su última aparición
    for fase in ["finales", "semifinales", "cuartos", "octavos", "dieciseisavos"]:
        ruta_ocr = dir_jugador / "eliminatorias" / fase / f"{fase}.json"
        if ruta_ocr.exists():
            ocr_data = cargar_json(ruta_ocr)
            partidos = ocr_data.get("predicciones", {}).get(fase, [])
            for p in partidos:
                if p.get("local") == equipo or p.get("visitante") == equipo:
                    return MAPEO_FASES[fase]
                    
    return 0

def determinar_fase_caida_real(equipo, realidad_dict):
    """Determina en qué fase cayó realmente una selección según el JSON oficial."""
    # Comprobar si no pasó de grupos
    if equipo not in realidad_dict.get("clasificados_a_dieciseisavos", []):
        return 0
        
    eliminatorias = realidad_dict.get("eliminatorias", {})
    for fase in ["finales", "final", "tercer_puesto", "semifinales", "cuartos", "octavos", "dieciseisavos"]:
        partidos = eliminatorias.get(fase, [])
        for p in partidos:
            if p.get("estado") == "finished" and (p.get("local") == equipo or p.get("visitante") == equipo):
                # Si el partido terminó, podemos evaluar si quedó fuera aquí
                gl, gv = int(p.get("goles_local", 0)), int(p.get("goles_visitante", 0))
                ganador = p.get("local") if gl > gv else p.get("visitante")
                if gl == gv:
                    pl, pv = int(p.get("penaltis_local", 0)), int(p.get("penaltis_visitante", 0))
                    ganador = p.get("local") if pl > pv else p.get("visitante")
                
                # Si jugó la fase pero no es el ganador, cayó aquí
                if ganador != equipo:
                    # Excepciones de Final/Tercer puesto (ambos cierran el torneo en su rango)
                    if fase in ["final", "finales"]: return 5
                    if fase in ["tercer_puesto", "semifinales"]: return 4
                    return MAPEO_FASES.get(fase, 0)
    return 0

def ejecutar_06e_motor_sorpresas():
    print("=======================================================")
    print(" 🎯 [06E] INICIANDO MOTOR DE SORPRESAS Y DECEPCIONES 🎯")
    print("=======================================================")

    settings = cargar_json(ROOT_DIR / "config" / "settings.json")
    realidad = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json")
    reporte_previo = cargar_json(ROOT_DIR / "data" / "resultados" / "reporte_06b_jornadas.json") # Heredamos estructura

    if not settings or not realidad or not reporte_previo:
        print("❌ Error: Faltan archivos de configuración o realidad para ejecutar el 06e.")
        return

    if settings.get("habilitadores", {}).get("sorpresas_decepciones", 0) == 0:
        print("⚠️ El interruptor 'sorpresas_decepciones' está desactivado.")
        return

    # Cargar umbrales
    conf = settings.get("sorpresas_decepciones_config", {})
    umb_p_m = conf.get("distancia_minima_pronostico_media", 2.0)
    umb_r_m = conf.get("distancia_minima_realidad_media", 2.0)
    umb_r_p = conf.get("distancia_maxima_pronostico_realidad", 1.0)
    
    pts_sorpresa = settings.get("puntuaciones", {}).get("premios_finales", {}).get("sorpresa", 5)
    pts_decepcion = settings.get("puntuaciones", {}).get("premios_finales", {}).get("decepcion", 5)

    jugadores = list(reporte_previo.keys())
    
    # Extraer lista de todos los equipos del torneo basados en la liguilla real
    todos_equipos = set()
    for grupo, partidos in realidad.get("fase_grupos", {}).items():
        for p in partidos:
            todos_equipos.add(p["local"])
            todos_equipos.add(p["visitante"])
    todos_equipos = sorted(list(todos_equipos))

    # --- PASADA 1: CALCULAR MEDIAS ---
    mapa_valores_caida = {eq: {"jugadores": {}, "realidad": 0, "media": 0.0} for eq in todos_equipos}
    
    for eq in todos_equipos:
        suma_fases = 0
        mapa_valores_caida[eq]["realidad"] = determinar_fase_caida_real(eq, realidad)
        
        for jug in jugadores:
            fase_p = determinar_fase_caida_jugador(jug, eq, realidad)
            mapa_valores_caida[eq]["jugadores"][jug] = fase_p
            suma_fases += fase_p
            
        mapa_valores_caida[eq]["media"] = round(suma_fases / len(jugadores), 2)

    # --- PASADA 2: EVALUAR JUGADORES ---
    reporte_06e = {}
    
    for jug in jugadores:
        reporte_06e[jug] = {
            "puntos_sorpresas": 0,
            "puntos_decepciones": 0,
            "detalles_equipos": {}
        }
        
        total_sorpresas = 0
        total_decepciones = 0

        for eq in todos_equipos:
            P = mapa_valores_caida[eq]["jugadores"][jug]
            M = mapa_valores_caida[eq]["media"]
            R = mapa_valores_caida[eq]["realidad"]

            # Comprobar condiciones matemáticas estrictas
            cumple_p_m = abs(P - M) >= umb_p_m
            cumple_r_m = abs(R - M) >= umb_r_m
            cumple_r_p = abs(R - P) <= umb_r_p

            tipo_premio = "Ninguno"
            puntos_ganados = 0

            # Solo se evalúa si el partido o la fase real para el equipo ya concluyó (R > 0 o fase terminada)
            if cumple_p_m and cumple_r_m and cumple_r_p:
                if R > M and P > M:
                    tipo_premio = "Sorpresa"
                    puntos_ganados = pts_sorpresa
                    total_sorpresas += puntos_ganados
                elif R < M and P < M:
                    tipo_premio = "Decepción"
                    puntos_ganados = pts_decepcion
                    total_decepciones += puntos_ganados

            reporte_06e[jug]["detalles_equipos"][eq] = {
                "pronostico": P,
                "media_grupo": M,
                "realidad": R,
                "resultado_calculo": tipo_premio,
                "puntos": puntos_ganados
            }

        reporte_06e[jug]["puntos_sorpresas"] = total_sorpresas
        reporte_06e[jug]["puntos_decepciones"] = total_decepciones

        # Actualizar el Historial de Puntos del Libro Personal
        ruta_libro = ROOT_DIR / "participantes" / jug / "estadisticas" / "historial_puntos.json"
        libro = cargar_json(ruta_libro)
        if libro:
            if "premios_finales" not in libro: libro["premios_finales"] = {}
            if "formularios" not in libro["premios_finales"]: libro["premios_finales"]["formularios"] = {"detalles": {}}
            
            libro["premios_finales"]["formularios"]["detalles"]["sorpresa"] = total_sorpresas
            libro["premios_finales"]["formularios"]["detalles"]["decepcion"] = total_decepciones
            
            # Guardamos los datos de las matrices de cálculo para que el generador de vistas los lea directamente
            libro["matriz_sorpresas_decepciones"] = reporte_06e[jug]["detalles_equipos"]
            guardar_json(libro, ruta_libro)

        print(f"👤 {jug.title()}: Sorpresas (+{total_sorpresas} pts) | Decepciones (+{total_decepciones} pts)")

    ruta_salida = ROOT_DIR / "data" / "resultados" / "reporte_06e_sorpresas.json"
    guardar_json(reporte_06e, ruta_salida)
    print(f"\n✅ Informe 06e guardado con éxito.")

if __name__ == "__main__":
    ejecutar_06e_motor_sorpresas()
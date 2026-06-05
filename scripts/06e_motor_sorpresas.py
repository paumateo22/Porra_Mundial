import sys
import json
import math
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# Mapeo estricto del torneo a valores numéricos (0 = Grupos, 5 = Final)
MAPEO_FASES = {
    "grupos": 0, "dieciseisavos": 1, "octavos": 2, 
    "cuartos": 3, "semifinales": 4, "tercer_puesto": 4, 
    "finales": 5, "final": 5
}

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

def guardar_json(datos, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def determinar_fase_caida_jugador(jugador, equipo):
    """
    Lee ESTRICTAMENTE el pronóstico original del jugador (Infobae / base.json)
    para saber cuál fue su apuesta inicial antes de empezar el mundial.
    """
    dir_jugador = ROOT_DIR / "participantes" / jugador / "pronosticos"
    ruta_base = dir_jugador / "grupos" / f"{jugador}_base.json"
    
    if not ruta_base.exists(): 
        return 0
        
    base = cargar_json(ruta_base)
    
    # Si en su pronóstico original el equipo no pasaba de grupos:
    if equipo not in base.get("clasificados_a_dieciseisavos", []): 
        return 0

    eliminatorias = base.get("eliminatorias", {})
    
    # Revisamos desde la fase más alta a la más baja dentro de SU PRONÓSTICO ORIGINAL
    for p in eliminatorias.get("finales", []) + eliminatorias.get("final", []):
        if p.get("local") == equipo or p.get("visitante") == equipo: 
            return 4 if p.get("id_partido") == 103 else 5
            
    for p in eliminatorias.get("semifinales", []) + eliminatorias.get("tercer_puesto", []):
        if p.get("local") == equipo or p.get("visitante") == equipo: 
            return 4
            
    for p in eliminatorias.get("cuartos", []):
        if p.get("local") == equipo or p.get("visitante") == equipo: 
            return 3
            
    for p in eliminatorias.get("octavos", []):
        if p.get("local") == equipo or p.get("visitante") == equipo: 
            return 2
            
    for p in eliminatorias.get("dieciseisavos", []):
        if p.get("local") == equipo or p.get("visitante") == equipo: 
            return 1
            
    return 0

def determinar_fase_caida_real(equipo, realidad_dict):
    if equipo not in realidad_dict.get("clasificados_a_dieciseisavos", []): return 0
    eliminatorias = realidad_dict.get("eliminatorias", {})
    
    for p in eliminatorias.get("finales", []) + eliminatorias.get("final", []):
        if p.get("local") == equipo or p.get("visitante") == equipo: return 4 if p.get("id_partido") == 103 else 5
    for p in eliminatorias.get("semifinales", []) + eliminatorias.get("tercer_puesto", []):
        if p.get("local") == equipo or p.get("visitante") == equipo: return 4
    for p in eliminatorias.get("cuartos", []):
        if p.get("local") == equipo or p.get("visitante") == equipo: return 3
    for p in eliminatorias.get("octavos", []):
        if p.get("local") == equipo or p.get("visitante") == equipo: return 2
    for p in eliminatorias.get("dieciseisavos", []):
        if p.get("local") == equipo or p.get("visitante") == equipo: return 1
    return 0

def ejecutar_06e_motor_sorpresas():
    print("=======================================================")
    print(" 🎯 [06E] INICIANDO MOTOR DE SORPRESAS Y DECEPCIONES 🎯")
    print("=======================================================")

    settings = cargar_json(ROOT_DIR / "config" / "settings.json")
    realidad = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json")
    reporte_previo = cargar_json(ROOT_DIR / "data" / "resultados" / "reporte_06b_jornadas.json")

    if not settings or not realidad or not reporte_previo: return

    if settings.get("habilitadores", {}).get("sorpresas_decepciones", 0) == 0: return

    conf = settings.get("sorpresas_decepciones_config", {})
    umb_minimo = conf.get("umbral_minimo_global", 1.0)
    mult_varianza = conf.get("multiplicador_varianza", 1.0)
    umb_r_p = conf.get("distancia_maxima_pronostico_realidad", 1.0) # Margen de error fijo
    
    pts_sorpresa = settings.get("puntuaciones", {}).get("premios_finales", {}).get("sorpresa", 5)
    pts_decepcion = settings.get("puntuaciones", {}).get("premios_finales", {}).get("decepcion", 5)

    jugadores = list(reporte_previo.keys())
    todos_equipos = {p["local"] for grp in realidad.get("fase_grupos", {}).values() for p in grp}.union(
                    {p["visitante"] for grp in realidad.get("fase_grupos", {}).values() for p in grp})
    todos_equipos = sorted(list(todos_equipos))

    mapa_valores_caida = {eq: {"jugadores": {}, "realidad": 0, "media": 0.0} for eq in todos_equipos}
    desviaciones_equipos = []
    
    # --- PASADA 1: CALCULAR MEDIAS Y DESVIACIÓN ESTÁNDAR POR EQUIPO ---
    for eq in todos_equipos:
        suma_fases = 0
        mapa_valores_caida[eq]["realidad"] = determinar_fase_caida_real(eq, realidad)
        
        for jug in jugadores:
            fase_p = determinar_fase_caida_jugador(jug, eq)
            mapa_valores_caida[eq]["jugadores"][jug] = fase_p
            suma_fases += fase_p
            
        media = suma_fases / len(jugadores)
        mapa_valores_caida[eq]["media"] = round(media, 2)
        
        varianza = sum((mapa_valores_caida[eq]["jugadores"][j] - media)**2 for j in jugadores) / len(jugadores)
        desviaciones_equipos.append(math.sqrt(varianza))

    # --- CÁLCULO DEL UMBRAL GLOBAL ---
    media_desviaciones = sum(desviaciones_equipos) / len(desviaciones_equipos) if desviaciones_equipos else 0
    umbral_global = max(umb_minimo, round(media_desviaciones * mult_varianza, 2))
    print(f"📊 Desviación media global de la comunidad: ±{umbral_global} fases.")

    # --- NUEVO: PREPARAR EL DICCIONARIO GLOBAL DE SD ---
    global_sd = {
        eq: {
            "media": mapa_valores_caida[eq]["media"],
            "realidad": mapa_valores_caida[eq]["realidad"],
            "umbral": umbral_global,
            "predicciones": []
        } for eq in todos_equipos
    }

    # --- PASADA 2: EVALUAR CON EL UMBRAL GLOBAL ---
    reporte_06e = {}
    for jug in jugadores:
        reporte_06e[jug] = {"puntos_sorpresas": 0, "puntos_decepciones": 0, "detalles_equipos": {}}
        total_sorpresas = total_decepciones = 0

        for eq in todos_equipos:
            P = mapa_valores_caida[eq]["jugadores"][jug]
            M = mapa_valores_caida[eq]["media"]
            R = mapa_valores_caida[eq]["realidad"]
            U = umbral_global

            cumple_p_m = abs(P - M) > U
            cumple_r_m = abs(R - M) > U
            cumple_r_p = abs(R - P) <= umb_r_p

            tipo_premio, puntos_ganados = "Ninguno", 0

            if cumple_p_m and cumple_r_m and cumple_r_p:
                if R > M and P > M:
                    tipo_premio, puntos_ganados = "Sorpresa", pts_sorpresa
                    total_sorpresas += puntos_ganados
                elif R < M and P < M:
                    tipo_premio, puntos_ganados = "Decepción", pts_decepcion
                    total_decepciones += puntos_ganados

            reporte_06e[jug]["detalles_equipos"][eq] = {
                "pronostico": P, "media_grupo": M, "realidad": R, "umbral_aplicado": U,
                "resultado_calculo": tipo_premio, "puntos": puntos_ganados
            }
            
            # --- Añadimos al registro global ---
            global_sd[eq]["predicciones"].append({
                "jugador_id": jug,
                "jugador_nombre": jug.replace('_', ' ').title(),
                "fase_pronostico": P,
                "puntos": puntos_ganados,
                "resultado": tipo_premio
            })

        reporte_06e[jug]["puntos_sorpresas"] = total_sorpresas
        reporte_06e[jug]["puntos_decepciones"] = total_decepciones

        ruta_libro = ROOT_DIR / "participantes" / jug / "estadisticas" / "historial_puntos.json"
        libro = cargar_json(ruta_libro)
        if libro:
            if "premios_finales" not in libro: libro["premios_finales"] = {}
            if "formularios" not in libro["premios_finales"]: libro["premios_finales"]["formularios"] = {"detalles": {}}
            
            libro["premios_finales"]["formularios"]["detalles"]["sorpresa"] = total_sorpresas
            libro["premios_finales"]["formularios"]["detalles"]["decepcion"] = total_decepciones
            libro["matriz_sorpresas_decepciones"] = reporte_06e[jug]["detalles_equipos"]
            guardar_json(libro, ruta_libro)

        print(f"👤 {jug.title()}: Sorpresas (+{total_sorpresas} pts) | Decepciones (+{total_decepciones} pts)")

    guardar_json(reporte_06e, ROOT_DIR / "data" / "resultados" / "reporte_06e_sorpresas.json")
    
    # --- NUEVO: Guardar el JSON Auxiliar para FrontEnd ---
    ruta_global_sd = ROOT_DIR / "data" / "resultados" / "global_sd.json"
    guardar_json(global_sd, ruta_global_sd)
    print(f"\n✅ Diccionario global guardado en: {ruta_global_sd}")
    print(f"✅ Informe 06e guardado con éxito.")

if __name__ == "__main__":
    ejecutar_06e_motor_sorpresas()
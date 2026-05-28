import sys
import json
import csv
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# =====================================================================
# UTILIDADES
# =====================================================================
def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_json(datos, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# =====================================================================
# EVALUADORES DE CIERRE (EL MACRO FINAL)
# =====================================================================
def evaluar_fase_grupos(jugador, realidad, settings):
    """Evalúa quién pasa de fase de grupos y devuelve puntos y detalles."""
    pts_grupos = 0
    detalle = {"equipos_acertados": [], "puntos_conseguidos": 0}
    
    if settings["habilitadores"].get("bono_clasificacion_grupos", 0) == 0 and settings["habilitadores"].get("bono_posicion_grupos", 0) == 0:
        return pts_grupos, detalle

    ruta_base = ROOT_DIR / "participantes" / jugador / "pronosticos" / "grupos" / f"{jugador}_base.json"
    porra = cargar_json(ruta_base)
    if not porra: return 0, detalle

    clasificados_reales = realidad.get("clasificados_a_dieciseisavos", [])
    clasificados_predichos = porra.get("clasificados_a_dieciseisavos", [])

    for equipo in clasificados_predichos:
        if equipo in clasificados_reales:
            if settings["habilitadores"].get("bono_clasificacion_grupos"):
                pts_grupos += settings["puntuaciones"]["fase_grupos"]["acierto_clasificado"]
                detalle["equipos_acertados"].append(equipo)

    detalle["puntos_conseguidos"] = pts_grupos
    return pts_grupos, detalle

def evaluar_podio(jugador, realidad, settings):
    """Calcula los puntos por acertar Campeón, Subcampeón y Tercer Puesto con detalles."""
    pts_podio = 0
    acerto_campeon = 0 
    detalle = {"campeon_acertado": None, "subcampeon_acertado": None, "tercero_acertado": None, "puntos_conseguidos": 0}

    ruta_base = ROOT_DIR / "participantes" / jugador / "pronosticos" / "grupos" / f"{jugador}_base.json"
    porra = cargar_json(ruta_base)
    if not porra: return 0, 0, detalle

    final_real = realidad.get("eliminatorias", {}).get("final", [])
    tercero_real = realidad.get("eliminatorias", {}).get("tercer_puesto", [])
    
    c_real, sub_real, t_real = None, None, None
    if final_real and final_real[0]["estado"] == "finished":
        c_real = final_real[0]["ganador"]
        sub_real = final_real[0]["local"] if final_real[0]["visitante"] == c_real else final_real[0]["visitante"]
    if tercero_real and tercero_real[0]["estado"] == "finished":
        t_real = tercero_real[0]["ganador"]

    c_pred = porra.get("campeon", "")
    
    # Campeón
    if settings["habilitadores"].get("campeon") and c_real and c_pred == c_real:
        pts_podio += settings["puntuaciones"]["premios_finales"]["campeon"]
        acerto_campeon = 1
        detalle["campeon_acertado"] = c_real
        
    # Subcampeón
    final_pred = porra.get("eliminatorias", {}).get("final", [])
    if settings["habilitadores"].get("subcampeon") and sub_real and final_pred:
        sub_pred = final_pred[0]["local"] if final_pred[0]["pasa"] != final_pred[0]["local"] else final_pred[0]["visitante"]
        if sub_pred == sub_real:
            pts_podio += settings["puntuaciones"]["premios_finales"]["subcampeon"]
            detalle["subcampeon_acertado"] = sub_real

    # Tercer Puesto
    tercero_pred = porra.get("eliminatorias", {}).get("tercer_puesto", [])
    if settings["habilitadores"].get("tercer_puesto") and t_real and tercero_pred:
        t_p = tercero_pred[0]["pasa"]
        if t_p == t_real:
            pts_podio += settings["puntuaciones"]["premios_finales"]["tercer_puesto"]
            detalle["tercero_acertado"] = t_real

    detalle["puntos_conseguidos"] = pts_podio
    return pts_podio, acerto_campeon, detalle

def evaluar_premios_forms(jugador, settings):
    """Cruza los premios de Google Forms con la realidad y devuelve desglose."""
    ruta_premios = ROOT_DIR / "participantes" / jugador / "pronosticos" / "premios.json"
    ruta_reales = ROOT_DIR / "data" / "resultados" / "premios_reales.json"
    
    premios_pred = cargar_json(ruta_premios)
    premios_reales = cargar_json(ruta_reales)
    
    detalle = {"aciertos_exactos": {}, "puntos_conseguidos": 0}
    if not premios_pred or not premios_reales: return 0, detalle
        
    pts_extra = 0
    respuestas_jugador = premios_pred.get("premios_extra", {})
    
    for categoria, respuesta in respuestas_jugador.items():
        cat_limpia = categoria.lower().replace(" ", "_")
        
        if settings["habilitadores"].get(cat_limpia, 0) == 1:
            respuesta_real = premios_reales.get(cat_limpia, "")
            if respuesta.strip().lower() == str(respuesta_real).strip().lower():
                pts_ganados = settings["puntuaciones"]["premios_finales"].get(cat_limpia, 0)
                pts_extra += pts_ganados
                detalle["aciertos_exactos"][categoria] = {"respuesta": respuesta_real, "puntos": pts_ganados}
                
    detalle["puntos_conseguidos"] = pts_extra
    return pts_extra, detalle

# =====================================================================
# EL MOTOR PRINCIPAL 06C
# =====================================================================
def ejecutar_06c_motor_cierre():
    print("=======================================================")
    print(" 🏆 [06C] INICIANDO MOTOR DE CIERRE Y DESEMPATES 🏆")
    print("=======================================================")
    
    settings = cargar_json(ROOT_DIR / "config" / "settings.json")
    realidad = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json")
    reporte_06b = cargar_json(ROOT_DIR / "data" / "resultados" / "reporte_06b_jornadas.json")

    if not all([settings, realidad, reporte_06b]):
        print("❌ Error: Faltan archivos clave. Ejecuta el 06b antes de cerrar el campeonato.")
        return

    ranking = []

    for jugador, stats_previos in reporte_06b.items():
        # 1. Calcular nuevos puntos Y obtener los "recibos"
        pts_grupos, det_grupos = evaluar_fase_grupos(jugador, realidad, settings)
        pts_podio, acerto_campeon, det_podio = evaluar_podio(jugador, realidad, settings)
        pts_forms, det_forms = evaluar_premios_forms(jugador, settings)
        
        # 2. Sumar el total global
        total_puntos = stats_previos["puntos_partidos"] + stats_previos["puntos_jornadas"] + pts_grupos + pts_podio + pts_forms
        
        # 3. Construir el perfil completo
        perfil = {
            "jugador": jugador,
            "total": total_puntos,
            "pts_partidos": stats_previos["puntos_partidos"],
            "pts_jornadas": stats_previos["puntos_jornadas"],
            "pts_grupos": pts_grupos,
            "pts_podio": pts_podio,
            "pts_forms": pts_forms,
            "acierto_1x2": stats_previos["total_aciertos_1x2"],
            "acierto_exacto": stats_previos["total_aciertos_exactos"],
            "campeon": acerto_campeon,
            # Guardamos los recibos para inyectarlos luego
            "det_grupos": det_grupos,
            "det_podio": det_podio,
            "det_forms": det_forms
        }
        ranking.append(perfil)

    # 4. EL SISTEMA DE DESEMPATE
    c1 = settings["desempates"].get("criterio_1", "acierto_1x2")
    c2 = settings["desempates"].get("criterio_2", "acierto_exacto")
    c3 = settings["desempates"].get("criterio_3", "campeon")
    
    ranking.sort(key=lambda x: (
        x["total"], 
        x.get(c1, 0), 
        x.get(c2, 0), 
        x.get(c3, 0)
    ), reverse=True)

    # 5. MOSTRAR CLASIFICACIÓN Y ACTUALIZAR LIBROS PERSONALES
    print("\n📊 CLASIFICACIÓN FINAL DEL MUNDIAL 📊")
    print("-" * 90)
    print(f"{'Pos':<4} | {'Jugador':<15} | {'Base (Part+Jorn)':<18} | {'Grupos':<8} | {'Podio+Extra':<13} | {'TOTAL':<5}")
    print("-" * 90)
    
    ruta_csv = ROOT_DIR / "data" / "resultados" / "ranking_oficial.csv"
    dir_participantes = ROOT_DIR / "participantes"
    
    with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Posicion", "Jugador", "Puntos_Partidos", "Puntos_Jornadas", "Puntos_Grupos", "Puntos_Podio", "Puntos_Forms", "Aciertos_1X2", "Aciertos_Exactos", "TOTAL"])
        
        posicion_real = 1
        for i, j in enumerate(ranking):
            if i > 0:
                prev = ranking[i-1]
                if j["total"] != prev["total"] or j[c1] != prev[c1] or j[c2] != prev[c2] or j[c3] != prev[c3]:
                    posicion_real = i + 1

            nombre = j['jugador'].replace('_', ' ').title()
            p_base = j['pts_partidos'] + j['pts_jornadas']
            p_extra = j['pts_podio'] + j['pts_forms']
            
            print(f"{posicion_real:<4} | {nombre:<15} | {p_base:<18.2f} | {j['pts_grupos']:<8} | {p_extra:<13} | {j['total']:<5.2f}")
            writer.writerow([posicion_real, nombre, j['pts_partidos'], j['pts_jornadas'], j['pts_grupos'], j['pts_podio'], j['pts_forms'], j['acierto_1x2'], j['acierto_exacto'], j['total']])
            
            # --- 📝 ACTUALIZAR EL LIBRO DE CUENTAS PERSONAL ---
            ruta_libro = dir_participantes / j['jugador'] / "estadisticas" / "historial_puntos.json"
            libro = cargar_json(ruta_libro)
            if libro:
                libro["resolucion_fase_grupos"] = j["det_grupos"]
                libro["premios_finales"] = {
                    "podio": j["det_podio"],
                    "formularios": j["det_forms"]
                }
                libro["puntos_totales"] = j["total"]
                libro["posicion_final_ranking"] = posicion_real
                guardar_json(libro, ruta_libro)
            # --------------------------------------------------

    print("-" * 90)
    print(f"💾 Ranking final exportado a CSV en: {ruta_csv.relative_to(ROOT_DIR)}")
    print(f"📔 Libros de Cuentas personales sellados con la posición final y los premios.")
    print(f"ℹ️ Criterios de desempate aplicados: 1º {c1.upper()}, 2º {c2.upper()}, 3º {c3.upper()}")

if __name__ == "__main__":
    ejecutar_06c_motor_cierre()
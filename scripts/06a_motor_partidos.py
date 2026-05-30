import sys
import json
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# =====================================================================
# CONFIGURACIÓN Y UTILIDADES
# =====================================================================
def cargar_configuracion():
    ruta = ROOT_DIR / "config" / "settings.json"
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

CONFIG = cargar_configuracion()
FASES_ORDENADAS = ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]

def cargar_realidad():
    ruta = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    if not ruta.exists():
        return None
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_json(datos, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# =====================================================================
# LÓGICA DE PUNTUACIÓN (MICRO)
# =====================================================================
def calcular_puntos_partido(pronostico_loc, pronostico_vis, real_loc, real_vis, racha_loc=0, racha_vis=0):
    pts_base = 0
    acierto_1x2 = False
    acierto_exacto = False
    
    if CONFIG["habilitadores"].get("acierto_1x2", 0) == 0:
        return 0, False, False, 1.0

    sig_p = "1" if pronostico_loc > pronostico_vis else ("2" if pronostico_vis > pronostico_loc else "X")
    sig_r = "1" if real_loc > real_vis else ("2" if real_vis > real_loc else "X")
    
    if sig_p == sig_r:
        pts_base += CONFIG["puntuaciones"]["partidos"]["acierto_1x2"]
        acierto_1x2 = True
        
    if CONFIG["habilitadores"].get("acierto_exacto", 0) == 1 and acierto_1x2:
        if pronostico_loc == real_loc and pronostico_vis == real_vis:
            pts_base += CONFIG["puntuaciones"]["partidos"]["acierto_exacto"]
            acierto_exacto = True

    multiplicador = CONFIG["multiplicadores"]["base"]
    if CONFIG["habilitadores"].get("racha_eliminatorias", 0) == 1:
        inc = CONFIG["multiplicadores"]["incremento_racha_por_fase"]
        multiplicador += (racha_loc * inc) + (racha_vis * inc)
        
    puntos_finales = pts_base * multiplicador
    return puntos_finales, acierto_1x2, acierto_exacto, multiplicador

def calcular_racha_equipo(jugador, equipo, fase_objetivo):
    racha = 0
    fases_cronologicas = ["grupos", "dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]
    
    fase_busqueda_ocr = "finales" if fase_objetivo in ["final", "tercer_puesto"] else fase_objetivo
    fase_busqueda_infobae = fase_objetivo
    
    idx_limite = fases_cronologicas.index(fase_busqueda_ocr) if fase_busqueda_ocr in fases_cronologicas else 0
    
    for i in range(idx_limite):
        fase_origen = fases_cronologicas[i]
        
        if fase_origen == "grupos":
            ruta_base = ROOT_DIR / "participantes" / jugador / "pronosticos" / "grupos" / f"{jugador}_base.json"
            if ruta_base.exists():
                with open(ruta_base, 'r', encoding='utf-8') as f:
                    base = json.load(f)
                    
                partidos_objetivo = base.get("eliminatorias", {}).get(fase_busqueda_infobae, [])
                for p in partidos_objetivo:
                    if p.get("local") == equipo or p.get("visitante") == equipo:
                        racha += 1
                        break 
                        
        else:
            ruta_ocr = ROOT_DIR / "participantes" / jugador / "pronosticos" / "eliminatorias" / fase_origen / f"{fase_origen}.json"
            if ruta_ocr.exists():
                with open(ruta_ocr, 'r', encoding='utf-8') as f:
                    ocr_data = json.load(f)
                    
                partidos_objetivo = ocr_data.get("predicciones", {}).get(fase_busqueda_ocr, [])
                for p in partidos_objetivo:
                    if p.get("local") == equipo or p.get("visitante") == equipo:
                        racha += 1
                        break 
                        
    return racha

# =====================================================================
# EL CEREBRO DE EJECUCIÓN 06A
# =====================================================================
def ejecutar_06a_motor_partidos():
    print("=======================================================")
    print(" ⚙️ [06A] INICIANDO MOTOR DE PARTIDOS Y RACHAS ⚙️")
    print("=======================================================")
    
    realidad = cargar_realidad()
    if not realidad:
        print("❌ Error: Falta realidad_oficial.json. Ejecuta el script 05.")
        return

    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p.name for p in dir_participantes.iterdir() if p.is_dir()]
    
    informe_06a = {}
    
    for jugador in jugadores:
        informe_06a[jugador] = {
            "puntos_partidos": 0,
            "total_aciertos_1x2": 0,
            "total_aciertos_exactos": 0,
            "historial_jornadas": {} 
        }
        
        # --- INICIO LIBRO DE CUENTAS PERSONAL ---
        libro_cuentas = {
            "jugador": jugador.replace('_', ' ').title(),
            "puntos_totales": 0.0,
            "desglose_partidos": {},
            "desglose_jornadas": {},
            "premios_finales": {}
        }
        # ----------------------------------------

        # 1. PROCESAR FASE DE GRUPOS
        ruta_base = dir_participantes / jugador / "pronosticos" / "grupos" / f"{jugador}_base.json"
        if ruta_base.exists():
            with open(ruta_base, 'r', encoding='utf-8') as f:
                porra_base = json.load(f)
                
            for grupo, partidos_reales in realidad.get("fase_grupos", {}).items():
                partidos_predichos = porra_base.get("fase_grupos", {}).get(grupo, [])
                
                for p_real in partidos_reales:
                    if p_real.get("estado", "notstarted") == "notstarted": continue
                    
                    for p_pred in partidos_predichos:
                        if p_pred.get("local") == p_real.get("local") and p_pred.get("visitante") == p_real.get("visitante"):
                            # USO DE .GET() PARA EVITAR KEYERRORS
                            pts, is_1x2, is_ex, mult = calcular_puntos_partido(
                                int(p_pred.get("goles_local", 0)), int(p_pred.get("goles_visitante", 0)),
                                int(p_real.get("goles_local", 0)), int(p_real.get("goles_visitante", 0))
                            )
                            
                            informe_06a[jugador]["puntos_partidos"] += pts
                            if is_1x2: informe_06a[jugador]["total_aciertos_1x2"] += 1
                            if is_ex: informe_06a[jugador]["total_aciertos_exactos"] += 1
                            
                            clave_partido = f"{p_real['local']}_vs_{p_real['visitante']}"
                            informe_06a[jugador]["historial_jornadas"][clave_partido] = {"acierto_1x2": is_1x2}
                            
                            libro_cuentas["desglose_partidos"][clave_partido] = {
                                "fase": "grupos",
                                "acierto_1x2": is_1x2,
                                "acierto_exacto": is_ex,
                                "multiplicador_aplicado": mult,
                                "puntos_conseguidos": pts
                            }
                            break

        # 2. PROCESAR ELIMINATORIAS (Evaluación por Índice y Mapeo Correcto de Finales)
        for fase in FASES_ORDENADAS:
            ruta_fase = dir_participantes / jugador / "pronosticos" / "eliminatorias" / fase / f"{fase}.json"
            
            predicciones = []
            if ruta_fase.exists():
                with open(ruta_fase, 'r', encoding='utf-8') as f:
                    porra_fase = json.load(f)
                predicciones = porra_fase.get("predicciones", {}).get(fase, [])
                
            # Mapeo de la realidad para juntar 3º puesto y final
            reales = []
            if fase == "finales":
                reales.extend(realidad.get("eliminatorias", {}).get("tercer_puesto", []))
                reales.extend(realidad.get("eliminatorias", {}).get("final", []))
            else:
                reales = realidad.get("eliminatorias", {}).get(fase, [])
                
            # Evaluamos por índice cronológico
            for i, p_real in enumerate(reales):
                if p_real.get("estado", "notstarted") == "notstarted": continue
                
                pts, is_1x2, is_ex, mult = 0, False, False, 1.0
                racha_l, racha_v = 0, 0
                racha_txt = "Fallo de cruce"
                
                if i < len(predicciones):
                    p_pred = predicciones[i]
                    
                    if p_pred.get("local") == p_real.get("local") and p_pred.get("visitante") == p_real.get("visitante"):
                        racha_l = calcular_racha_equipo(jugador, p_real["local"], fase)
                        racha_v = calcular_racha_equipo(jugador, p_real["visitante"], fase)
                        
                        pts, is_1x2, is_ex, mult = calcular_puntos_partido(
                            int(p_pred.get("goles_local", 0)), int(p_pred.get("goles_visitante", 0)),
                            int(p_real.get("goles_local", 0)), int(p_real.get("goles_visitante", 0)),
                            racha_loc=racha_l, racha_vis=racha_v
                        )
                        racha_txt = f"{racha_l} ({p_real['local']}) / {racha_v} ({p_real['visitante']})"
                        
                informe_06a[jugador]["puntos_partidos"] += pts
                if is_1x2: informe_06a[jugador]["total_aciertos_1x2"] += 1
                if is_ex: informe_06a[jugador]["total_aciertos_exactos"] += 1
                
                # REGISTRAMOS SIEMPRE (incluso con 0 puntos si falló los equipos)
                clave_partido = f"ID_{p_real['id_partido']}"
                informe_06a[jugador]["historial_jornadas"][clave_partido] = {"acierto_1x2": is_1x2}

                libro_cuentas["desglose_partidos"][clave_partido] = {
                    "fase": fase,
                    "acierto_1x2": is_1x2,
                    "acierto_exacto": is_ex,
                    "multiplicador_aplicado": mult,
                    "racha_detectada": racha_txt,
                    "puntos_conseguidos": pts
                }

        # Guardar el Libro de Cuentas Personal de este jugador
        ruta_libro = dir_participantes / jugador / "estadisticas" / "historial_puntos.json"
        guardar_json(libro_cuentas, ruta_libro)

    # 3. GUARDAR INFORME PARA 06B Y 06C
    ruta_guardado = ROOT_DIR / "data" / "resultados" / "reporte_06a_partidos.json"
    guardar_json(informe_06a, ruta_guardado)
        
    print(f"✅ Informe 06a generado con éxito: {ruta_guardado.relative_to(ROOT_DIR)}")
    print("📔 Creado el 'Libro de Cuentas' en la carpeta de estadísticas de cada jugador.")

if __name__ == "__main__":
    ejecutar_06a_motor_partidos()
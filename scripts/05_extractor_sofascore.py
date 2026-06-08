import sys
import json
from pathlib import Path
from curl_cffi import requests

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# ====================================================================
# IDs DEL MUNDIAL 2026 (SofaScore)
# ====================================================================
UNIQUE_TOURNAMENT_ID = 16
SEASON_ID = 58210  # ID actual de SofaScore para 2026. Revisar días antes del torneo.

# Diccionario traductor base (Se ampliará cuando se clasifiquen los 48 equipos)
TRADUCCIONES = {
    "Netherlands": "Países Bajos", "USA": "Estados Unidos", "Argentina": "Argentina",
    "Australia": "Australia", "France": "Francia", "Poland": "Polonia",
    "England": "Inglaterra", "Senegal": "Senegal", "Japan": "Japón",
    "Croatia": "Croacia", "Brazil": "Brasil", "South Korea": "Corea del Sur",
    "Morocco": "Marruecos", "Spain": "España", "Portugal": "Portugal",
    "Switzerland": "Suiza", "Germany": "Alemania", "Belgium": "Bélgica",
    "Cameroon": "Camerún", "Canada": "Canadá", "Costa Rica": "Costa Rica",
    "Denmark": "Dinamarca", "Ecuador": "Ecuador", "Ghana": "Ghana",
    "Iran": "Irán", "Mexico": "México", "Qatar": "Qatar",
    "Saudi Arabia": "Arabia Saudí", "Serbia": "Serbia", "Tunisia": "Túnez",
    "Uruguay": "Uruguay", "Wales": "Gales"
}

def obtener_partidos_mundial():
    headers = {
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/",
        "Accept-Language": "es-ES,es;q=0.9" # Forzamos castellano
    }
    
    print(f"🔍 Buscando partidos del Mundial 2026 (Torneo: {UNIQUE_TOURNAMENT_ID}, Temp: {SEASON_ID})...")
    
    todos_los_eventos = []
    pagina = 0
    
    while True:
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{UNIQUE_TOURNAMENT_ID}/season/{SEASON_ID}/events/last/{pagina}"
        try:
            # Usamos curl_cffi para saltarnos la protección antibots
            respuesta = requests.get(url, headers=headers, impersonate="chrome110")
            if respuesta.status_code != 200: 
                break
                
            datos = respuesta.json()
            eventos_pagina = datos.get('events', [])
            todos_los_eventos.extend(eventos_pagina)
            
            # Si no hay más páginas, cortamos el bucle
            if not datos.get('hasNextPage', False) or not eventos_pagina: 
                break
            pagina += 1
            
        except Exception as e:
            print(f"❌ Error de conexión con SofaScore: {e}")
            break
            
    print(f"✅ Extraídos {len(todos_los_eventos)} partidos en bruto del servidor.")
    return todos_los_eventos

def estructurar_resultados_oficiales(eventos_crudos):
    resultados = {
        "fase_grupos": {},
        "clasificados_a_dieciseisavos": [],
        "eliminatorias": {
            "dieciseisavos": [], "octavos": [], "cuartos": [],
            "semifinales": [], "tercer_puesto": [], "final": []
        }
    }
    
    partidos_procesados = 0
    
    for evento in eventos_crudos:
        estado = evento.get('status', {}).get('type')
        
        # Mapeamos nombres blindados por el diccionario
        local_eng = evento.get('homeTeam', {}).get('name', 'TBD')
        visitante_eng = evento.get('awayTeam', {}).get('name', 'TBD')
        local = TRADUCCIONES.get(local_eng, local_eng)
        visitante = TRADUCCIONES.get(visitante_eng, visitante_eng)
        
        score_home = evento.get('homeScore', {})
        score_away = evento.get('awayScore', {})
        
        penaltis_loc = score_home.get('penalties', 0)
        penaltis_vis = score_away.get('penalties', 0)
        
        # Extraemos goles reales (restando penaltis) como STRINGS. Si no ha empezado, dejamos un vacío.
        goles_loc_str = str(score_home.get('current', 0) - penaltis_loc) if estado != 'notstarted' else ""
        goles_vis_str = str(score_away.get('current', 0) - penaltis_vis) if estado != 'notstarted' else ""
        
        pasa = "TBD"
        if estado == 'finished':
            if goles_loc_str and goles_vis_str:
                if int(goles_loc_str) > int(goles_vis_str): pasa = local
                elif int(goles_vis_str) > int(goles_loc_str): pasa = visitante
                else:
                    if penaltis_loc > penaltis_vis: pasa = local
                    elif penaltis_vis > penaltis_loc: pasa = visitante
                    else: pasa = "Empate"
        
        nombre_ronda = evento.get('roundInfo', {}).get('name', '').lower()
        
        # 1. FASE DE GRUPOS
        if not ("16" in nombre_ronda or "quarter" in nombre_ronda or "semi" in nombre_ronda or "final" in nombre_ronda or "3rd" in nombre_ronda or "1/8" in nombre_ronda or "1/4" in nombre_ronda or "32" in nombre_ronda):
            grupo_crudo = evento.get('tournament', {}).get('groupName', 'Group Desconocido')
            grupo = grupo_crudo.replace("Group", "Grupo").strip()
            
            if grupo not in resultados["fase_grupos"]:
                resultados["fase_grupos"][grupo] = []
                
            resultados["fase_grupos"][grupo].append({
                "local": local,
                "visitante": visitante,
                "goles_local": goles_loc_str,
                "goles_visitante": goles_vis_str,
                "estado": estado
            })
            
        # 2. ELIMINATORIAS (Sin IDs numéricos, pura cadena de texto)
        else:
            partido_elim = {
                "local": local,
                "visitante": visitante,
                "pasa": pasa,
                "estado": estado,
                "goles_local": goles_loc_str,
                "goles_visitante": goles_vis_str
            }
            
            if "32" in nombre_ronda or "1/16" in nombre_ronda or "dieciseisavos" in nombre_ronda:
                resultados["eliminatorias"]["dieciseisavos"].append(partido_elim)
            elif "16" in nombre_ronda or "1/8" in nombre_ronda or "octavos" in nombre_ronda:
                resultados["eliminatorias"]["octavos"].append(partido_elim)
            elif "quarter" in nombre_ronda or "1/4" in nombre_ronda or "cuartos" in nombre_ronda:
                resultados["eliminatorias"]["cuartos"].append(partido_elim)
            elif "semi" in nombre_ronda or "1/2" in nombre_ronda:
                resultados["eliminatorias"]["semifinales"].append(partido_elim)
            elif "3rd" in nombre_ronda or "third" in nombre_ronda or "tercer" in nombre_ronda:
                partido_elim["ganador"] = pasa 
                resultados["eliminatorias"]["tercer_puesto"].append(partido_elim)
            elif "final" in nombre_ronda:
                partido_elim["ganador"] = pasa
                resultados["eliminatorias"]["final"].append(partido_elim)

        partidos_procesados += 1

    # Ordenar los grupos de la A a la Z
    resultados["fase_grupos"] = dict(sorted(resultados["fase_grupos"].items()))
    
    # Deducir clasificados leyendo la primera ronda eliminatoria
    ronda_corte = "dieciseisavos" if resultados["eliminatorias"]["dieciseisavos"] else "octavos"
    equipos_clasificados = set()
    for p in resultados["eliminatorias"][ronda_corte]:
        if p["local"] != "TBD": equipos_clasificados.add(p["local"])
        if p["visitante"] != "TBD": equipos_clasificados.add(p["visitante"])
        
    resultados["clasificados_a_dieciseisavos"] = sorted(list(equipos_clasificados))
    
    print(f"📊 Se han estructurado {partidos_procesados} partidos en el formato oficial temporal.")
    return resultados

def hacer_update_selectivo(realidad_actual, resultados_nuevos):
    """
    Actualiza la realidad oficial conservando fechas, id_partidos y placeholders.
    Solo sobrescribe goles, estado y el equipo que pasa SI hay coincidencia de nombres.
    """
    # 1. Actualizar Grupos
    for grupo, partidos_actuales in realidad_actual.get("fase_grupos", {}).items():
        partidos_nuevos = resultados_nuevos.get("fase_grupos", {}).get(grupo, [])
        for p_act in partidos_actuales:
            for p_nuevo in partidos_nuevos:
                if (p_act.get("local") == p_nuevo["local"] and p_act.get("visitante") == p_nuevo["visitante"]) or \
                   (p_act.get("local") == p_nuevo["visitante"] and p_act.get("visitante") == p_nuevo["local"]):
                    
                    if p_act.get("local") == p_nuevo["local"]:
                        p_act["goles_local"] = p_nuevo["goles_local"]
                        p_act["goles_visitante"] = p_nuevo["goles_visitante"]
                    else:
                        p_act["goles_local"] = p_nuevo["goles_visitante"]
                        p_act["goles_visitante"] = p_nuevo["goles_local"]
                        
                    p_act["estado"] = p_nuevo["estado"]
                    break

    # 2. Actualizar Eliminatorias
    for fase, partidos_actuales in realidad_actual.get("eliminatorias", {}).items():
        partidos_nuevos = resultados_nuevos.get("eliminatorias", {}).get(fase, [])
        for p_act in partidos_actuales:
            for p_nuevo in partidos_nuevos:
                if (p_act.get("local") == p_nuevo["local"] and p_act.get("visitante") == p_nuevo["visitante"]) or \
                   (p_act.get("local") == p_nuevo["visitante"] and p_act.get("visitante") == p_nuevo["local"]):
                    
                    if p_act.get("local") == p_nuevo["local"]:
                        p_act["goles_local"] = p_nuevo["goles_local"]
                        p_act["goles_visitante"] = p_nuevo["goles_visitante"]
                        p_act["pasa"] = p_nuevo.get("pasa", "TBD")
                        if "ganador" in p_nuevo: p_act["ganador"] = p_nuevo["ganador"]
                    else:
                        p_act["goles_local"] = p_nuevo["goles_visitante"]
                        p_act["goles_visitante"] = p_nuevo["goles_local"]
                        p_act["pasa"] = p_nuevo.get("pasa", "TBD")
                        if "ganador" in p_nuevo: p_act["ganador"] = p_nuevo["ganador"]
                        
                    p_act["estado"] = p_nuevo["estado"]
                    break

    # 3. Actualizar clasificados si los hay
    if resultados_nuevos.get("clasificados_a_dieciseisavos"):
        realidad_actual["clasificados_a_dieciseisavos"] = resultados_nuevos["clasificados_a_dieciseisavos"]
        
    return realidad_actual

def ejecutar_05_scraper():
    print("=======================================================")
    print(" 📥 [05] ACTUALIZANDO REALIDAD DESDE SOFASCORE 📥")
    print("=======================================================")
    
    eventos_crudos = obtener_partidos_mundial()
    if not eventos_crudos: 
        print("⚠️ No hay datos en SofaScore para este torneo todavía. Manteniendo realidad anterior.")
        return
        
    resultados_nuevos = estructurar_resultados_oficiales(eventos_crudos)
    
    # Preparar la carga del estado semilla
    carpeta_resultados = ROOT_DIR / "data" / "resultados"
    carpeta_resultados.mkdir(parents=True, exist_ok=True)
    ruta_guardado = carpeta_resultados / "realidad_oficial.json"
    
    realidad_actual = {"fase_grupos": {}, "clasificados_a_dieciseisavos": [], "eliminatorias": {}}
    if ruta_guardado.exists():
        with open(ruta_guardado, 'r', encoding='utf-8') as f:
            try:
                realidad_actual = json.load(f)
            except json.JSONDecodeError:
                pass
                
    # Realizar el merge respetando el estado semilla
    realidad_actualizada = hacer_update_selectivo(realidad_actual, resultados_nuevos)
    
    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(realidad_actualizada, f, ensure_ascii=False, indent=4)
        
    print(f"💾 ¡Realidad oficial actualizada (Update Selectivo) con éxito en: {ruta_guardado.relative_to(ROOT_DIR)}")

if __name__ == "__main__":
    ejecutar_05_scraper()
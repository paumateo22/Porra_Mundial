import sys
import time
import json
from pathlib import Path
from curl_cffi import requests

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from utils.helpers import inicializar_estructura, guardar_json

def cargar_partidos_jugados():
    """
    Lee la realidad_oficial.json generada por el script 05 para sacar
    los IDs de los partidos que ya han empezado o terminado.
    """
    ruta_oficial = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    if not ruta_oficial.exists():
        print("❌ Error: No existe 'realidad_oficial.json'. Ejecuta el script 05 primero.")
        return []
        
    with open(ruta_oficial, 'r', encoding='utf-8') as f:
        datos = json.load(f)
        
    lista_ids = []
    
    # Recoger IDs de Fase de Grupos
    for grupo, partidos in datos.get("fase_grupos", {}).items():
        for p in partidos:
            if p["estado"] != "notstarted":
                lista_ids.append((p["id_sofascore"], p["local"], p["visitante"]))
                
    # Recoger IDs de Eliminatorias
    for fase, partidos in datos.get("eliminatorias", {}).items():
        for p in partidos:
            if p["estado"] != "notstarted":
                lista_ids.append((p["id_sofascore"], p["local"], p["visitante"]))
                
    return lista_ids

def extraer_stats_partido(match_id, equipo_local, equipo_visitante):
    """
    Extrae las estadísticas de los jugadores de un partido usando tu lógica de LaLiga.
    """
    url = f"https://api.sofascore.com/api/v1/event/{match_id}/lineups"
    headers = {
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/"
    }
    
    try:
        respuesta = requests.get(url, headers=headers, impersonate="chrome110")
        if respuesta.status_code != 200: return []
            
        datos = respuesta.json()
        jugadores_partido = []
        
        for bando in ['home', 'away']:
            if bando not in datos or 'players' not in datos[bando]:
                continue
                
            equipo_real = equipo_local if bando == 'home' else equipo_visitante
            
            for item in datos[bando]['players']:
                jugador = item.get('player', {})
                stats = item.get('statistics', {})
                
                nombre = jugador.get('name', 'Desconocido')
                posicion = item.get('position', 'Desconocido')
                minutos = stats.get('minutesPlayed', 0)
                
                if minutos > 0:
                    jugadores_partido.append({
                        "nombre": nombre,
                        "equipo": equipo_real,
                        "posicion": posicion,
                        "goles": stats.get('goals', 0),
                        "paradas": stats.get('saves', 0),
                        "asistencias": stats.get('goalAssist', 0),
                        "rojas": stats.get('redCards', 0)
                    })
                    
        return jugadores_partido
        
    except Exception as e:
        print(f"⚠️ Error extrayendo stats del partido {match_id}: {e}")
        return []

def minar_estadisticas_mundial():
    print("=======================================================")
    print(" ⛏️ INICIANDO EXTRACCIÓN DE STATS DE JUGADORES ⛏️")
    print("=======================================================")
    
    inicializar_estructura()
    partidos_a_procesar = cargar_partidos_jugados()
    
    if not partidos_a_procesar:
        print("⚠️ No hay partidos jugados todavía en el archivo oficial.")
        return
        
    print(f"📊 Se van a analizar {len(partidos_a_procesar)} partidos...")
    
    # Diccionario maestro para acumular stats de todo el torneo
    # Formato clave: "Mbappé_France"
    estadisticas_acumuladas = {}
    
    for i, (match_id, local, visitante) in enumerate(partidos_a_procesar, 1):
        print(f"   [{i}/{len(partidos_a_procesar)}] Analizando: {local} vs {visitante}...")
        
        jugadores = extraer_stats_partido(match_id, local, visitante)
        
        for j in jugadores:
            clave = f"{j['nombre']}_{j['equipo']}"
            
            if clave not in estadisticas_acumuladas:
                estadisticas_acumuladas[clave] = {
                    "nombre": j['nombre'],
                    "equipo": j['equipo'],
                    "posicion": j['posicion'],
                    "goles_totales": 0,
                    "paradas_totales": 0,
                    "asistencias_totales": 0,
                    "rojas_totales": 0
                }
                
            # Sumamos lo que ha hecho en este partido al total de su torneo
            estadisticas_acumuladas[clave]["goles_totales"] += j['goles']
            estadisticas_acumuladas[clave]["paradas_totales"] += j['paradas']
            estadisticas_acumuladas[clave]["asistencias_totales"] += j['asistencias']
            estadisticas_acumuladas[clave]["rojas_totales"] += j['rojas']
            
        time.sleep(1) # Respiro para no enfadar a SofaScore
        
    # Convertimos el diccionario a una lista para guardarlo limpio
    lista_final_jugadores = list(estadisticas_acumuladas.values())
    
    # Ordenamos por goles por defecto para que sea más fácil de leer (Ranking de Pichichis)
    lista_final_jugadores.sort(key=lambda x: x["goles_totales"], reverse=True)
    
    guardar_json(lista_final_jugadores, "resultados", "estadisticas_jugadores.json")
    
    print("=======================================================")
    print(" 🏁 EXTRACCIÓN DE JUGADORES FINALIZADA")
    print("=======================================================")

if __name__ == "__main__":
    minar_estadisticas_mundial()
import sys
import json
import os
from pathlib import Path
from curl_cffi import requests

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# IDs del Mundial 2026 en SofaScore (Ajustar cuando SofaScore lo cree oficialmente, usamos el 16 de tu enlace por ahora)
UNIQUE_TOURNAMENT_ID = 16
SEASON_ID = 58210  # ID sacado de tu URL: #id:58210

def obtener_partidos_mundial():
    """
    Se conecta a la API de SofaScore y extrae todos los partidos del Mundial 2026.
    """
    # Endpoint para sacar todos los eventos de un torneo en una temporada
    url = f"https://api.sofascore.com/api/v1/unique-tournament/{UNIQUE_TOURNAMENT_ID}/season/{SEASON_ID}/events"
    
    headers = {
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/"
    }
    
    print(f"🔍 Buscando partidos del Mundial 2026 (Torneo: {UNIQUE_TOURNAMENT_ID}, Temp: {SEASON_ID})...")
    
    try:
        # Usamos curl_cffi para saltarnos la protección de Cloudflare de SofaScore
        respuesta = requests.get(url, headers=headers, impersonate="chrome110")
        
        if respuesta.status_code != 200:
            print(f"❌ Error al obtener los partidos: Estado {respuesta.status_code}")
            return []
            
        datos = respuesta.json()
        eventos = datos.get('events', [])
        
        print(f"✅ ¡Éxito! Encontrados {len(eventos)} partidos en el servidor.")
        return eventos
        
    except Exception as e:
        print(f"❌ Error inesperado en el crawler: {e}")
        return []

def estructurar_resultados_oficiales(eventos_crudos):
    """
    Filtra los eventos crudos, se queda solo con los partidos ya jugados (o en juego)
    y los estructura en nuestro formato estándar.
    """
    resultados = {
        "fase_grupos": {},
        "eliminatorias": {
            "dieciseisavos": [],
            "octavos": [],
            "cuartos": [],
            "semifinales": [],
            "tercer_puesto": [],
            "final": []
        }
    }
    
    partidos_procesados = 0
    
    for evento in eventos_crudos:
        # Extraemos datos clave
        estado = evento.get('status', {}).get('type')
        
        # Si el partido no ha empezado ('notstarted'), no nos sirve para dar puntos todavía
        if estado == 'notstarted':
            continue
            
        # Equipos
        local = evento.get('homeTeam', {}).get('name', 'Desconocido')
        visitante = evento.get('awayTeam', {}).get('name', 'Desconocido')
        
        # Goles (si el partido está en curso, cogerá los goles actuales. Si terminó, los finales)
        goles_loc = evento.get('homeScore', {}).get('current', 0)
        goles_vis = evento.get('awayScore', {}).get('current', 0)
        
        # Ganador (calculado para simplificar la vida al motor de puntuaciones)
        ganador = local if goles_loc > goles_vis else (visitante if goles_vis > goles_loc else "Empate")
        
        # En SofaScore, las fases se distinguen por el 'roundInfo'
        ronda_info = evento.get('roundInfo', {})
        nombre_ronda = ronda_info.get('name', '')
        
        partido_formateado = {
            "id_sofascore": evento.get('id'),
            "local": local,
            "visitante": visitante,
            "goles_local": goles_loc,
            "goles_visitante": goles_vis,
            "ganador": ganador,
            "estado": estado # 'finished' o 'inprogress'
        }
        
        # --- CLASIFICADOR DE FASES ---
        # (Lógica estándar de SofaScore para Mundiales)
        if "Group" in nombre_ronda:
            grupo = nombre_ronda.replace("Round", "").strip() # Ej: "Group A"
            if grupo not in resultados["fase_grupos"]:
                resultados["fase_grupos"][grupo] = []
            resultados["fase_grupos"][grupo].append(partido_formateado)
            
        elif "Round of 32" in nombre_ronda or "1/16" in nombre_ronda:
            resultados["eliminatorias"]["dieciseisavos"].append(partido_formateado)
            
        elif "Round of 16" in nombre_ronda or "1/8" in nombre_ronda:
            resultados["eliminatorias"]["octavos"].append(partido_formateado)
            
        elif "Quarter" in nombre_ronda or "1/4" in nombre_ronda:
            resultados["eliminatorias"]["cuartos"].append(partido_formateado)
            
        elif "Semi" in nombre_ronda or "1/2" in nombre_ronda:
            resultados["eliminatorias"]["semifinales"].append(partido_formateado)
            
        elif "3rd" in nombre_ronda or "Third" in nombre_ronda:
            resultados["eliminatorias"]["tercer_puesto"].append(partido_formateado)
            
        elif "Final" in nombre_ronda:
            resultados["eliminatorias"]["final"].append(partido_formateado)
            
        partidos_procesados += 1
        
    print(f"📊 Se han estructurado {partidos_procesados} partidos jugados/en juego.")
    return resultados

def extraer_realidad_mundial():
    print("=======================================================")
    print(" 🚀 INICIANDO EXTRACCIÓN DE RESULTADOS OFICIALES 🚀")
    print("=======================================================")
    
    # 1. Bajar todo el JSON crudo del Mundial
    eventos_crudos = obtener_partidos_mundial()
    
    if not eventos_crudos:
        print("⚠️ No se pudo obtener el calendario. Abortando.")
        return
        
    # 2. Convertirlo a nuestra estructura de la Porra
    resultados_limpios = estructurar_resultados_oficiales(eventos_crudos)
    
    # 3. Preparar la carpeta de guardado
    carpeta_resultados = ROOT_DIR / "data" / "resultados"
    carpeta_resultados.mkdir(parents=True, exist_ok=True)
    
    ruta_guardado = carpeta_resultados / "realidad_oficial.json"
    
    # 4. Guardarlo como el archivo maestro
    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(resultados_limpios, f, ensure_ascii=False, indent=4)
        
    print(f"💾 Realidad oficial guardada en: {ruta_guardado.relative_to(ROOT_DIR)}")
    print("=======================================================")
    print(" 🏁 EXTRACCIÓN DE SOFASCORE FINALIZADA")
    print("=======================================================")

if __name__ == "__main__":
    extraer_realidad_mundial()
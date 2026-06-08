import sys
import csv
import json
import requests
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Añadimos la raíz del proyecto al "Path"
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def crear_estructura_participante(nombre_limpio):
    """
    Crea el árbol completo de carpetas para un jugador nuevo dentro de 'participantes/'
    """
    base_dir = ROOT_DIR / "participantes" / nombre_limpio / "pronosticos"
    
    # Creamos todas las carpetas necesarias para el futuro
    (base_dir / "grupos").mkdir(parents=True, exist_ok=True)
    (base_dir / "eliminatorias" / "dieciseisavos").mkdir(parents=True, exist_ok=True)
    (base_dir / "eliminatorias" / "octavos").mkdir(parents=True, exist_ok=True)
    (base_dir / "eliminatorias" / "cuartos").mkdir(parents=True, exist_ok=True)
    (base_dir / "eliminatorias" / "semifinales").mkdir(parents=True, exist_ok=True)
    (base_dir / "eliminatorias" / "finales").mkdir(parents=True, exist_ok=True)
    
    # NUEVO: Carpeta para guardar los premios estáticos del formulario
    (base_dir / "premios").mkdir(parents=True, exist_ok=True)
    
    return base_dir

def guardar_premios_formulario(nombre_limpio, premios_dict):
    """
    Guarda los premios del Google Forms en un JSON dedicado.
    """
    ruta_premios = ROOT_DIR / "participantes" / nombre_limpio / "pronosticos" / "premios" / "premios_formulario.json"
    with open(ruta_premios, 'w', encoding='utf-8') as f:
        json.dump(premios_dict, f, ensure_ascii=False, indent=4)
    print(f"🏅 Premios subjetivos guardados para {nombre_limpio.title()}.")

def extraer_porra_infobae(nombre, url_pronostico, premios_dict):
    """
    Extrae los datos de Infobae para el pronóstico inicial (fase de grupos y cuadro).
    """
    nombre_limpio = nombre.lower().replace(' ', '_')
    carpeta_pronosticos = crear_estructura_participante(nombre_limpio)
    
    # Guardamos/Actualizamos los premios del formulario siempre por si editaron su respuesta
    guardar_premios_formulario(nombre_limpio, premios_dict)
    
    ruta_archivo_json = carpeta_pronosticos / "grupos" / f"{nombre_limpio}_base.json"
    
    # Comprobación de existencia: Si ya lo tenemos, nos lo saltamos
    if ruta_archivo_json.exists():
        print(f"✅ {nombre.title()}: Pronóstico base ya descargado. Saltando extracción de grupos...")
        return True

    print(f"\n🚀 Nuevo participante detectado. Extrayendo grupos de: {nombre.title()}...")
    
    # 1. Extraer el predict_id de la URL
    parsed_url = urlparse(url_pronostico)
    query_params = parse_qs(parsed_url.query)
    
    if 'predict' not in query_params:
        print(f"❌ Error: No se encontró la ID de predicción en la URL para {nombre.title()}.")
        return False
        
    predict_id = query_params['predict'][0]
    
    # 2. Descargar el JSON de la API
    api_url = f"https://storage.googleapis.com/arc-buckets/web-components/soccer/wc-2026-predict/data/{predict_id}.json"
    respuesta = requests.get(api_url)
    
    if respuesta.status_code != 200:
        print(f"❌ Error al descargar los datos para {nombre.title()}. HTTP Status: {respuesta.status_code}")
        return False
        
    datos_crudos = respuesta.json()
    
    # 3. Estructurar el JSON
    porra_estructurada = {
        "participante": nombre,
        "fase_prediccion": "grupos_base",
        "campeon": datos_crudos.get("winner", {}).get("mode-score-input", ""),
        "fase_grupos": {},
        "clasificados_a_dieciseisavos": [],
        "eliminatorias": {
            "dieciseisavos": [],
            "octavos": [],
            "cuartos": [],
            "semifinales": [],
            "tercer_puesto": [],
            "final": []
        }
    }
    
    # Procesar Fase de Grupos
    for partido in datos_crudos.get("predictedMatches", []):
        grupo = partido.get("groupName", "Sin Grupo")
        if grupo not in porra_estructurada["fase_grupos"]:
            porra_estructurada["fase_grupos"][grupo] = []
            
        porra_estructurada["fase_grupos"][grupo].append({
            "local": partido["homeTeam"]["nombre"],
            "visitante": partido["awayTeam"]["nombre"],
            "goles_local": partido.get("homeScore"),
            "goles_visitante": partido.get("awayScore")
        })
        
    # Extraer clasificados
    for etapa in datos_crudos.get("tournamentData", []):
        if etapa["nombre"] == "Fase de Grupos":
            for grupo in etapa["grupos"]:
                for equipo in grupo["equipos"]:
                    if equipo.get("qualified") == True:
                        porra_estructurada["clasificados_a_dieciseisavos"].append(equipo["nombre"])
                        
    # Procesar Eliminatorias
    partidos_eliminatorias = datos_crudos.get("matches", {}).get("mode-score-input", {})
    
    for match_id_str, match_data in partidos_eliminatorias.items():
        if not match_id_str.isdigit(): continue
            
        match_id = int(match_id_str)
        local = match_data.get("local", "")
        visitante = match_data.get("visitor", "")
        ganador = match_data.get("winner", "")
        
        if not local or not visitante: continue
            
        detalle_partido = {"id_partido": match_id, "local": local, "visitante": visitante, "pasa": ganador}
        
        if 73 <= match_id <= 88: porra_estructurada["eliminatorias"]["dieciseisavos"].append(detalle_partido)
        elif 89 <= match_id <= 96: porra_estructurada["eliminatorias"]["octavos"].append(detalle_partido)
        elif 97 <= match_id <= 100: porra_estructurada["eliminatorias"]["cuartos"].append(detalle_partido)
        elif 101 <= match_id <= 102: porra_estructurada["eliminatorias"]["semifinales"].append(detalle_partido)
        elif match_id == 103: porra_estructurada["eliminatorias"]["tercer_puesto"].append(detalle_partido)
        elif match_id == 104: porra_estructurada["eliminatorias"]["final"].append(detalle_partido)

    # 4. Guardar directamente en la carpeta del participante
    with open(ruta_archivo_json, 'w', encoding='utf-8') as f:
        json.dump(porra_estructurada, f, ensure_ascii=False, indent=4)
        
    print(f"💾 Guardado con éxito en: {ruta_archivo_json.relative_to(ROOT_DIR)}")
    return True

def procesar_registro_masivo():
    """
    Lee el archivo CSV de Google Forms y registra los pronósticos y premios.
    """
    ruta_csv = ROOT_DIR / "inscripcion.csv"
    
    if not ruta_csv.exists():
        print(f"❌ Error: No se encuentra el archivo '{ruta_csv.name}' en la raíz del proyecto.")
        return
        
    print(f"--- 📋 INICIANDO LECTURA DE GOOGLE FORMS ({ruta_csv.name}) ---")
    
    with open(ruta_csv, mode='r', encoding='utf-8') as archivo_csv:
        # Usamos DictReader para leer directamente por el nombre de la columna exportada
        lector = csv.DictReader(archivo_csv)
        
        for fila in lector:
            nombre = fila.get('Nombre', '').strip()
            url = fila.get('Pronóstico fase de grupos (pega el enlace)', '').strip()
            
            # Recolectamos las respuestas de los premios extra
            premios_dict = {
                "balon_oro": fila.get("Balón de Oro del Torneo", "").strip(),
                "guante_oro": fila.get("Guante de Oro del Torneo", "").strip(),
                "bota_oro": fila.get("Bota de Oro del Torneo", "").strip(),
                "mejor_joven": fila.get("Jugador Joven del Torneo", "").strip(),
                "gol_torneo": fila.get("Jugador que marque el gol del torneo", "").strip()
            }
            
            if nombre and url:
                extraer_porra_infobae(nombre, url, premios_dict)

if __name__ == "__main__":
    procesar_registro_masivo()
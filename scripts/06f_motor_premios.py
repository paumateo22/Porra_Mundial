import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return {}
    with open(ruta, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def guardar_json(datos, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def obtener_podio_real(realidad):
    podio = {"campeon": "", "subcampeon": "", "tercero": "", "cuarto": ""}
    
    # Final
    final = realidad.get("eliminatorias", {}).get("final", [])
    if final and final[0].get("estado") == "finished":
        p = final[0]
        ganador = p.get("pasa", "")
        perdedor = p["visitante"] if p["local"] == ganador else p["local"]
        podio["campeon"] = ganador
        podio["subcampeon"] = perdedor
        
    # Tercer puesto
    tercer = realidad.get("eliminatorias", {}).get("tercer_puesto", [])
    if tercer and tercer[0].get("estado") == "finished":
        p = tercer[0]
        ganador = p.get("pasa", "")
        perdedor = p["visitante"] if p["local"] == ganador else p["local"]
        podio["tercero"] = ganador
        podio["cuarto"] = perdedor
        
    return podio

def extraer_podio_pronosticado(base_pronostico):
    """
    Busca en el archivo base de grupos de cada jugador cómo pronosticó el podio
    analizando la fase de finales / final / tercer puesto en sus pronósticos de eliminatorias.
    """
    podio = {"campeon": "", "subcampeon": "", "tercero": "", "cuarto": ""}
    
    eliminatorias = base_pronostico.get("eliminatorias", {})
    if not eliminatorias:
        eliminatorias = base_pronostico.get("predicciones", {})
        
    # Buscar partidos de finales (final y tercer puesto)
    partidos_finales = []
    if "finales" in eliminatorias:
        partidos_finales = eliminatorias["finales"]
    else:
        if "final" in eliminatorias: partidos_finales.extend(eliminatorias["final"])
        if "tercer_puesto" in eliminatorias: partidos_finales.extend(eliminatorias["tercer_puesto"])
        
    for p in partidos_finales:
        id_p = str(p.get("id_partido", ""))
        local = p.get("local", "")
        visitante = p.get("visitante", "")
        pasa = p.get("pasa", "")
        
        # Identificar si es la Final (id 104 o última) o 3º puesto (id 103)
        if "104" in id_p or (not id_p and len(partidos_finales) == 2 and p == partidos_finales[1]):
            if pasa:
                podio["campeon"] = pasa
                podio["subcampeon"] = visitante if pasa == local else local
        elif "103" in id_p or (not id_p and len(partidos_finales) == 2 and p == partidos_finales[0]):
            if pasa:
                podio["tercero"] = pasa
                podio["cuarto"] = visitante if pasa == local else local
        elif len(partidos_finales) == 1:
            # Si solo hay un partido guardado, asumimos que es la final
            if pasa:
                podio["campeon"] = pasa
                podio["subcampeon"] = visitante if pasa == local else local

    return podio

def ejecutar_06f_premios():
    print("=======================================================")
    print(" 🏅 [06F] INICIANDO MOTOR DE PREMIOS Y PODIO 🏅")
    print("=======================================================")

    settings = cargar_json(ROOT_DIR / "config" / "settings.json")
    realidad = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json")
    premios_oficiales = cargar_json(ROOT_DIR / "data" / "resultados" / "premios_oficiales.json")
    
    habilitadores = settings.get("habilitadores", {})
    pts_conf = settings.get("puntuaciones", {}).get("premios_finales", {})

    podio_real = obtener_podio_real(realidad)
    premios_individuales_reales = premios_oficiales.get("premios_individuales", {})

    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    
    reporte_06f = {}

    for j_dir in jugadores:
        jug = j_dir.name
        
        # Cargar archivo base de pronósticos de grupos donde reside la estructura de eliminatorias
        ruta_base = j_dir / "pronosticos" / "grupos" / f"{jug}_base.json"
        base_pred = cargar_json(ruta_base)
        podio_pred = extraer_podio_pronosticado(base_pred)

        # Cargar formulario de premios individuales
        form_pred = cargar_json(j_dir / "pronosticos" / "premios" / "premios_formulario.json")
        
        pts_podio = 0
        pts_forms = 0
        detalles_podio = {}
        detalles_forms = {}

        # 1. Evaluar Podio Pronosticado desde su base de grupos
        mapeo_podio = [
            ("campeon", "campeon"), 
            ("subcampeon", "subcampeon"), 
            ("tercero", "tercer_puesto"), 
            ("cuarto", "tercer_puesto") 
        ]
        
        for pos, clave_settings in mapeo_podio:
            if habilitadores.get(clave_settings, 1) == 0:
                continue
                
            pts_premio = pts_conf.get(clave_settings, 0)
            pred_val = str(podio_pred.get(pos, "")).strip().lower()
            real_val = str(podio_real.get(pos, "")).strip().lower()
            
            ganado = 0
            if real_val and pred_val == real_val:
                ganado = pts_premio
                pts_podio += ganado
                
            detalles_podio[pos] = {
                "pronostico": podio_pred.get(pos, ""),
                "realidad": podio_real.get(pos, ""),
                "puntos": ganado
            }

        # 2. Evaluar Premios Individuales desde el formulario de premios
        if form_pred:
            for premio in ["bota_oro", "balon_oro", "guante_oro", "mejor_joven", "gol_torneo"]:
                if habilitadores.get(premio, 1) == 0:
                    continue

                pts_premio_indiv = pts_conf.get(premio, 0)
                pred_val = str(form_pred.get(premio, "")).strip().lower()
                
                real_vals_raw = premios_individuales_reales.get(premio, [])
                if isinstance(real_vals_raw, str):
                    real_vals = [real_vals_raw]
                else:
                    real_vals = real_vals_raw
                    
                real_vals_clean = [str(x).strip().lower() for x in real_vals if str(x).strip()]
                
                ganado = 0
                if real_vals_clean and pred_val in real_vals_clean:
                    ganado = pts_premio_indiv
                    pts_forms += ganado
                    
                detalles_forms[premio] = {
                    "pronostico": form_pred.get(premio, ""),
                    "realidad": ", ".join([str(x) for x in real_vals if str(x).strip()]),
                    "puntos": ganado
                }

        reporte_06f[jug] = {
            "puntos_podio": pts_podio,
            "puntos_formulario": pts_forms,
            "detalles": {
                "podio": detalles_podio,
                "individuales": detalles_forms
            }
        }

        # Guardar en el libro de cuentas del jugador
        ruta_libro = j_dir / "estadisticas" / "historial_puntos.json"
        libro = cargar_json(ruta_libro)
        if libro:
            if "premios_finales" not in libro: libro["premios_finales"] = {}
            libro["premios_finales"]["podio"] = {"puntos_conseguidos": pts_podio, "detalles": detalles_podio}
            
            if "formularios" not in libro["premios_finales"]: libro["premios_finales"]["formularios"] = {}
            libro["premios_finales"]["formularios"]["puntos_individuales"] = pts_forms
            libro["premios_finales"]["formularios"]["detalles_individuales"] = detalles_forms
            
            guardar_json(libro, ruta_libro)
            
        print(f"👤 {jug.title()}: Podio (+{pts_podio} pts) | Premios Indiv (+{pts_forms} pts)")

    ruta_reporte = ROOT_DIR / "data" / "resultados" / "reporte_06f_premios.json"
    guardar_json(reporte_06f, ruta_reporte)
    print(f"\n✅ Informe 06f generado con éxito en: {ruta_reporte.relative_to(ROOT_DIR)}")

if __name__ == "__main__":
    ejecutar_06f_premios()

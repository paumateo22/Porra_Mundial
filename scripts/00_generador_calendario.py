import sys
import json
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def generar_indice_jornadas():
    print("--- 📅 GENERANDO ÍNDICE DE JORNADAS DE LA PORRA ---")
    
    # Pillamos el archivo base del participante genérico
    ruta_base = ROOT_DIR / "participantes" / "generico_1" / "pronosticos" / "grupos" / "generico_1_base.json"
    
    if not ruta_base.exists():
        print(f"❌ Error: No se encuentra {ruta_base}. Asegúrate de que el archivo existe.")
        return
        
    with open(ruta_base, 'r', encoding='utf-8') as f:
        datos_infobae = json.load(f)
        
    fase_grupos = datos_infobae.get("fase_grupos", {})
    eliminatorias = datos_infobae.get("eliminatorias", {})
    
    bloque_1 = ["Grupo A", "Grupo B", "Grupo C", "Grupo D", "Grupo E", "Grupo F"]
    bloque_2 = ["Grupo G", "Grupo H", "Grupo I", "Grupo J", "Grupo K", "Grupo L"]
    
    calendario_porra = {
        "J1.1": [], "J1.2": [],
        "J2.1": [], "J2.2": [],
        "J3.1": [], "J3.2": [],
        "dieciseisavos.1": [], "dieciseisavos.2": [],
        "octavos": [],
        "cuartos": [],
        "semifinales": [],
        "finales": []
    }
    
    # --- 1. PROCESAR FASE DE GRUPOS (Mantenemos Local y Visitante) ---
    for nombre_grupo, partidos in fase_grupos.items():
        if nombre_grupo in bloque_1:
            sufijo = ".1"
        elif nombre_grupo in bloque_2:
            sufijo = ".2"
        else:
            continue
            
        for i, partido in enumerate(partidos):
            info_partido = {
                "local": partido["local"],
                "visitante": partido["visitante"],
                "grupo": nombre_grupo
            }
            if i < 2: calendario_porra[f"J1{sufijo}"].append(info_partido)
            elif i < 4: calendario_porra[f"J2{sufijo}"].append(info_partido)
            elif i < 6: calendario_porra[f"J3{sufijo}"].append(info_partido)

    # --- 2. PROCESAR ELIMINATORIAS (Solo ID y Fase) ---
    partidos_dieciseisavos = eliminatorias.get("dieciseisavos", [])
    partidos_dieciseisavos.sort(key=lambda x: x.get("id_partido", 0))
    
    for i, partido in enumerate(partidos_dieciseisavos):
        info_partido = {
            "id_partido": partido["id_partido"],
            "fase": "dieciseisavos"
        }
        if i < 8:
            calendario_porra["dieciseisavos.1"].append(info_partido)
        else:
            calendario_porra["dieciseisavos.2"].append(info_partido)
            
    for fase in ["octavos", "cuartos", "semifinales"]:
        for partido in eliminatorias.get(fase, []):
            calendario_porra[fase].append({
                "id_partido": partido["id_partido"],
                "fase": fase
            })
            
    for partido in eliminatorias.get("tercer_puesto", []):
        calendario_porra["finales"].append({
            "id_partido": partido["id_partido"],
            "fase": "tercer_puesto"
        })
        
    for partido in eliminatorias.get("final", []):
        calendario_porra["finales"].append({
            "id_partido": partido["id_partido"],
            "fase": "final"
        })
                
    # --- 3. GUARDAR RESULTADO ---
    carpeta_config = ROOT_DIR / "config"
    carpeta_config.mkdir(parents=True, exist_ok=True)
    ruta_guardado = carpeta_config / "jornadas.json"
    
    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(calendario_porra, f, ensure_ascii=False, indent=4)
        
    print(f"✅ ¡Índice creado con éxito en: {ruta_guardado.relative_to(ROOT_DIR)}!")

if __name__ == "__main__":
    generar_indice_jornadas()
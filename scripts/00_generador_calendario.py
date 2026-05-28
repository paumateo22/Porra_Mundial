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
    
    # Nombres de grupos en español tal cual vienen en tu JSON
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
    
    # --- 1. PROCESAR FASE DE GRUPOS ---
    for nombre_grupo, partidos in fase_grupos.items():
        # Validar en qué bloque está
        if nombre_grupo in bloque_1:
            sufijo = ".1"
        elif nombre_grupo in bloque_2:
            sufijo = ".2"
        else:
            print(f"⚠️ Grupo no reconocido: {nombre_grupo}")
            continue
            
        # P1 y P2 son de la Jornada 1
        # P3 y P4 son de la Jornada 2
        # P5 y P6 son de la Jornada 3
        for i, partido in enumerate(partidos):
            info_partido = {
                "local": partido["local"],
                "visitante": partido["visitante"],
                "grupo": nombre_grupo
            }
            
            if i < 2:
                calendario_porra[f"J1{sufijo}"].append(info_partido)
            elif i < 4:
                calendario_porra[f"J2{sufijo}"].append(info_partido)
            elif i < 6:
                calendario_porra[f"J3{sufijo}"].append(info_partido)

    # --- 2. PROCESAR ELIMINATORIAS ---
    
    # Dieciseisavos (Divididos en 2 jornadas de 8 partidos por ID)
    partidos_dieciseisavos = eliminatorias.get("dieciseisavos", [])
    # Ordenamos por ID por si acaso no vinieran ordenados del JSON original
    partidos_dieciseisavos.sort(key=lambda x: x.get("id_partido", 0))
    
    for i, partido in enumerate(partidos_dieciseisavos):
        info_partido = {
            "id_partido": partido["id_partido"],
            "local": partido["local"],
            "visitante": partido["visitante"],
            "fase": "dieciseisavos"
        }
        if i < 8:
            calendario_porra["dieciseisavos.1"].append(info_partido)
        else:
            calendario_porra["dieciseisavos.2"].append(info_partido)
            
    # Octavos, Cuartos, Semifinales (Jornadas completas)
    for fase in ["octavos", "cuartos", "semifinales"]:
        for partido in eliminatorias.get(fase, []):
            calendario_porra[fase].append({
                "id_partido": partido["id_partido"],
                "local": partido["local"],
                "visitante": partido["visitante"],
                "fase": fase
            })
            
    # Finales (Agrupamos Tercer Puesto y Final)
    for partido in eliminatorias.get("tercer_puesto", []):
        calendario_porra["finales"].append({
            "id_partido": partido["id_partido"],
            "local": partido["local"],
            "visitante": partido["visitante"],
            "fase": "tercer_puesto"
        })
        
    for partido in eliminatorias.get("final", []):
        calendario_porra["finales"].append({
            "id_partido": partido["id_partido"],
            "local": partido["local"],
            "visitante": partido["visitante"],
            "fase": "final"
        })
                
    # --- 3. GUARDAR RESULTADO ---
    # Preparar carpeta de guardado (Lo metemos en config/ porque es estructural)
    carpeta_config = ROOT_DIR / "config"
    carpeta_config.mkdir(parents=True, exist_ok=True)
    
    ruta_guardado = carpeta_config / "jornadas.json"
    
    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(calendario_porra, f, ensure_ascii=False, indent=4)
        
    print(f"✅ ¡Índice creado con éxito en: {ruta_guardado.relative_to(ROOT_DIR)}!")
    print(f"📊 Partidos en J1.1: {len(calendario_porra['J1.1'])}")
    print(f"📊 Partidos en J1.2: {len(calendario_porra['J1.2'])}")
    print(f"📊 Partidos en J2.1: {len(calendario_porra['J2.1'])}")
    print(f"📊 Partidos en J2.2: {len(calendario_porra['J2.2'])}")
    print(f"📊 Partidos en J3.1: {len(calendario_porra['J3.1'])}")
    print(f"📊 Partidos en J3.2: {len(calendario_porra['J3.2'])}")
    print(f"📊 Partidos en dieciseisavos.1: {len(calendario_porra['dieciseisavos.1'])}")
    print(f"📊 Partidos en dieciseisavos.2: {len(calendario_porra['dieciseisavos.2'])}")
    print(f"📊 Partidos en octavos: {len(calendario_porra['octavos'])}")
    print(f"📊 Partidos en cuartos: {len(calendario_porra['cuartos'])}")
    print(f"📊 Partidos en semifinales: {len(calendario_porra['semifinales'])}")
    print(f"📊 Partidos en finales (Tercer puesto + Final): {len(calendario_porra['finales'])}")

if __name__ == "__main__":
    generar_indice_jornadas()
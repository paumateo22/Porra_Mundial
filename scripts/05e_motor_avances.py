import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def arrastrar_clasificados():
    print("=======================================================")
    print(" ⏩ [05E] MOTOR DE AVANCES (ARRASTRE ELIMINATORIAS) ⏩")
    print("=======================================================")
    
    ruta_realidad = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    
    if not ruta_realidad.exists():
        print("❌ Error: No se encontró realidad_oficial.json")
        return
        
    with open(ruta_realidad, 'r', encoding='utf-8') as f:
        realidad = json.load(f)

    # 1. Crear el diccionario de ganadores y perdedores
    diccionario_avances = {}
    
    for fase, partidos in realidad.get("eliminatorias", {}).items():
        for p in partidos:
            if p.get("estado") == "finished" and p.get("pasa") and p.get("pasa") != "TBD":
                id_p = p.get("id_partido")
                ganador = p["pasa"]
                
                # Averiguar quién es el perdedor (para el 3º y 4º puesto)
                if p["local"] == ganador:
                    perdedor = p["visitante"]
                else:
                    perdedor = p["local"]
                
                diccionario_avances[f"Ganador {id_p}"] = ganador
                diccionario_avances[f"Perdedor {id_p}"] = perdedor

    # 2. Aplicar los avances en los cruces posteriores
    cambios = 0
    for fase, partidos in realidad.get("eliminatorias", {}).items():
        for p in partidos:
            if p["local"] in diccionario_avances:
                p["local"] = diccionario_avances[p["local"]]
                cambios += 1
            if p["visitante"] in diccionario_avances:
                p["visitante"] = diccionario_avances[p["visitante"]]
                cambios += 1

    if cambios > 0:
        with open(ruta_realidad, 'w', encoding='utf-8') as f:
            json.dump(realidad, f, ensure_ascii=False, indent=4)
        print(f"✅ Cuadro actualizado: Se han arrastrado {cambios} equipos a la siguiente ronda.")
    else:
        print("ℹ️ No hay nuevos clasificados que arrastrar en el cuadro.")

if __name__ == "__main__":
    arrastrar_clasificados()
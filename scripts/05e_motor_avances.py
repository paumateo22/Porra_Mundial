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
                id_p = str(p.get("id_partido"))
                ganador = p["pasa"]
                
                if p.get("local") == ganador:
                    perdedor = p.get("visitante")
                else:
                    perdedor = p.get("local")
                
                # Guardamos todas las nomenclaturas posibles para que el match sea perfecto
                diccionario_avances[f"Ganador {id_p}"] = ganador
                diccionario_avances[f"W{id_p}"] = ganador
                diccionario_avances[f"Perdedor {id_p}"] = perdedor
                diccionario_avances[f"L{id_p}"] = perdedor

    # 2. Aplicar los avances en cascada (bucle por si hay saltos múltiples en un día)
    cambios_totales = 0
    while True:
        cambios_iter = 0
        for fase, partidos in realidad.get("eliminatorias", {}).items():
            for p in partidos:
                loc = str(p.get("local", ""))
                vis = str(p.get("visitante", ""))
                
                if loc in diccionario_avances and p["local"] != diccionario_avances[loc]:
                    p["local"] = diccionario_avances[loc]
                    cambios_iter += 1
                    
                if vis in diccionario_avances and p["visitante"] != diccionario_avances[vis]:
                    p["visitante"] = diccionario_avances[vis]
                    cambios_iter += 1
                    
        cambios_totales += cambios_iter
        if cambios_iter == 0:
            break

    if cambios_totales > 0:
        with open(ruta_realidad, 'w', encoding='utf-8') as f:
            json.dump(realidad, f, ensure_ascii=False, indent=4)
        print(f"✅ Cuadro actualizado: Se han propagado {cambios_totales} equipos a las siguientes rondas.")
    else:
        print("ℹ️ No hay nuevos clasificados que arrastrar en el cuadro.")

if __name__ == "__main__":
    arrastrar_clasificados()
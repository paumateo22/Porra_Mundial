import sys
import json
import random
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def simular_realidad():
    print("=======================================================")
    print(" 🎲 [99] SIMULADOR DE REALIDAD (LLENADO ALEATORIO) 🎲")
    print("=======================================================")

    ruta_realidad = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    realidad = html_utils.cargar_json(ruta_realidad)

    if not realidad:
        print("❌ No se encontró realidad_oficial.json. Ejecuta 00b primero.")
        return

    partidos_simulados = 0

    # 1. Simular Fase de Grupos
    # En fase de grupos sí puede haber empates
    for grupo, partidos in realidad.get("fase_grupos", {}).items():
        for p in partidos:
            p["goles_local"] = str(random.randint(0, 4))
            p["goles_visitante"] = str(random.randint(0, 4))
            p["estado"] = "finished"
            partidos_simulados += 1

    # 2. Simular Eliminatorias
    for fase, partidos in realidad.get("eliminatorias", {}).items():
        for p in partidos:
            gl = random.randint(0, 4)
            gv = random.randint(0, 4)
            
            # En eliminatorias tiene que pasar alguien. Si hay empate, forzamos desempate (simulando penaltis)
            while gl == gv:
                gv = random.randint(0, 4)

            p["goles_local"] = str(gl)
            p["goles_visitante"] = str(gv)
            p["estado"] = "finished"
            
            ganador = p["local"] if gl > gv else p["visitante"]
            p["pasa"] = ganador
            
            # Para tercer puesto y final, Sofascore a veces usa el flag "ganador"
            if fase in ["tercer_puesto", "final"]:
                p["ganador"] = ganador

            partidos_simulados += 1

    with open(ruta_realidad, 'w', encoding='utf-8') as f:
        json.dump(realidad, f, ensure_ascii=False, indent=4)

    print(f"✅ ¡Simulación completada! Se han rellenado {partidos_simulados} partidos con resultados aleatorios.")
    print("⚠️ Recuerda ejecutar 'python main.py' (o los motores) para que estos resultados se calculen.")

if __name__ == "__main__":
    simular_realidad()
import sys
import json
import random
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def clonar_realidad():
    print("=======================================================")
    print(" 🪞 INICIANDO CLONADOR DE REALIDAD (PARTIDA PERFECTA) 🪞")
    print("=======================================================")
    
    # Definimos el jugador que será nuestro "Oráculo"
    jugador_origen = "generico_2"
    ruta_base = ROOT_DIR / "participantes" / jugador_origen / "pronosticos" / "grupos" / f"{jugador_origen}_base.json"
    
    if not ruta_base.exists():
        print(f"❌ Error: No se encuentra el archivo {ruta_base.name}.")
        print(f"Asegúrate de que la carpeta de '{jugador_origen}' existe y tiene su pronóstico base.")
        return

    with open(ruta_base, 'r', encoding='utf-8') as f:
        base = json.load(f)

    # Preparamos el esqueleto de la realidad oficial
    realidad = {
        "fase_grupos": {},
        "clasificados_a_dieciseisavos": base.get("clasificados_a_dieciseisavos", []),
        "eliminatorias": {}
    }

    # --- 1. Copiar y adaptar Fase de Grupos ---
    print(f"⚽ Copiando la Fase de Grupos de {jugador_origen}...")
    for grupo, partidos in base.get("fase_grupos", {}).items():
        realidad["fase_grupos"][grupo] = []
        for p in partidos:
            partido_real = p.copy()
            partido_real["estado"] = "finished"  # Fundamental para que el motor lo evalúe
            realidad["fase_grupos"][grupo].append(partido_real)

    # --- 2. Copiar y adaptar Eliminatorias (Inyectando goles) ---
    print("⚔️ Copiando las Eliminatorias e inventando goles coherentes...")
    for fase, partidos in base.get("eliminatorias", {}).items():
        realidad["eliminatorias"][fase] = []
        for p in partidos:
            partido_real = p.copy()
            partido_real["estado"] = "finished"
            
            # Aseguramos que existe la etiqueta 'pasa'. Si no está, forzamos al local.
            if "pasa" not in partido_real:
                partido_real["pasa"] = partido_real["local"]
                
            ganador = partido_real["pasa"]
            
            # Generamos goles artificiales y coherentes para que el 06a pueda calcular el 1X2
            if "goles_local" not in partido_real or "goles_visitante" not in partido_real:
                # Inventamos unos goles (ej: 2 a 1, 3 a 0...)
                gl_random = random.randint(1, 3)
                gv_random = random.randint(0, 2)
                
                # Evitamos el empate para que sea más limpio en eliminatorias
                if gl_random == gv_random: 
                    gl_random += 1
                
                # Asignamos los goles mayores al equipo que debe pasar
                if ganador == partido_real["local"]:
                    partido_real["goles_local"] = str(max(gl_random, gv_random))
                    partido_real["goles_visitante"] = str(min(gl_random, gv_random))
                else:
                    partido_real["goles_local"] = str(min(gl_random, gv_random))
                    partido_real["goles_visitante"] = str(max(gl_random, gv_random))
                
            # Si es la final o el tercer puesto, necesitamos la clave 'ganador' para el script 06c
            if fase in ["final", "tercer_puesto"]:
                partido_real["ganador"] = partido_real["pasa"]
                
            realidad["eliminatorias"][fase].append(partido_real)

    # --- 3. Guardar la nueva Realidad Oficial ---
    ruta_guardado = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    ruta_guardado.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(realidad, f, ensure_ascii=False, indent=4)
        
    print(f"✅ ¡Realidad Oficial sobreescrita con éxito (Goles generados automáticamentente)!")
    print(f"💾 Guardado en: {ruta_guardado.relative_to(ROOT_DIR)}")
    print(f"ℹ️ Ahora el motor creerá que todo lo que dijo {jugador_origen} ha ocurrido de verdad.")

if __name__ == "__main__":
    clonar_realidad()
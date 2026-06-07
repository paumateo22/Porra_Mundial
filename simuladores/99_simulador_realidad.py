import sys
import json
import random
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def simular_goles(es_eliminatoria=False):
    """Genera goles con probabilidades realistas de fútbol."""
    goles_l = random.choices([0, 1, 2, 3, 4, 5], weights=[25, 35, 20, 12, 6, 2])[0]
    goles_v = random.choices([0, 1, 2, 3, 4, 5], weights=[30, 30, 20, 12, 6, 2])[0]
    
    # En eliminatorias tiene que haber un ganador sí o sí (simulación de prórroga/penaltis)
    if es_eliminatoria and goles_l == goles_v:
        if random.choice([True, False]): goles_l += 1
        else: goles_v += 1
            
    return str(goles_l), str(goles_v)

def ejecutar_simulador():
    print("=======================================================")
    print(" 🌍 INICIANDO SIMULADOR DE REALIDAD (MUNDIAL 2026) 🌍")
    print("=======================================================")
    
    # Usamos el base de un jugador para sacar los enfrentamientos de grupos
    ruta_base = ROOT_DIR / "participantes" / "generico_1" / "pronosticos" / "grupos" / "generico_1_base.json"
    if not ruta_base.exists():
        print(f"❌ Error: Falta {ruta_base} para leer los cruces.")
        return
        
    with open(ruta_base, 'r', encoding='utf-8') as f:
        base = json.load(f)

    realidad = {
        "fase_grupos": {},
        "clasificados_a_dieciseisavos": [],
        "eliminatorias": {
            "dieciseisavos": [], "octavos": [], "cuartos": [],
            "semifinales": [], "tercer_puesto": [], "final": []
        }
    }

    clasificacion_global = []

    # --- 1. SIMULAR FASE DE GRUPOS ---
    print("⚽ Simulando Fase de Grupos y calculando puntos...")
    for grupo, partidos in base.get("fase_grupos", {}).items():
        realidad["fase_grupos"][grupo] = []
        tabla = {} # Para calcular quién pasa
        
        for p in partidos:
            gl, gv = simular_goles(es_eliminatoria=False)
            realidad["fase_grupos"][grupo].append({
                "local": p["local"], "visitante": p["visitante"],
                "goles_local": gl, "goles_visitante": gv,
                "estado": "finished"
            })
            
            # Inicializar equipos en la tabla
            for eq in [p["local"], p["visitante"]]:
                if eq not in tabla: tabla[eq] = {"pts": 0, "dif": 0}
            
            # Repartir puntos
            gl_int, gv_int = int(gl), int(gv)
            tabla[p["local"]]["dif"] += (gl_int - gv_int)
            tabla[p["visitante"]]["dif"] += (gv_int - gl_int)
            
            if gl_int > gv_int: tabla[p["local"]]["pts"] += 3
            elif gv_int > gl_int: tabla[p["visitante"]]["pts"] += 3
            else:
                tabla[p["local"]]["pts"] += 1
                tabla[p["visitante"]]["pts"] += 1

        # Ordenar el grupo por puntos y luego por diferencia de goles
        equipos_ordenados = sorted(tabla.items(), key=lambda x: (x[1]["pts"], x[1]["dif"]), reverse=True)
        
        # Pasan los 2 primeros seguro. El 3º va a la repesca global
        realidad["clasificados_a_dieciseisavos"].extend([equipos_ordenados[0][0], equipos_ordenados[1][0]])
        clasificacion_global.append(equipos_ordenados[2]) # Guardamos al 3º

    # Repesca: Los 8 mejores terceros pasan
    mejores_terceros = sorted(clasificacion_global, key=lambda x: (x[1]["pts"], x[1]["dif"]), reverse=True)[:8]
    realidad["clasificados_a_dieciseisavos"].extend([eq[0] for eq in mejores_terceros])
    
    random.shuffle(realidad["clasificados_a_dieciseisavos"]) # Mezclamos para los cruces

    # --- 2. EL CUADRO DE ELIMINATORIAS (BRACKET) ---
    print("⚔️ Simulando Rondas Eliminatorias (K.O.)...")
    
    # Diccionario para saber quién avanza a qué partido
    enfrentamientos = {
        "dieciseisavos": list(range(73, 89)), # IDs del 73 al 88
        "octavos": list(range(89, 97)),
        "cuartos": list(range(97, 101)),
        "semifinales": [101, 102]
    }
    
    # Rellenar dieciseisavos
    equipos_vivos = realidad["clasificados_a_dieciseisavos"]
    proxima_ronda = []
    
    # Dieciseisavos
    idx_eq = 0
    for id_p in enfrentamientos["dieciseisavos"]:
        loc, vis = equipos_vivos[idx_eq], equipos_vivos[idx_eq+1]
        idx_eq += 2
        gl, gv = simular_goles(es_eliminatoria=True)
        pasa = loc if int(gl) > int(gv) else vis
        proxima_ronda.append(pasa)
        
        realidad["eliminatorias"]["dieciseisavos"].append({
            "id_partido": id_p, "local": loc, "visitante": vis,
            "goles_local": gl, "goles_visitante": gv, "pasa": pasa, "estado": "finished"
        })

    # Función genérica para siguientes rondas
    def simular_fase(nombre_fase, ids, equipos_entrada):
        equipos_salida = []
        idx = 0
        perdedores_semis = []
        for id_p in ids:
            loc, vis = equipos_entrada[idx], equipos_entrada[idx+1]
            idx += 2
            gl, gv = simular_goles(es_eliminatoria=True)
            pasa = loc if int(gl) > int(gv) else vis
            pierde = vis if pasa == loc else loc
            equipos_salida.append(pasa)
            if nombre_fase == "semifinales": perdedores_semis.append(pierde)
            
            realidad["eliminatorias"][nombre_fase].append({
                "id_partido": id_p, "local": loc, "visitante": vis,
                "goles_local": gl, "goles_visitante": gv, "pasa": pasa, "estado": "finished"
            })
        return equipos_salida, perdedores_semis

    # Octavos, Cuartos y Semis
    proxima_ronda, _ = simular_fase("octavos", enfrentamientos["octavos"], proxima_ronda)
    proxima_ronda, _ = simular_fase("cuartos", enfrentamientos["cuartos"], proxima_ronda)
    finalistas, perdedores_semis = simular_fase("semifinales", enfrentamientos["semifinales"], proxima_ronda)

    # Tercer Puesto
    gl, gv = simular_goles(es_eliminatoria=True)
    ganador_tercero = perdedores_semis[0] if int(gl) > int(gv) else perdedores_semis[1]
    realidad["eliminatorias"]["tercer_puesto"].append({
        "id_partido": 103, "local": perdedores_semis[0], "visitante": perdedores_semis[1],
        "goles_local": gl, "goles_visitante": gv, "pasa": ganador_tercero, "ganador": ganador_tercero, "estado": "finished"
    })

    # Final
    gl, gv = simular_goles(es_eliminatoria=True)
    campeon = finalistas[0] if int(gl) > int(gv) else finalistas[1]
    realidad["eliminatorias"]["final"].append({
        "id_partido": 104, "local": finalistas[0], "visitante": finalistas[1],
        "goles_local": gl, "goles_visitante": gv, "pasa": campeon, "ganador": campeon, "estado": "finished"
    })

    print(f"🏆 ¡Mundial Simulado! Campeón: {campeon}")

    # Guardar
    ruta_guardado = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    ruta_guardado.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(realidad, f, ensure_ascii=False, indent=4)
        
    print(f"💾 Realidad guardada en: {ruta_guardado.relative_to(ROOT_DIR)}")

if __name__ == "__main__":
    ejecutar_simulador()
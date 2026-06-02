import sys
import json
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_json(datos, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def calcular_clasificacion_grupos(fase_grupos):
    posiciones = {}
    for grupo, partidos in fase_grupos.items():
        tabla = {}
        for p in partidos:
            loc, vis = p['local'], p['visitante']
            if loc not in tabla: tabla[loc] = {"pts": 0, "dif": 0}
            if vis not in tabla: tabla[vis] = {"pts": 0, "dif": 0}

            gl = int(p.get('goles_local', 0)) if str(p.get('goles_local', '')).isdigit() else 0
            gv = int(p.get('goles_visitante', 0)) if str(p.get('goles_visitante', '')).isdigit() else 0

            tabla[loc]["dif"] += (gl - gv)
            tabla[vis]["dif"] += (gv - gl)

            if p.get('estado', 'finished') == 'finished':
                if gl > gv: tabla[loc]["pts"] += 3
                elif gv > gl: tabla[vis]["pts"] += 3
                else:
                    tabla[loc]["pts"] += 1
                    tabla[vis]["pts"] += 1

        equipos_ordenados = sorted(tabla.items(), key=lambda x: (x[1]["pts"], x[1]["dif"]), reverse=True)
        for idx, (eq, stats) in enumerate(equipos_ordenados):
            posiciones[eq] = idx + 1
    return posiciones

def ejecutar_06c_motor_grupos():
    print("=======================================================")
    print(" ⚽ [06C] INICIANDO MOTOR DE FASE DE GRUPOS ⚽")
    print("=======================================================")

    settings = cargar_json(ROOT_DIR / "config" / "settings.json")
    realidad = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json")
    reporte_06b = cargar_json(ROOT_DIR / "data" / "resultados" / "reporte_06b_jornadas.json")

    if not all([settings, realidad, reporte_06b]):
        print("❌ Error: Faltan archivos clave para el 06c. Ejecuta 06b primero.")
        return

    # Extraemos habilitadores y puntuaciones del config
    hab_clasif = settings.get("habilitadores", {}).get("bono_clasificacion_grupos", 1)
    hab_pos = settings.get("habilitadores", {}).get("bono_posicion_grupos", 1)
    
    pts_clasificado = settings.get("puntuaciones", {}).get("fase_grupos", {}).get("acierto_clasificado", 1)
    pts_posicion = settings.get("puntuaciones", {}).get("fase_grupos", {}).get("acierto_posicion_exacta", 2)

    pasan_real = realidad.get("clasificados_a_dieciseisavos", [])
    pos_real = calcular_clasificacion_grupos(realidad.get("fase_grupos", {}))

    reporte_06c = {}

    for jugador, stats in reporte_06b.items():
        reporte_06c[jugador] = {**stats, "puntos_grupos": 0}

        ruta_base = ROOT_DIR / "participantes" / jugador / "pronosticos" / "grupos" / f"{jugador}_base.json"
        base_pred = cargar_json(ruta_base)
        if not base_pred: continue

        pasan_pred = base_pred.get("clasificados_a_dieciseisavos", [])
        pos_pred = calcular_clasificacion_grupos(base_pred.get("fase_grupos", {}))

        puntos_jugador = 0
        
        # NUEVA LÓGICA: Recorremos SOLO las selecciones que han pasado en la Realidad
        for eq in pasan_real:
            if eq in pasan_pred:
                if hab_clasif == 1:
                    puntos_jugador += pts_clasificado
                if hab_pos == 1 and pos_real.get(eq) == pos_pred.get(eq):
                    puntos_jugador += pts_posicion
        
        reporte_06c[jugador]["puntos_grupos"] = puntos_jugador

        # Actualizar libro personal
        ruta_libro = ROOT_DIR / "participantes" / jugador / "estadisticas" / "historial_puntos.json"
        libro = cargar_json(ruta_libro)
        if libro:
            libro["resolucion_fase_grupos"] = {"puntos_conseguidos": puntos_jugador}
            libro["puntos_totales"] = stats["puntos_partidos"] + stats["puntos_jornadas"] + puntos_jugador
            guardar_json(libro, ruta_libro)
        
        print(f"👤 {jugador.title()}: +{puntos_jugador} pts por Fase de Grupos.")

    ruta_salida = ROOT_DIR / "data" / "resultados" / "reporte_06c_grupos.json"
    guardar_json(reporte_06c, ruta_salida)
    print(f"\n✅ Informe 06c generado con éxito: {ruta_salida.relative_to(ROOT_DIR)}")

if __name__ == "__main__":
    ejecutar_06c_motor_grupos()
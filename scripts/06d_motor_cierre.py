import sys
import json
import csv
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

def ejecutar_06d_motor_cierre():
    print("=======================================================")
    print(" 🏆 [06D] INICIANDO MOTOR DE CIERRE Y DESEMPATES 🏆")
    print("=======================================================")

    settings = cargar_json(ROOT_DIR / "config" / "settings.json") or {}
    reporte_06c = cargar_json(ROOT_DIR / "data" / "resultados" / "reporte_06c_grupos.json")
    reporte_06f = cargar_json(ROOT_DIR / "data" / "resultados" / "reporte_06f_premios.json") or {}

    if not reporte_06c:
        print("❌ Error: Falta reporte_06c_grupos.json. Ejecuta 06c primero.")
        return

    ranking = []
    
    # Preparamos los criterios de desempate desde settings
    criterios = settings.get("desempates", {})
    
    for jugador, stats in reporte_06c.items():
        # Recuperar el historial del jugador para comprobar desempates complejos (ej. Campeón)
        ruta_libro = ROOT_DIR / "participantes" / jugador.replace(' ', '_').lower() / "estadisticas" / "historial_puntos.json"
        libro = cargar_json(ruta_libro) or {}
        
        # 1. Recuperar los puntos extra calculados en el 06f
        stats_premios = reporte_06f.get(jugador, {})
        pts_podio = stats_premios.get("puntos_podio", 0) 
        pts_forms = stats_premios.get("puntos_formulario", 0) 
        
        # 2. Sumar el total absoluto
        pts_base = stats["puntos_partidos"] + stats["puntos_jornadas"]
        pts_grupos = stats["puntos_grupos"]
        total = pts_base + pts_grupos + pts_podio + pts_forms
        
        # 3. Extraer métricas para desempates
        aciertos_1x2 = stats.get("total_aciertos_1x2", 0)
        aciertos_exactos = stats.get("total_aciertos_exactos", 0)
        acierto_campeon = 1 if libro.get("premios_finales", {}).get("podio", {}).get("detalles", {}).get("campeon", 0) > 0 else 0

        # Mapeo dinámico de desempates según settings
        valores_desempate = {
            "acierto_1x2": aciertos_1x2,
            "acierto_exacto": aciertos_exactos,
            "campeon": acierto_campeon
        }
        
        v_crit_1 = valores_desempate.get(criterios.get("criterio_1"), 0)
        v_crit_2 = valores_desempate.get(criterios.get("criterio_2"), 0)
        v_crit_3 = valores_desempate.get(criterios.get("criterio_3"), 0)

        ranking.append({
            "Jugador": jugador,
            "Puntos_Partidos": stats["puntos_partidos"],
            "Puntos_Jornadas": stats["puntos_jornadas"],
            "Puntos_Grupos": pts_grupos,
            "Puntos_Podio": pts_podio,
            "Puntos_Forms": pts_forms,
            "TOTAL": total,
            "Crit_1": v_crit_1,
            "Crit_2": v_crit_2,
            "Crit_3": v_crit_3
        })

    # Ordenar por: Total -> Criterio 1 -> Criterio 2 -> Criterio 3
    ranking_ordenado = sorted(ranking, key=lambda x: (x["TOTAL"], x["Crit_1"], x["Crit_2"], x["Crit_3"]), reverse=True)

    print("\n📊 CLASIFICACIÓN FINAL DEL MUNDIAL 📊")
    print("-" * 90)
    print(f"{'Pos':<4} | {'Jugador':<15} | {'Base (Part+Jorn)':<18} | {'Grupos':<8} | {'Podio+Extra':<13} | {'TOTAL':<5}")
    print("-" * 90)

    # --- LÓGICA DE EMPATES REALES ---
    posicion_real = 1
    for i, j in enumerate(ranking_ordenado):
        if i > 0:
            j_ant = ranking_ordenado[i-1]
            
            # Comparamos la tupla exacta de puntuación y desempates con el jugador anterior
            tupla_actual = (j["TOTAL"], j["Crit_1"], j["Crit_2"], j["Crit_3"])
            tupla_anterior = (j_ant["TOTAL"], j_ant["Crit_1"], j_ant["Crit_2"], j_ant["Crit_3"])
            
            # Si este jugador tiene resultados estrictamente peores, su posición cae a su índice real + 1
            if tupla_actual < tupla_anterior:
                posicion_real = i + 1
                
        j["Posicion"] = posicion_real
        
        pts_base = j["Puntos_Partidos"] + j["Puntos_Jornadas"]
        pts_extra = j["Puntos_Podio"] + j["Puntos_Forms"]
        print(f"{j['Posicion']:<4} | {j['Jugador'].title():<15} | {pts_base:<18.2f} | {j['Puntos_Grupos']:<8} | {pts_extra:<13.2f} | {j['TOTAL']:.2f}")

    ruta_csv = ROOT_DIR / "data" / "resultados" / "ranking_oficial.csv"
    columnas = ["Posicion", "Jugador", "Puntos_Partidos", "Puntos_Jornadas", "Puntos_Grupos", "Puntos_Podio", "Puntos_Forms", "TOTAL"]
    
    # Limpiamos las llaves de desempate antes de exportar para no ensuciar el CSV
    ranking_export = [{k: v for k, v in row.items() if k in columnas} for row in ranking_ordenado]
    
    with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(ranking_export)

    # Actualizamos los libros de cuentas con la posición final y los puntos absolutos
    dir_participantes = ROOT_DIR / "participantes"
    for j in ranking_ordenado:
        ruta_libro = dir_participantes / j["Jugador"].replace(' ', '_').lower() / "estadisticas" / "historial_puntos.json"
        libro = cargar_json(ruta_libro)
        if libro:
            libro["posicion_final_ranking"] = j["Posicion"]
            libro["puntos_totales"] = j["TOTAL"]
            with open(ruta_libro, 'w', encoding='utf-8') as f:
                json.dump(libro, f, ensure_ascii=False, indent=4)

    print("-" * 90)
    print(f"💾 Ranking final exportado a CSV en: {ruta_csv.relative_to(ROOT_DIR)}")
    print("📔 Libros de Cuentas personales sellados con la posición final y puntos totales.")

if __name__ == "__main__":
    ejecutar_06d_motor_cierre()
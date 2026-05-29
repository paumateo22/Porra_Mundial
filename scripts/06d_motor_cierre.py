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

    reporte_06c = cargar_json(ROOT_DIR / "data" / "resultados" / "reporte_06c_grupos.json")
    if not reporte_06c:
        print("❌ Error: Falta reporte_06c_grupos.json. Ejecuta 06c primero.")
        return

    ranking = []
    for jugador, stats in reporte_06c.items():
        # Lectura de premios extra si los tuvieras configurados en el futuro
        pts_podio = stats.get("puntos_podio", 0) 
        pts_forms = stats.get("puntos_forms", 0) 
        
        pts_base = stats["puntos_partidos"] + stats["puntos_jornadas"]
        pts_grupos = stats["puntos_grupos"]
        total = pts_base + pts_grupos + pts_podio + pts_forms

        ranking.append({
            "Jugador": jugador,
            "Puntos_Partidos": stats["puntos_partidos"],
            "Puntos_Jornadas": stats["puntos_jornadas"],
            "Puntos_Grupos": pts_grupos,
            "Puntos_Podio": pts_podio,
            "Puntos_Forms": pts_forms,
            "TOTAL": total,
            "Aciertos_1X2": stats.get("total_aciertos_1x2", 0),
            "Aciertos_Exactos": stats.get("total_aciertos_exactos", 0)
        })

    # Criterio de desempate
    ranking_ordenado = sorted(ranking, key=lambda x: (x["TOTAL"], x["Aciertos_1X2"], x["Aciertos_Exactos"]), reverse=True)

    print("\n📊 CLASIFICACIÓN FINAL DEL MUNDIAL 📊")
    print("-" * 90)
    print(f"{'Pos':<4} | {'Jugador':<15} | {'Base (Part+Jorn)':<18} | {'Grupos':<8} | {'Podio+Extra':<13} | {'TOTAL':<5}")
    print("-" * 90)

    for i, j in enumerate(ranking_ordenado):
        j["Posicion"] = i + 1
        pts_base = j["Puntos_Partidos"] + j["Puntos_Jornadas"]
        pts_extra = j["Puntos_Podio"] + j["Puntos_Forms"]
        print(f"{j['Posicion']:<4} | {j['Jugador'].title():<15} | {pts_base:<18.2f} | {j['Puntos_Grupos']:<8} | {pts_extra:<13.2f} | {j['TOTAL']:.2f}")

    ruta_csv = ROOT_DIR / "data" / "resultados" / "ranking_oficial.csv"
    columnas = ["Posicion", "Jugador", "Puntos_Partidos", "Puntos_Jornadas", "Puntos_Grupos", "Puntos_Podio", "Puntos_Forms", "TOTAL"]
    with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columnas, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(ranking_ordenado)

    dir_participantes = ROOT_DIR / "participantes"
    for j in ranking_ordenado:
        ruta_libro = dir_participantes / j["Jugador"].replace(' ', '_').lower() / "estadisticas" / "historial_puntos.json"
        libro = cargar_json(ruta_libro)
        if libro:
            libro["posicion_final_ranking"] = j["Posicion"]
            with open(ruta_libro, 'w', encoding='utf-8') as f:
                json.dump(libro, f, ensure_ascii=False, indent=4)

    print("-" * 90)
    print(f"💾 Ranking final exportado a CSV en: {ruta_csv.relative_to(ROOT_DIR)}")
    print("📔 Libros de Cuentas personales sellados con la posición final.")

if __name__ == "__main__":
    ejecutar_06d_motor_cierre()
import sys
import json
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# =====================================================================
# UTILIDADES DE CARGA Y GUARDADO
# =====================================================================
def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_json(datos, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

# =====================================================================
# EL CEREBRO DE EJECUCIÓN 06B (EL MACRO)
# =====================================================================
def ejecutar_06b_motor_jornadas():
    print("=======================================================")
    print(" 📅 [06B] INICIANDO MOTOR DE JORNADAS (GANADOR/PERDEDOR) ")
    print("=======================================================")
    
    # 1. Cargar el tridente de datos
    settings = cargar_json(ROOT_DIR / "config" / "settings.json")
    jornadas = cargar_json(ROOT_DIR / "config" / "jornadas.json")
    reporte_06a = cargar_json(ROOT_DIR / "data" / "resultados" / "reporte_06a_partidos.json")

    if not all([settings, jornadas, reporte_06a]):
        print("❌ Error: Faltan archivos clave (settings.json, jornadas.json o reporte_06a_partidos.json).")
        print("Asegúrate de ejecutar el 06a antes que este script.")
        return

    # 2. Leer los interruptores de tu Panel de Control
    bono_habilitado = settings.get("habilitadores", {}).get("ganador_perdedor_jornada", 0) == 1
    pts_ganador = settings.get("puntuaciones", {}).get("jornadas", {}).get("ganador", 2)
    pts_perdedor = settings.get("puntuaciones", {}).get("jornadas", {}).get("perdedor", -2)

    # 3. Preparar la "mochila" que le pasaremos al 06c
    reporte_06b = {}
    for jugador, stats in reporte_06a.items():
        reporte_06b[jugador] = {
            **stats,  # Heredamos todos los puntos, aciertos 1x2 y exactos del 06a
            "puntos_jornadas": 0,
            "desglose_jornadas": {}
        }

    if not bono_habilitado:
        print("⚠️ El interruptor 'ganador_perdedor_jornada' está apagado en settings.json.")
        print("Saltando la evaluación, pero pasando los datos intactos al 06c...")
        ruta_salida = ROOT_DIR / "data" / "resultados" / "reporte_06b_jornadas.json"
        guardar_json(reporte_06b, ruta_salida)
        return

    # 4. Analizar el calendario bloque por bloque
    for nombre_jornada, partidos_jornada in jornadas.items():
        if not partidos_jornada: continue
            
        # El 06a guardó los partidos con la clave "Local_vs_Visitante"
        claves_busqueda = []
        for p in partidos_jornada:
            if "id_partido" in p:
                claves_busqueda.append(f"ID_{p['id_partido']}")
            else:
                claves_busqueda.append(f"{p['local']}_vs_{p['visitante']}")
        
        # Conteo de aciertos para esta jornada específica
        aciertos_jornada = {}
        partidos_jugados_en_esta_jornada = 0
        
        for jugador, stats in reporte_06a.items():
            aciertos = 0
            historial = stats.get("historial_jornadas", {})
            
            # Revisamos el historial del jugador para los partidos de esta jornada
            for clave in claves_busqueda:
                if clave in historial:
                    partidos_jugados_en_esta_jornada += 1 # Truco para saber si la jornada ha empezado
                    if historial[clave].get("acierto_1x2"):
                        aciertos += 1
                        
            aciertos_jornada[jugador] = aciertos

        # Si aún no se ha jugado NINGÚN partido de esta jornada, no repartimos premios
        if partidos_jugados_en_esta_jornada == 0:
            continue

        # Encontrar los topes por arriba y por abajo
        max_aciertos = max(aciertos_jornada.values())
        min_aciertos = min(aciertos_jornada.values())

        print(f"\n--- 📊 Resultados Temporales: {nombre_jornada} ---")
        
        # Regla del empate masivo
        if max_aciertos == min_aciertos:
            print(f"🤝 ¡Empate masivo a {max_aciertos} aciertos! Nadie suma ni resta.")
            for j in aciertos_jornada:
                reporte_06b[j]["desglose_jornadas"][nombre_jornada] = {
                    "aciertos_1x2": aciertos_jornada[j],
                    "puntos_bono": 0,
                    "resultado": "Empate Masivo"
                }
            continue

        # Reparto de gloria y miseria
        for jugador, aciertos in aciertos_jornada.items():
            bono_asignado = 0
            resultado_txt = "Neutral"
            
            if aciertos == max_aciertos:
                bono_asignado = pts_ganador
                resultado_txt = "Ganador"
                print(f"🥇 {jugador.title()} GANA con {aciertos} aciertos (+{bono_asignado} pts)")
            elif aciertos == min_aciertos:
                bono_asignado = pts_perdedor
                resultado_txt = "Perdedor"
                print(f"📉 {jugador.title()} PIERDE con {aciertos} aciertos ({bono_asignado} pts)")
            else:
                print(f"➖ {jugador.title()} queda en tierra de nadie con {aciertos} aciertos.")

            reporte_06b[jugador]["puntos_jornadas"] += bono_asignado
            reporte_06b[jugador]["desglose_jornadas"][nombre_jornada] = {
                "aciertos_1x2": aciertos,
                "puntos_bono": bono_asignado,
                "resultado": resultado_txt
            }

    # 5. ACTUALIZAR LIBROS DE CUENTAS PERSONALES
    dir_participantes = ROOT_DIR / "participantes"
    
    for jugador, datos in reporte_06b.items():
        ruta_libro = dir_participantes / jugador / "estadisticas" / "historial_puntos.json"
        libro = cargar_json(ruta_libro)
        
        if libro:
            # Añadimos el desglose de jornadas al libro personal
            libro["desglose_jornadas"] = datos["desglose_jornadas"]
            # Sumamos los puntos base (partidos) + bonos (jornadas) para tener un total provisional real
            libro["puntos_totales"] = datos["puntos_partidos"] + datos["puntos_jornadas"]
            
            guardar_json(libro, ruta_libro)

    # 6. Guardar el nuevo reporte enriquecido global
    ruta_salida = ROOT_DIR / "data" / "resultados" / "reporte_06b_jornadas.json"
    guardar_json(reporte_06b, ruta_salida)
    
    print(f"\n✅ Informe 06b generado con éxito: {ruta_salida.relative_to(ROOT_DIR)}")
    print("📔 Libros de Cuentas actualizados con bonos de jornada. ¡Listo para el cierre (06c)!")

if __name__ == "__main__":
    ejecutar_06b_motor_jornadas()
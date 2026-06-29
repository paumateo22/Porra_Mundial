import sys
import json
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def generar_indice_jornadas():
    print("=======================================================")
    print(" 📅 INICIANDO GENERADOR DE CALENDARIO (JORNADAS) 📅")
    print("=======================================================")
    
    ruta_base = ROOT_DIR / "participantes" / "pau" / "pronosticos" / "grupos" / "pau_base.json"
    
    if not ruta_base.exists():
        print(f"❌ Error: No se encuentra el archivo {ruta_base}")
        return

    with open(ruta_base, 'r', encoding='utf-8') as f:
        base = json.load(f)

    # Cargar horas para ordenar cronológicamente
    ruta_horas = ROOT_DIR / "config" / "horas_partidos.json"
    horas_elim = {}
    if ruta_horas.exists():
        with open(ruta_horas, 'r', encoding='utf-8') as f:
            horas_data = json.load(f)
            horas_elim = horas_data.get("eliminatorias_horas", {})

    jornadas = {
        "J1.1": [], "J1.2": [],
        "J2.1": [], "J2.2": [],
        "J3.1": [], "J3.2": []
    }

    bloque_1 = ["A", "B", "C", "D", "E", "F"]
    
    fase_grupos = base.get("fase_grupos", {})
    for nombre_grupo, partidos in fase_grupos.items():
        letra = nombre_grupo.split("_")[-1] if "_" in nombre_grupo else nombre_grupo[-1]
        sufijo = "1" if letra in bloque_1 else "2"
        
        for i, p in enumerate(partidos):
            partido_limpio = {"local": p["local"], "visitante": p["visitante"]}
            if i < 2: jornadas[f"J1.{sufijo}"].append(partido_limpio)
            elif i < 4: jornadas[f"J2.{sufijo}"].append(partido_limpio)
            else: jornadas[f"J3.{sufijo}"].append(partido_limpio)

    # --- REPARTO CRONOLÓGICO DE ELIMINATORIAS ---
    dieciseisavos = []
    for i in range(73, 89):
        fecha = horas_elim.get(str(i), "")
        dieciseisavos.append({"id_partido": i, "fecha": fecha})
        
    dieciseisavos_ordenados = sorted(dieciseisavos, key=lambda x: x["fecha"])
    
    jornadas["dieciseisavos.1"] = [{"id_partido": p["id_partido"]} for p in dieciseisavos_ordenados[:8]]
    jornadas["dieciseisavos.2"] = [{"id_partido": p["id_partido"]} for p in dieciseisavos_ordenados[8:]]
    
    jornadas["octavos"] = [{"id_partido": i} for i in range(89, 97)]
    jornadas["cuartos"] = [{"id_partido": i} for i in range(97, 101)]
    jornadas["semifinales"] = [{"id_partido": i} for i in range(101, 103)]
    jornadas["finales"] = [{"id_partido": 103}, {"id_partido": 104}]

    ruta_guardado = ROOT_DIR / "config" / "jornadas.json"
    ruta_guardado.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(jornadas, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Calendario generado (Eliminatorias ordenadas por fecha de juego).")

if __name__ == "__main__":
    generar_indice_jornadas()
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
    
    # Leemos la base de generico_1 como molde
    ruta_base = ROOT_DIR / "participantes" / "generico_1" / "pronosticos" / "grupos" / "generico_1_base.json"
    
    if not ruta_base.exists():
        print(f"❌ Error: No se encuentra el archivo {ruta_base}")
        return

    with open(ruta_base, 'r', encoding='utf-8') as f:
        base = json.load(f)

    # Inicializamos el diccionario con las jornadas vacías
    jornadas = {
        "J1.1": [], "J1.2": [],
        "J2.1": [], "J2.2": [],
        "J3.1": [], "J3.2": []
    }

    # Letras para definir los sufijos
    bloque_1 = ["A", "B", "C", "D", "E", "F"]
    
    # --- 1. REPARTO MILIMÉTRICO DE LA FASE DE GRUPOS ---
    fase_grupos = base.get("fase_grupos", {})
    
    for nombre_grupo, partidos in fase_grupos.items():
        # Sacamos la letra del grupo (Ej: "Grupo_A" -> "A")
        letra = nombre_grupo.split("_")[-1] if "_" in nombre_grupo else nombre_grupo[-1]
        
        # Asignamos el sufijo .1 o .2 según la letra
        sufijo = "1" if letra in bloque_1 else "2"
        
        # Repartimos los 6 partidos del grupo
        for i, p in enumerate(partidos):
            partido_limpio = {"local": p["local"], "visitante": p["visitante"]}
            
            if i < 2:
                jornadas[f"J1.{sufijo}"].append(partido_limpio)
            elif i < 4:
                jornadas[f"J2.{sufijo}"].append(partido_limpio)
            else:
                jornadas[f"J3.{sufijo}"].append(partido_limpio)

    # --- 2. AÑADIMOS LAS ELIMINATORIAS (POR ID) ---
    # Partimos los 16 partidos de dieciseisavos en 2 bloques (8 y 8)
    jornadas["dieciseisavos.1"] = [{"id_partido": i} for i in range(73, 81)]
    jornadas["dieciseisavos.2"] = [{"id_partido": i} for i in range(81, 89)]
    
    # El resto de rondas van enteras
    jornadas["octavos"] = [{"id_partido": i} for i in range(89, 97)]
    jornadas["cuartos"] = [{"id_partido": i} for i in range(97, 101)]
    jornadas["semifinales"] = [{"id_partido": i} for i in range(101, 103)]
    jornadas["finales"] = [{"id_partido": 103}, {"id_partido": 104}] # Tercer puesto y Final

    # --- 3. GUARDAMOS EL JSON ---
    ruta_guardado = ROOT_DIR / "config" / "jornadas.json"
    ruta_guardado.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(jornadas, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Calendario generado estructurado a la perfección (12 en 12 para Grupos).")
    print(f"💾 Guardado en: {ruta_guardado.relative_to(ROOT_DIR)}")

if __name__ == "__main__":
    generar_indice_jornadas()
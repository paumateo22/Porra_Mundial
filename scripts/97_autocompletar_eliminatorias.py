import sys
import json
import random
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

FASES_ORDENADAS = ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]

def simular_goles():
    """Simula goles obligando a que haya un ganador (simulando prórroga/penaltis)."""
    gl = random.choices([0, 1, 2, 3], weights=[30, 40, 20, 10])[0]
    gv = random.choices([0, 1, 2, 3], weights=[30, 40, 20, 10])[0]
    if gl == gv:
        if random.choice([True, False]): gl += 1
        else: gv += 1
    return gl, gv

def generar_pronosticos_falsos():
    print("=======================================================")
    print(" 🤖 AUTO-GENERADOR DE PRONÓSTICOS DE ELIMINATORIAS 🤖")
    print("=======================================================")
    
    ruta_realidad = ROOT_DIR / "data" / "resultados" / "realidad_oficial.json"
    if not ruta_realidad.exists():
        print("❌ Error: No existe realidad_oficial.json. Ejecuta el 98 o 99 primero.")
        return
        
    with open(ruta_realidad, 'r', encoding='utf-8') as f:
        realidad = json.load(f)
        
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    
    for jugador_dir in jugadores:
        nombre_jugador = jugador_dir.name
        print(f"\n⚡ Generando JSONs en cadena para -> {nombre_jugador.upper()}")
        
        # Iteramos sobre cada momento del tiempo (fase de origen)
        for idx_origen, fase_origen in enumerate(FASES_ORDENADAS):
            
            porra_completa = {
                "participante": nombre_jugador,
                "fase_origen": fase_origen,
                "predicciones": {}
            }
            
            # 1. Leer los cruces reales de esa fase origen
            if fase_origen == "finales":
                reales = realidad["eliminatorias"].get("tercer_puesto", []) + realidad["eliminatorias"].get("final", [])
            else:
                reales = realidad["eliminatorias"].get(fase_origen, [])
                
            # Ordenamos por ID para mantener la estructura del bracket (cuadro)
            reales = sorted(reales, key=lambda x: x.get("id_partido", 0))
            
            if not reales:
                continue

            # 2. Simular la fase origen
            partidos_origen = []
            ganadores = []
            perdedores = []
            
            for p_real in reales:
                loc, vis = p_real["local"], p_real["visitante"]
                gl, gv = simular_goles()
                pasa = loc if gl > gv else vis
                pierde = vis if pasa == loc else loc
                
                partidos_origen.append({
                    "local": loc, "visitante": vis,
                    "goles_local": gl, "goles_visitante": gv,
                    "pasa": pasa
                })
                ganadores.append(pasa)
                perdedores.append(pierde)
                
            porra_completa["predicciones"][fase_origen] = partidos_origen
            
            # 3. Simular en cascada el resto de rondas hasta la final
            equipos_vivos = ganadores
            perdedores_semis = perdedores if fase_origen == "semifinales" else []
            
            for sub_fase in FASES_ORDENADAS[idx_origen + 1:]:
                partidos_subfase = []
                nuevos_ganadores = []
                nuevos_perdedores = []
                
                if sub_fase == "finales":
                    # Partido 1: Tercer Puesto
                    if len(perdedores_semis) >= 2:
                        loc3, vis3 = perdedores_semis[0], perdedores_semis[1]
                        gl, gv = simular_goles()
                        pasa3 = loc3 if gl > gv else vis3
                        partidos_subfase.append({
                            "local": loc3, "visitante": vis3, "goles_local": gl, "goles_visitante": gv, "pasa": pasa3
                        })
                    
                    # Partido 2: Gran Final
                    if len(equipos_vivos) >= 2:
                        locF, visF = equipos_vivos[0], equipos_vivos[1]
                        gl, gv = simular_goles()
                        pasaF = locF if gl > gv else visF
                        partidos_subfase.append({
                            "local": locF, "visitante": visF, "goles_local": gl, "goles_visitante": gv, "pasa": pasaF
                        })
                else:
                    # Rondas normales (Octavos, Cuartos, Semis)
                    for i in range(0, len(equipos_vivos), 2):
                        if i+1 >= len(equipos_vivos): break
                        loc, vis = equipos_vivos[i], equipos_vivos[i+1]
                        gl, gv = simular_goles()
                        pasa = loc if gl > gv else vis
                        pierde = vis if pasa == loc else loc
                        
                        partidos_subfase.append({
                            "local": loc, "visitante": vis, "goles_local": gl, "goles_visitante": gv, "pasa": pasa
                        })
                        nuevos_ganadores.append(pasa)
                        nuevos_perdedores.append(pierde)
                        
                    equipos_vivos = nuevos_ganadores
                    if sub_fase == "semifinales":
                        perdedores_semis = nuevos_perdedores
                        
                porra_completa["predicciones"][sub_fase] = partidos_subfase
                
            # 4. Guardar el archivo JSON en su carpeta
            carpeta_destino = jugador_dir / "pronosticos" / "eliminatorias" / fase_origen
            carpeta_destino.mkdir(parents=True, exist_ok=True)
            
            ruta_guardado = carpeta_destino / f"{fase_origen}.json"
            with open(ruta_guardado, 'w', encoding='utf-8') as f:
                json.dump(porra_completa, f, ensure_ascii=False, indent=4)
                
            print(f"  ✅ Creado: eliminatorias/{fase_origen}/{fase_origen}.json")

if __name__ == "__main__":
    generar_pronosticos_falsos()
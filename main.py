import sys
import subprocess
from pathlib import Path

# Conectar con la raíz del proyecto y la carpeta de scripts
ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"

def ejecutar_script(nombre_script):
    """Ejecuta un script individual usando el intérprete de Python actual."""
    ruta = SCRIPTS_DIR / nombre_script
    if not ruta.exists():
        print(f"\n❌ Error Crítico: No se encuentra el archivo {nombre_script} en la carpeta scripts/")
        return False
    
    print(f"\n{'='*50}")
    print(f"🚀 LANZANDO: {nombre_script}")
    print(f"{'='*50}")
    
    try:
        # Ejecuta el script de forma segura
        subprocess.run([sys.executable, str(ruta)], check=True)
        return True
    except subprocess.CalledProcessError:
        print(f"\n❌ El script {nombre_script} ha fallado. Abortando operación en cadena.")
        return False
    except KeyboardInterrupt:
        print(f"\n⚠️ Ejecución cancelada manualmente por el usuario.")
        return False

def mostrar_menu():
    while True:
        print("\n" + "⚽"*30)
        print("   🏆 PANEL DE CONTROL MUNDIAL 2026 🏆   ")
        print("⚽"*30)
        
        print("\n--- 👤 FASE 0: REGISTRO DE JUGADORES ---")
        print("  1. 📝 Registrar Nuevo Jugador / Extraer Infobae (01)")
        
        print("\n--- 🗄️  FASE 1: EXTRACCIÓN Y DATOS ---")
        print("  2. 📸 Procesar Capturas OCR de Eliminatorias (02)")
        print("  3. 📅 Regenerar Índice de Jornadas (00)")
        print("  4. 📥 Actualizar Realidad Oficial SofaScore (05)")
        
        print("\n--- ⚙️  FASE 2: CÁLCULO DE PUNTOS ---")
        print("  5. 🧮 Ejecutar Motor de Puntuación (06a -> 06b -> 06c -> 06e -> 06f -> 06d)")
        
        print("\n--- 📊 FASE 3: VISUALIZACIÓN ---")
        print("  6. 🎨 Generar Vistas Web / GitHub (07 + 07b)")
        
        print("\n--- 🛠️  HERRAMIENTAS DE DESARROLLADOR ---")
        print("  9. 🎲 Ejecutar Simulador de Mundial Completo (99)")
        print(" 10. ⚡ ACTUALIZACIÓN TOTAL (SofaScore + Motor + GitHub + Web)")
        
        print("\n  0. ❌ Salir")
        print("-" * 60)
        
        opcion = input("👉 Selecciona una acción: ").strip()
        
        if opcion == "1":
            ejecutar_script("01_extractor_infobae.py")
            
        elif opcion == "2":
            ejecutar_script("02_extractor_livefutbol.py")
            
        elif opcion == "3":
            ejecutar_script("00_generador_calendario.py")
            
        elif opcion == "4":
            ejecutar_script("05_scraper_sofascore.py")
            
        elif opcion == "5":
            print("\n🔄 Iniciando cálculo en cascada...")
            if ejecutar_script("06a_motor_partidos.py"):
                if ejecutar_script("06b_motor_jornadas.py"):
                    if ejecutar_script("06c_motor_fase_grupos.py"):
                        if ejecutar_script("06e_motor_sorpresas.py"):
                            if ejecutar_script("06f_motor_premios.py"):
                                if ejecutar_script("06d_motor_cierre.py"):
                                    pass
                    
        elif opcion == "6":
            if ejecutar_script("07_generador_vistas.py"):
                ejecutar_script("07b_generador_html.py")
            
        elif opcion == "9":
            print("\n🎲 Creando un multiverso alternativo...")
            ejecutar_script("99_simulador_realidad.py")
            
        elif opcion == "10":
            print("\n⚡ Iniciando actualización absoluta...")
            if ejecutar_script("05_scraper_sofascore.py"):
                if ejecutar_script("06a_motor_partidos.py"):
                    if ejecutar_script("06b_motor_jornadas.py"):
                        if ejecutar_script("06c_motor_fase_grupos.py"):
                            if ejecutar_script("06e_motor_sorpresas.py"):
                                if ejecutar_script("06f_motor_premios.py"):
                                    if ejecutar_script("06d_motor_cierre.py"):
                                        if ejecutar_script("07_generador_vistas.py"):
                                            if ejecutar_script("07b_generador_html.py"):
                                                print("\n✅ ¡ACTUALIZACIÓN TOTAL COMPLETADA! Todo listo para subir a GitHub.")
                    
        elif opcion == "0":
            print("\n👋 ¡Cerrando la sala de máquinas! Hasta pronto.")
            break
            
        else:
            print("\n⚠️ Opción no válida.")

if __name__ == "__main__":
    mostrar_menu()

## 📋 TODO: Próximos Pasos (Fase de Despliegue y Visualización)

- [ ] **1. Orquestador Central (`main.py`)**
  - Crear un menú interactivo en consola para ejecutar todo el pipeline de forma centralizada (Extraer SofaScore -> Procesar OCR -> Correr Motores de Puntuación).

- [ ] **2. Testing End-to-End (Simulacro Completo)**
  - Montar un escenario de prueba con un jugador ficticio y resultados falsos.
  - Ejecutar el flujo del `00` al `06c` y validar matemáticamente que las sumas, los multiplicadores de racha y el sistema de desempate automático no tienen fisuras.

- [ ] **3. Generador de Vistas GitHub (`07_generador_vistas.py`)**
  - Automatizar la creación y actualización del `README.md` principal con la tabla de clasificación general.
  - Generar un `README.md` dinámico dentro de la carpeta de cada participante (traduciendo su `historial_puntos.json` en gráficas, medallas y un listado visual de aciertos ✅/❌).

- [ ] **4. Preparación de Realidad Estática**
  - Crear la plantilla `data/resultados/premios_reales.json` para tenerla lista el día de la final y rellenarla manualmente con los ganadores de los premios extra (MVP, Bota de Oro, Sorpresa...).
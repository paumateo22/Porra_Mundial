### 📝 Tareas Pendientes - Porra Mundial 2026

- [ ] **1. Diseñar las Vistas Individuales (Perfiles de Jugador):** 
  Actualmente el `07_generador_vistas.py` crea un `README.md` muy básico en la carpeta de cada participante. Falta diseñar cómo queremos que se vea su perfil: ¿Añadimos sus equipos favoritos? ¿Una tabla con el detalle de todos los partidos que ha acertado exactamente? ¿Su predicción completa del cuadro de eliminatorias?

- [ ] **2. Revisar la Extracción de Puntos Extra (Sorpresa/Decepción):**
  En la tabla general hemos puesto las columnas, pero hay que confirmar que las llaves del `premios.json` (donde se guardan las respuestas de Google Forms) coinciden exactamente con lo que busca el `07_generador_vistas.py` para que no salgan a cero.

- [ ] **3. Despliegue y Pruebas en GitHub Pages:**
  Hacer el primer `git push` real al repositorio de GitHub. Activar la opción de "GitHub Pages" en la configuración del repositorio. Verificar que los colores HTML (`goldenrod`, `red`) y los enlaces entre el README general y los individuales funcionan correctamente en la versión web.

- [ ] **4. Pruebas de Resiliencia (Casos Extremos):**
  ¿Qué pasa si un participante se olvida de mandar su captura de octavos y falta su `.json`? Hay que asegurarse de que el motor no crashee y simplemente le asigne 0 puntos en esa jornada.

- [ ] **5. Configurar Triggers Remotos desde el Móvil:**
  Vincular las GitHub Actions (`workflow_dispatch` o `repository_dispatch`) con el teléfono móvil. Crear un acceso directo (usando la app Atajos, Tasker o la app oficial de GitHub) para poder ejecutar el cálculo de puntos y la actualización de vistas en la nube con un solo toque, sin necesidad de encender el ordenador.

- [ ] **6. Limpieza de Datos de Prueba:**
  Una vez terminemos los testeos, habrá que vaciar las carpetas de los usuarios de prueba, borrar el `jornadas.json` y el `realidad_oficial.json` generados artificialmente, y dejar el sistema completamente limpio esperando a los participantes reales.

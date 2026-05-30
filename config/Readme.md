### 📝 Tareas Pendientes - Porra Mundial 2026

- [x] **1. Diseñar las Vistas Individuales (Perfiles de Jugador):** ¡Completado! Transformado en un dashboard profesional con historial, multiplicadores trazables, balances y la Matriz Gráfica de Desviaciones con `matplotlib`.

- [x] **2. Revisar la Extracción de Puntos Extra (Sorpresa/Decepción):**
  ¡Completado! Automatizado matemáticamente con el motor `06e` calculando la varianza global de la comunidad para crear umbrales dinámicos. Ya no depende de los formularios.

- [ ] **3. Despliegue y Pruebas en GitHub Pages:**
  Hacer el primer `git push` real al repositorio de GitHub. Activar la opción de "GitHub Pages" en la configuración del repositorio. Verificar que los colores HTML (`goldenrod`, `red`), los enlaces y los PNGs de las gráficas funcionan y se ven correctamente.

- [ ] **4. Pruebas de Resiliencia (Casos Extremos):**
  ¿Qué pasa si un participante se olvida de mandar su captura de octavos y falta su `.json`? Hay que asegurarse de que el motor no crashee y simplemente le asigne 0 puntos en esa jornada.

- [ ] **5. Configurar Triggers Remotos desde el Móvil:**
  Vincular las GitHub Actions (`workflow_dispatch` o `repository_dispatch`) con el teléfono móvil. Crear un acceso directo para poder ejecutar el cálculo de puntos y la actualización de vistas en la nube con un solo toque.

- [ ] **6. Limpieza de Datos de Prueba:**
  Una vez terminemos los testeos, vaciar las carpetas de los usuarios de prueba, borrar el `jornadas.json` y el `realidad_oficial.json` generados artificialmente, y dejar el sistema completamente limpio.

- [ ] **7. Motor de Premios Subjetivos (Google Forms):**
  Crear un script (ej. `06f_motor_premios.py`) que lea el CSV de Google Forms para otorgar los puntos fijos del resto de galardones: MVP, Bota de Oro, Guante de Oro, Mejor Joven y Gol del Torneo.

- [ ] **8. Archivo de Dependencias (`requirements.txt`):**
  Crear este archivo en la raíz para que GitHub Actions sepa que tiene que instalar `matplotlib` antes de ejecutar el generador de vistas, permitiendo crear las imágenes PNG en la nube.

- [ ] **9. Aplicar Lógica de Desempates:**
  Asegurar que el motor de cierre (`06d`) use los criterios definidos en el `settings.json` (`criterio_1`, `criterio_2`, etc.) para ordenar automáticamente a los jugadores empatados a puntos en el CSV del ranking.

- [ ] **10. Blindaje del Scraper de SofaScore:**
  Planear un "Plan B" (como un input manual desde la consola) por si el scraper se cae un día crítico debido a cambios en la web o bloqueos durante el torneo.

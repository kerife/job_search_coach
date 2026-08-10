# Job Search Coach - Diseño del plugin para Codex

Fecha: 2026-08-05

## Objetivo

Construir un plugin modular para Codex que funcione como coach integral de búsqueda de empleo. Debe ayudar a identificar oportunidades de alta compensación, optimizar la presencia profesional, preparar procesos de selección y medir resultados. Su especialidad principal será LinkedIn y soportará México, Estados Unidos y trabajo remoto internacional.

## Usuarios

### Autoservicio

El candidato proporciona su perfil, CV, objetivos, restricciones y vacantes. El agente entrega análisis y borradores, y solicita autorización puntual antes de cualquier acción externa.

### Coach mode

Un coach administra varios casos aislados, revisa entregables y registra resultados. Los datos de un candidato no deben aparecer en otro caso.

## Arquitectura del plugin

El producto se distribuirá como un plugin nativo llamado `job-search-coach`. El manifiesto `.codex-plugin/plugin.json` expondrá una colección de skills bajo un mismo namespace y una experiencia coherente en Codex.

La skill principal `job-search-coach` será el orquestador. Detectará la etapa del candidato, seleccionará el módulo adecuado, aplicará las reglas compartidas de evidencia y privacidad, y mantendrá el flujo del caso. Las skills especializadas harán el trabajo de dominio.

Skills previstas:

1. `job-search-coach` - orquestación, intake, consentimiento, estado y selección de módulos.
2. `optimize-linkedin-career` - núcleo experto en LinkedIn.
3. `discover-high-value-career-paths` - oportunidades de alta compensación y transiciones realistas.
4. `research-target-job-market` - demanda, salarios, requisitos y brechas actuales.
5. `optimize-job-search-assets` - CV, cartas, portafolio y materiales ATS.
6. `prepare-role-interviews` - preparación específica para la vacante.
7. `recommend-career-learning` - cursos, certificaciones y proyectos por retorno esperado.
8. `track-job-search-outcomes` - resultados a 14/30/60/90 días.

Cada skill se diseñará, probará y confirmará por separado antes de iniciar la siguiente. El orquestador se probará primero como router mínimo y se ampliará únicamente cuando los módulos correspondientes estén validados.

### Estructura prevista

```text
job-search-coach/
├── .codex-plugin/
│   └── plugin.json
├── README.md
├── skills/
│   ├── job-search-coach/
│   │   ├── SKILL.md
│   │   └── references/
│   ├── optimize-linkedin-career/
│   ├── discover-high-value-career-paths/
│   ├── research-target-job-market/
│   ├── optimize-job-search-assets/
│   ├── prepare-role-interviews/
│   ├── recommend-career-learning/
│   └── track-job-search-outcomes/
├── scripts/
└── tests/
```

Las referencias compartidas definirán el esquema del expediente, los niveles de evidencia, límites de acción y formatos de entrega. Los scripts se reservarán para validaciones deterministas, generación de plantillas y métricas; no se usarán para esconder criterio profesional que deba ser visible en las skills.

### Plugin y Workspace Agent

El plugin será la fuente de verdad versionada y portable. Un Workspace Agent llamado `Job Search Coach` podrá configurarse posteriormente como interfaz conversacional con identidad, prompts iniciales y memoria controlada, pero solo después de validar el plugin. El agente será un consumidor del plugin, no una implementación paralela.

### Integraciones

La primera versión no incluirá un servidor MCP ni una app propia. Usará capacidades disponibles en Codex —navegación web actual, Chrome autorizado y archivos proporcionados por el usuario— mediante instrucciones explícitas en las skills. Una integración nueva solo se agregará si una prueba demuestra que las capacidades existentes no cubren el caso.

### Distribución

El desarrollo será local y versionado en Git. La instalación se realizará mediante un marketplace local después de validar el plugin. Crear o modificar una entrada de marketplace, instalar el plugin o publicar un Workspace Agent son pasos separados y requieren autorización explícita en el momento de ejecutarlos.

## Especialidad central: LinkedIn

`optimize-linkedin-career` debe cubrir:

- Auditoría visual y textual de foto, banner, nombre, URL, titular, ubicación, contacto, About, experiencia, aptitudes, Destacados, certificaciones, educación, recomendaciones, actividad y preferencias laborales.
- Inspección de LinkedIn con la sesión del candidato cuando exista autorización y una herramienta compatible.
- Comparación con vacantes actuales en LinkedIn Jobs y fuentes públicas primarias.
- Posicionamiento para búsquedas de recruiters mediante títulos, seniority, ubicación, idiomas, skills y palabras clave verificables.
- Reescritura de titular, About y experiencia sin inventar logros, escala, responsabilidades o tecnologías.
- Estrategia de evidencia: portafolio, proyectos, recomendaciones y Destacados.
- Estrategia de networking, mensajes y contenido como borradores.
- Preparación específica para vacantes encontradas.
- Registro de Analytics antes y después de cambios.
- Experimentos controlados para evaluar titulares, About, aptitudes, actividad y preferencias.
- Identificación explícita de secciones no visibles o restringidas.
- Rechazo de afirmaciones sobre el algoritmo de LinkedIn sin fuente o evidencia suficiente.

## Flujo del candidato

1. Obtener consentimiento, modo de uso y límites de acción.
2. Registrar línea base: objetivo, compensación, ubicación, autorización laboral, perfil, CV y métricas disponibles.
3. Auditar LinkedIn, CV, portafolio y coherencia entre fuentes.
4. Investigar vacantes y compensación actuales.
5. Priorizar brechas reales y oportunidades alcanzables.
6. Producir borradores y un plan de mejora.
7. Solicitar aprobación antes de editar, publicar, conectar, escribir o postular.
8. Preparar aplicaciones e entrevistas por vacante.
9. Recomendar aprendizaje únicamente cuando una brecha aparezca repetidamente y tenga retorno probable.
10. Medir resultados a 14/30/60/90 días y ajustar la estrategia.

## Evidencia y afirmaciones

Clasificar cada dato:

- **Observado:** visible en LinkedIn, CV, portafolio, analytics o vacante.
- **Declarado:** proporcionado por el candidato, pendiente o no de documentación.
- **Inferido:** conclusión razonable que debe etiquetarse como inferencia.
- **Recomendado:** propuesta todavía no ejecutada.

Jerarquía de fuentes de mercado:

1. Vacantes vigentes y páginas oficiales de empleadores.
2. Datos gubernamentales o metodologías salariales transparentes.
3. Informes reputados con fecha, muestra y geografía.
4. Plataformas agregadoras y evidencia anecdótica, señaladas como menor confianza.

No prometer causalidad, contratación, rapidez ni aumento salarial. Reportar resultados observados y nivel de confianza.

## Datos y privacidad

- Aislar cada expediente y minimizar PII.
- No repetir teléfono, correo, dirección u otros identificadores sin necesidad.
- No reutilizar CV, mensajes, métricas o resultados entre candidatos.
- Mantener benchmarking desactivado por defecto.
- Incluir resultados anonimizados en benchmarks solo con consentimiento explícito y revocable.
- No almacenar conversaciones privadas, contraseñas, cookies ni datos de sesión.

## Acciones externas

El agente puede leer, analizar y preparar borradores. Debe solicitar autorización inmediatamente antes de:

- Editar un perfil.
- Publicar contenido.
- Enviar un mensaje o solicitud de conexión.
- Postular a una vacante.
- Subir un CV o archivo personal.
- Compartir datos con un tercero.

La autorización para una acción no autoriza acciones posteriores.

## Medición

Línea base y seguimiento por candidato:

- Apariciones en búsquedas y visitas al perfil.
- Contactos relevantes de recruiters.
- Aplicaciones enviadas.
- Tasa de respuesta.
- Entrevistas por etapa.
- Ofertas.
- Días hasta primera entrevista y oferta.
- Compensación anterior, objetivo y ofrecida, expresadas por geografía y moneda.
- Tiempo invertido y cambios realizados.

Usar ventanas de 14/30/60/90 días. No atribuir un resultado a un cambio aislado cuando existan varias intervenciones simultáneas.

## Entregables

- Diagnóstico ejecutivo y puntuaciones explicadas.
- Matriz observado/declarado/inferido/recomendado.
- Comparación con mercado y compensación.
- Borradores de LinkedIn y CV.
- Plan priorizado por impacto, esfuerzo y evidencia.
- Paquete de preparación por vacante.
- Ruta de aprendizaje con costo, tiempo y retorno esperado.
- Tablero de seguimiento y reporte de experimentos.

## Manejo de incertidumbre y errores

- Si una sección no es visible, indicarlo y continuar con la evidencia disponible.
- Si CV y LinkedIn se contradicen, detener la redacción de esa sección y solicitar confirmación.
- Si una vacante expiró, no usarla como evidencia de demanda actual.
- Si no hay datos salariales comparables, entregar un rango amplio o declarar evidencia insuficiente.
- Si una herramienta falla, no sustituir una fuente autenticada por otra menos adecuada para evadir la restricción.
- Si faltan métricas, usar marcadores de confirmación y preguntas concretas; no inventarlas.

## Estrategia de pruebas

Cada skill seguirá RED-GREEN-REFACTOR:

1. Ejecutar escenarios realistas sin la skill y documentar omisiones, invenciones, recomendaciones genéricas o acciones no autorizadas.
2. Escribir la guía mínima que corrija los fallos observados.
3. Repetir los escenarios con la skill.
4. Agregar variaciones de profesión, seniority, geografía, datos incompletos y contradicciones.
5. Validar estructura, frontmatter, activación, concisión y cumplimiento de límites.

Casos mínimos de evaluación:

- Perfil tecnológico senior con CV y LinkedIn inconsistentes.
- Profesional no técnico que busca una transición de alta compensación.
- Candidato junior sin métricas ni portafolio.
- Vacante concreta con entrevista próxima.
- Candidato con recomendaciones basadas en tecnologías que no domina.
- Coach mode con dos candidatos y riesgo de contaminación de datos.

## Fases

### Fase 1

Generar y validar el esqueleto del plugin, su manifiesto y un orquestador mínimo. Construir `optimize-linkedin-career` con auditoría, mercado, borradores y límites de acción.

### Fase 2

Construir investigación de mercado y rutas de alta compensación.

### Fase 3

Construir CV/ATS, entrevistas y aprendizaje.

### Fase 4

Construir seguimiento, experimentos, benchmarks anónimos y coach mode.

### Fase 5

Completar el orquestador, probar el flujo integral, instalar el plugin en un marketplace local y preparar opcionalmente el Workspace Agent. Publicar únicamente con autorización explícita.

## Criterios de éxito

- El agente distingue hechos, inferencias y recomendaciones en todos los entregables.
- Ninguna prueba contiene logros o tecnologías inventadas.
- LinkedIn recibe una auditoría completa y específica, no consejos genéricos.
- Las recomendaciones de formación se vinculan a vacantes y retorno esperado.
- La preparación de entrevista depende de la vacante y del historial real del candidato.
- Ninguna acción externa ocurre sin aprobación puntual.
- Los datos de candidatos permanecen aislados.
- Los cambios y resultados pueden auditarse longitudinalmente.
- El manifiesto y todas las skills pasan la validación oficial del formato de plugins de Codex.
- Una sesión nueva de Codex descubre el orquestador y activa el módulo correcto en los escenarios de prueba.

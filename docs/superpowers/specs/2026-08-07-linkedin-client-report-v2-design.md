# Diseño del diagnóstico ejecutivo de LinkedIn v2

Fecha: 2026-08-07

Estado: aprobado para especificación; pendiente de revisión antes de implementar

## Objetivo

Convertir el diagnóstico de LinkedIn en una entrega que una persona pueda leer,
entender y ejecutar sin interpretar filas de contrato. La primera pantalla debe
comunicar una decisión profesional, la evidencia que la sostiene y las tres
acciones de mayor valor. Las matrices, fuentes y controles permanecen
disponibles como apéndice auditable, pero no dominan la respuesta visible.

El cambio debe mejorar la calidad del diagnóstico. No promete posicionamiento
en búsquedas, respuesta de reclutadores, entrevista, oferta, salario ni tiempo
de contratación.

## Problema observado

El skill ya define `coach_brief`, cover sheets, una muestra de reporte renderizado
y controles de entrega. Sin embargo, el output canónico sigue expresando esos
artefactos como filas largas delimitadas por punto y coma. Una respuesta puede
cumplir el contrato y seguir pareciendo un volcado técnico. En la línea base
auditada, el `coach_brief` contiene 20 filas, 28,802 caracteres y 2,154 palabras;
la fila que se declara renderizada tiene 1,593 caracteres, 15 puntos y coma y
16 signos `=`. El smoke completo tiene 393 filas y 382,264 caracteres.

Las inspecciones autorizadas de dos perfiles reales también mostraron que el
diagnóstico debe adaptarse al caso:

- Un perfil puede tener evidencia técnica abundante, pero una identidad visual
  y un mensaje de posicionamiento dispersos.
- Otro puede tener una identidad visual coherente y actividad relevante, pero
  un titular y una narrativa demasiado generales para comunicar nivel e impacto.

Los perfiles reales se usan únicamente para derivar escenarios estructurales.
No se conservarán nombres, fotografías, URLs, texto crudo, analíticas privadas,
identificadores de conexión ni datos de contacto en fixtures o evaluaciones.

## Decisión de diseño

La salida tendrá dos capas explícitas y ordenadas:

1. `client_report`: reporte Markdown cliente-primero, legible y accionable.
2. `evidence_appendix`: contratos, trazabilidad, fuentes y controles técnicos.

El reporte es la entrega. El apéndice explica por qué. Una fila que describa
cómo se vería el reporte no sustituye al reporte renderizado. No se añadirá un
nuevo contrato cliente equivalente a los existentes: el renderer consolidará
la información ya calculada y ocultará de la primera pantalla agenda, delivery
map, quality gate, handoffs y drills.

## Contrato del reporte visible

`client_report` inicia en el byte 0 con un H1 localizado. En español usa
`# Diagnóstico ejecutivo de LinkedIn`; en inglés usa
`# LinkedIn Executive Diagnostic`. La v2 conserva el idioma de la solicitud y
mantiene mapas explícitos `es` y `en` para encabezados. Antes del H1 no puede
aparecer ninguna fila técnica, identificador de contrato ni inventario de
evidencia.

El reporte visible contiene, en este orden:

1. `## Veredicto`: una decisión en lenguaje natural y una frontera de confianza.
2. `## Calificación`: tabla de dimensiones con estado, puntuación o `No evaluado`,
   evidencia observada y razón breve.
3. `## Las tres decisiones prioritarias`: exactamente tres acciones ordenadas
   por impacto esperado sobre claridad o credibilidad, esfuerzo y dependencia
   de evidencia. El impacto es `COACH_HEURISTIC`, no un outcome laboral.
4. `## Copy listo para revisar`: un titular, una apertura de About y un ejemplo
   de experiencia; cada bloque indica `listo`, `requiere confirmación` u `omitir`.
5. `## No cambies todavía`: máximo tres claims, tecnologías, métricas o activos
   que no deben publicarse sin evidencia o revisión de confidencialidad.
6. `## Plan privado de siete días`: únicamente perfil, copy y prueba profesional;
   ninguna acción externa se presenta como ejecutada o autorizada y no duplica
   el plan de outreach o primera entrevista.
7. `## Evidencia pendiente`: sólo preguntas cuya respuesta pueda cambiar una
   puntuación, una prioridad o una pieza de copy.
8. `## Límites del diagnóstico`: explica que las recomendaciones no predicen
   ranking, respuestas, entrevistas ni contratación.

El primer `## Apéndice de evidencia` —o su equivalente localizado— termina
`client_report` e inicia `evidence_appendix`. El conteo y los gates del reporte
terminan antes de ese encabezado.

El cuerpo visible tiene un máximo obligatorio de 800 palabras, sin contar la
tabla de calificación. El rango de 450 a 800 es una guía, no un mínimo. Puede ser
menor cuando falta evidencia y nunca se rellena con contenido genérico.

## Calificación multidimensional

La tabla cubre siete dimensiones:

- identidad visual y primera impresión;
- titular y propuesta de valor;
- apertura y narrativa de About;
- experiencia y densidad de prueba;
- skills y coherencia de keywords;
- activos de prueba y credibilidad;
- completitud y descubribilidad.

Cada dimensión usa una escala de 0 a 100 sólo cuando existe evidencia suficiente.
La dimensión visual debe usar `No evaluado` si no hubo captura visual autorizada.
No se infieren edad, raza, origen étnico, género, discapacidad, salud,
personalidad, atractivo ni confiabilidad a partir de una fotografía.

La puntuación global reutiliza el modelo ponderado existente y se calcula
únicamente sobre dimensiones evaluadas. Debe mostrar denominador, dimensiones
excluidas y confianza. No puede mezclar `No evaluado` con cero, ni presentar una
calificación provisional como certeza. El score visible se deriva del ledger;
no se acepta otro número declarado de forma independiente.

## Reglas de personalización y evidencia

- Cada prioridad se enlaza con al menos una observación y una dimensión baja o
  bloqueada.
- Cada copy usa hechos `verified` o `candidate-reported`; un hecho `inferred`
  se marca como hipótesis y `unknown` nunca se convierte en claim público.
- Las recomendaciones nombran el problema específico. Frases intercambiables
  como “mejora tu perfil”, “agrega keywords” o “sé más atractivo” no satisfacen
  el contrato.
- Una tecnología solicitada por una vacante pero no respaldada se confirma o se
  omite del copy. La transferencia razonable sólo puede explicarse en rationale,
  notas del coach o puente de entrevista; nunca se presenta como experiencia o
  skill visible del candidato hasta confirmación.
- Las fuentes actuales respaldan criterios de completitud, legibilidad,
  preferencias, skills y uso de secciones; no respaldan causalidad sobre
  resultados de contratación.

## Apéndice auditable

El apéndice conserva los artefactos existentes de scorecard, evidencia,
fronteras de claims, copy, fuentes, autorización y medición. Debe:

- aparecer después del reporte visible;
- compartir el mismo `candidate_id` internamente;
- permitir rastrear cada score, prioridad y copy a IDs de evidencia;
- mantenerse fuera de la primera pantalla;
- evitar nombres, URLs completas, datos de contacto, texto crudo y analíticas
  privadas;
- permanecer disponible para depuración, evaluación o solicitud explícita.

En modo normal, `evidence_appendix` muestra sólo un índice compacto: máximo 250
palabras, IDs de evidencia, fuentes, cobertura, claims bloqueados y cómo pedir
el detalle. No muestra filas canónicas completas. Sólo en modo `debug`, `eval`
o ante solicitud explícita puede mostrar el apéndice completo, siempre después
del reporte. El payload normal completo no puede superar 1,100 palabras.

## Validación semántica

Se añade un validador de entrega completa, no sólo validadores por fila. Debe
rechazar:

- una muestra de reporte descrita en una fila sin reporte Markdown real;
- cualquier contrato antes del título del reporte;
- cualquier `candidate_id=`, clave `linkedin_*=` o fila canónica delimitada por
  punto y coma dentro de `client_report`;
- placeholders o texto tokenizado como `x`, `criteria`, `generic`, `TBD` o
  equivalentes sin contexto;
- puntuaciones sin observación, denominador o estado de evidencia;
- puntuaciones contradictorias entre reporte y apéndice;
- prioridades que no enlacen evidencia y una brecha concreta;
- más o menos de tres decisiones prioritarias;
- copy sin una audiencia, problema, evidencia o frontera de claim; el texto
  cliente muestra el estado y la frontera necesaria, y la metadata completa se
  mantiene en el apéndice;
- prioridades cuyo fingerprint
  `section+diagnosed_gap+action_type+evidence_ids+done_when` no sea específico;
- claims de resultados, acciones externas ejecutadas o autorización inferida;
- PII, texto crudo, analíticas privadas o contaminación entre candidatos.

El validador también debe comprobar consistencia de estado: un elemento
`bloqueado` o `requiere confirmación` no puede aparecer como listo para publicar
en otra sección.

Los rechazos deterministas son la única capa bloqueante. Un grader de IA
advisory, con prompt, rúbrica y versión de modelo registrados, puede evaluar
especificidad, utilidad decisional, fidelidad a evidencia, diferenciación,
claridad, actionability y límites en una escala de 1 a 5. Consume sólo fixtures
sintéticos o un reporte previamente minimizado, devuelve evidencia textual por
nota, no recibe screenshots, URLs de perfil ni texto crudo, y no puede anular
un fallo determinista ni convertir fluidez en veracidad.

## Escenarios de evaluación

### Escenario A: señal técnica dispersa

Fixture sintético con evidencia de operaciones de plataforma, automatización y
alcance técnico; titular enumerativo, banner no alineado, narrativa sin impacto
cuantificado y claims de una tecnología objetivo sin confirmar.

El reporte debe priorizar claridad de rol, evidencia de impacto y coherencia
visual; conservar la tecnología no confirmada fuera del copy listo.

### Escenario B: identidad coherente, narrativa general

Fixture sintético con foto y banner profesionalmente coherentes, actividad y
credenciales relevantes; titular genérico, About breve, experiencia de
liderazgo sin alcance ni resultados observables.

El reporte debe reconocer la fortaleza visual y priorizar especialidad,
alcance de liderazgo, resultados y prueba profesional. No debe copiar las
prioridades del escenario A.

### Escenario C: estructura sin evidencia visual

Fixture sintético con presencia de secciones y estados textuales, pero sin
captura visual autorizada. La dimensión visual queda `No evaluado`, se excluye
del denominador y el reporte solicita el mínimo de evidencia que cambiaría la
decisión.

### Escenario D: evidencia visual parcial

Fixture sintético donde sólo foto o banner es inspeccionable. El reporte puede
emitir observaciones cualitativas sobre lo disponible, pero no un score visual
agregado.

### Escenarios adversariales

- reporte convertido en una sola fila de contrato;
- reporte pulido pero sin evidencia enlazada;
- siete scores idénticos sin justificación;
- visual puntuado sin captura autorizada;
- copy con claim tecnológico desconocido;
- tres consejos genéricos intercambiables entre A y B;
- contradicción `requiere confirmación` frente a `listo`;
- apéndice de un candidato unido al reporte de otro;
- presencia de nombre, URL, contacto, texto crudo o analítica privada;
- lenguaje que garantiza ranking, respuesta o entrevista.
- placeholder en cualquier combinación de mayúsculas y minúsculas o marcador
  `[CONFIRMAR DESPUÉS]` sin una pregunta concreta;
- score visible 61 frente a ledger 72;
- prioridad sin sección, acción, timebox o `done_when`;
- frontera de privacidad correcta acompañada por email, teléfono o URL de perfil;
- reporte y apéndice con IDs de candidato distintos;
- resultado correcto con candidato, score, denominador y claim bloqueado
  distintos al fixture principal;
- variantes foto-only y banner-only del escenario D;
- evidencia textual escasa con reporte corto y sin relleno;
- copy `listo` cuyo claim también aparece en `No cambies todavía`.

Los escenarios A y B deben diferir en al menos dos de sus tres fingerprints de
prioridad, en el gap principal y en el copy recomendado. Cada uno incluye por
lo menos dos categorías semánticas esperadas; no se valida por texto exacto.
Los escenarios A–D usan IDs, scores, denominadores, cobertura y claims bloqueados
distintos. Renderer y validator no pueden contener literales esperados para
`linkedin-jenkins-001`, score `72`, `Jenkins` ni un orden de scores memorizado.

## Fuentes y actualización

La jerarquía de evidencia será:

1. LinkedIn Help y LinkedIn Talent Blog para comportamiento documentado del
   producto y orientación oficial.
2. Fuentes primarias del mercado o empleador para requisitos de vacantes.
3. Fuentes secundarias fechadas sólo para heurísticas de lectura o coaching.

Cada fuente registra URL, fecha de acceso, fecha de publicación cuando exista,
alcance y límite de inferencia. Una fuente secundaria no puede justificar una
promesa causal ni un supuesto algoritmo de ranking. Las fuentes secundarias
fechadas son opcionales: no se exigen para aparentar respaldo cuando una fuente
oficial es suficiente. Pesos, bandas, ventanas de lectura rápida y prioridades
propias del coach se etiquetan `COACH_HEURISTIC`.

La sección Featured se evalúa como prueba visible del trabajo, no como señal de
búsqueda. El score del coach no se presenta como LinkedIn Job Match, Recruiter
ranking ni métrica interna de LinkedIn.

Cada `source_id` resuelve a una entrada única con `access_date`, alcance y límite
de inferencia. El catálogo mínimo cubre buen perfil, foto, cover, Featured,
skills, Job Match, AI Hiring Agents y conexión entre job seekers y hirers. Se
revalida cuando cambia la guía o transcurren 90 días. Una fuente vencida o
inaccesible degrada la recomendación a `COACH_HEURISTIC` o bloquea el claim;
nunca pasa silenciosamente. Un dato agregado oficial, incluido “hasta 2x”, no
alimenta lift, score ni predicción individual.

## Privacidad y autorización

- La inspección de perfil es de sólo lectura y se limita a la superficie
  autorizada.
- Los fixtures son sintéticos, compuestos y contrafactuales; no corresponden uno
  a uno con un perfil real ni almacenan una tabla de correspondencia.
- `structural_state_fixture` usa estados enumerados y
  `additionalProperties=false`. `synthetic_fact_catalog` aporta facts totalmente
  inventados y controlados para generar copy verificable. Puede incluir
  `role_family`, `capability_family`, `leadership_scope_state`,
  `target_capability_evidence_state`, `scope_bucket` y fact IDs sintéticos.
- No admite texto, nombres, cargos literales, organizaciones, instituciones,
  ubicaciones, fechas, tecnologías, conteos sociales, analytics, URLs de perfil,
  imágenes, OCR, hashes, embeddings ni identificadores derivados de los perfiles
  inspeccionados. Las URLs públicas del catálogo de fuentes, metadata del paquete,
  nombres genéricos de métricas y sentinelas inequívocamente sintéticos de tests
  negativos sí están permitidos en sus rutas correspondientes.
- Cada fixture registra
  `origin_class=synthetic_from_authorized_structural_review`,
  `derivation=composite_plus_counterfactual_perturbation` y
  `real_profile_mapping=none_created`. Su composición se revisa contra
  singularización sin requerir ni conservar el mapping fuente.
- Revisar un perfil no autoriza editarlo, publicar, conectar, enviar mensajes,
  aplicar, cargar archivos ni compartir contenido.
- Cualquier acción externa requiere acción, objetivo y contenido exactos,
  confirmados inmediatamente antes de ejecutarse.

## Entregables de implementación

1. Instrucciones de renderizado cliente-primero en el skill y referencias.
2. Cuatro fixtures estructurales sintéticos, compuestos y contrafactuales.
3. Escenarios RED de calidad, evidencia, privacidad y contradicción.
4. Validador semántico de reporte completo.
5. Output canónico actualizado con reporte Markdown real antes del apéndice.
6. Pruebas de regresión para contratos y fronteras existentes.
7. Documentación de fuentes y límites de inferencia.
8. Inventario y saneamiento limitado a los fixtures, evals y artefactos derivados
   de perfil que este incremento cree o modifique. Un audit global del checkout
   y la limpieza del historial Git son incrementos separados. Hasta completarlos,
   el repositorio se considera local y no queda aprobado para publicación.

## Criterios de aceptación

- El parser encuentra una sola instancia de las ocho secciones cliente, en el
  orden definido, antes del primer encabezado de apéndice.
- `client_report` contiene cero `candidate_id=`, claves `linkedin_*=` y filas
  canónicas delimitadas por punto y coma.
- Los escenarios A y B difieren en al menos dos de tres fingerprints de
  prioridad, gap principal y copy recomendado.
- Cada una de las tres prioridades y los tres bloques de copy está trazada a
  evidence IDs y estados del apéndice.
- El validador rechaza todos los escenarios adversariales definidos.
- El output actual de 2,154 palabras falla el nuevo gate de presentación.
- Los artefactos nuevos o modificados derivados de perfil no contienen nombres,
  URLs de perfil, imágenes, texto crudo, valores de analytics ni combinaciones
  singularizables procedentes de perfiles reales. Los checks deterministas
  cubren emails, teléfonos, URLs de perfil, rutas, campos privados y texto crudo;
  una revisión advisory separada cubre entidades libres y riesgo de singling-out.
- El gate operativo registra que no hubo edición, publicación, conexión, mensaje,
  aplicación, carga ni otro efecto externo; el unittest verifica que ningún
  contrato infiera autorización.
- Las suites focales, estáticas, completas y el validador oficial quedan verdes.
- El plugin instalado localmente corresponde al commit verificado.
- No ocurre ninguna acción externa en LinkedIn durante la implementación o las
  pruebas.

## Fuera de alcance de este incremento

- Recorrer de forma amplia la lista de conexiones.
- Identificar o conservar nombres de reclutadores.
- Enviar solicitudes, mensajes, publicaciones o aplicaciones.
- Activar automáticamente vacantes o predecir probabilidad de entrevista.
- Reemplazar el puente de vacantes vigentes o la auditoría de integridad del
  funnel, que permanecen como siguientes incrementos priorizados.

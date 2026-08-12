# Diseño de posicionamiento de LinkedIn

Fecha: 2026-08-05

## Objetivo

Definir un método reutilizable para posicionar un perfil profesional hacia
roles de confiabilidad, plataforma, infraestructura y DevOps sin guardar datos
identificables de una persona candidata en el repositorio.

## Principios de posicionamiento

- Separar el título formal, la función real y el rol objetivo cuando difieran.
- Describir la experiencia de infraestructura según su alcance confirmado:
  laboratorio, desarrollo/pruebas, producción o desconocido.
- Presentar automatización, troubleshooting, observabilidad y liderazgo solo
  cuando exista evidencia suministrada por la persona candidata.
- Mantener separados el empleo actual, la geografía, la elegibilidad y el
  arreglo laboral; no inferir ninguno de ellos.
- Tratar la IA como una herramienta que aumenta la capacidad operativa, no como
  un título o especialidad que la evidencia no respalde.

## Evidencia verificable

La implementación puede recibir, de forma temporal y fuera del repositorio:

- alcance de plataformas y entornos operados;
- incidentes, troubleshooting, automatización y resultados observables;
- liderazgo, colaboración y ownership, con fechas y alcance confirmados;
- herramientas o certificaciones realmente utilizadas;
- restricciones de producción, métricas, geografía y elegibilidad.

Los artefactos públicos deben conservar únicamente categorías, estados de
evidencia y ejemplos sintéticos. No deben incluir nombres, empleadores,
ubicaciones exactas, títulos personales, URLs de perfiles, contactos,
identificadores ni rutas del equipo local.

## Límites de precisión

- No afirmar responsabilidad productiva, SLO, MTTR, MTTD, disponibilidad o
  resultados financieros sin evidencia explícita.
- No convertir experiencia de laboratorio o desarrollo/pruebas en experiencia
  de producción.
- No presentar una herramienta, certificación o proyecto personal como
  experiencia profesional.
- No inventar procesos de contratación, salarios, demanda, elegibilidad ni
  tiempos de transición.
- No incluir información de empleadores, clientes, compañeros o sistemas
  internos en ejemplos públicos.

## Arquitectura del mensaje

1. Titular: nivel y función objetivo, con tecnologías solo si están respaldadas.
2. About: problemas resueltos, alcance, decisiones y resultados verificables.
3. Experiencia: separar responsabilidades, contexto, automatización y límites.
4. Evidencia adicional: usar proyectos públicos y no confidenciales.
5. Próximo paso: pedir la evidencia faltante antes de editar o publicar.

## Titular base sintético

Senior Platform / Reliability Engineer | Kubernetes, Observability & Automation

## Criterios de éxito

- Un reclutador identifica rápidamente nivel, función y núcleo técnico.
- El perfil comunica alcance sin aparentar experiencia no demostrada.
- SRE, DevOps y Platform quedan como destinos coherentes con la evidencia.
- Cada afirmación puede rastrearse a un hecho suministrado y no sensible.
- El repositorio no conserva datos biográficos, rutas locales ni identificadores
  de la persona candidata.

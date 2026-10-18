# Historias de usuario

Este documento registra historias iniciales a partir de las funciones que ya existen en el chatbot. La asignación de responsables queda pendiente de acuerdo del equipo; no se debe considerar una historia asignada hasta que se escriba el nombre de quien la trabajó.

## HU-01 — Realizar consultas generales

- **Historia:** Como visitante, quiero hacer preguntas generales al asistente sin ingresar mi identificación, para obtener orientación sobre la Universidad.
- **Estado:** Implementada; el frontend permite continuar sin identificación y el backend expone `POST /ai/generate`.
- **Criterios de aceptación:**
  - El usuario puede omitir la identificación y escribir una pregunta.
  - La pregunta se envía al backend y la respuesta aparece en el chat.
  - Una consulta general no debe incluir datos personales de perfiles institucionales.
- **Responsable:** Pendiente de asignación.

## HU-02 — Consultar información personalizada

- **Historia:** Como estudiante o integrante registrado de la comunidad universitaria, quiero proporcionar mi identificación para que el asistente use la información académica asociada a un perfil existente.
- **Estado:** Implementada parcialmente; se comprueba la existencia del perfil y se informa cuando no se valida. La comprobación no equivale a autenticación institucional.
- **Criterios de aceptación:**
  - Una identificación existente puede habilitar contexto del perfil correspondiente.
  - Una identificación no encontrada permite continuar con consultas generales.
  - Una identificación no validada no debe cargar datos académicos personales ni asociar el historial a ese perfil.
- **Responsable:** Pendiente de asignación.

## HU-03 — Guardar el historial del chat

- **Historia:** Como equipo del proyecto, queremos guardar preguntas y respuestas del asistente en PostgreSQL para conservar un registro de las conversaciones.
- **Estado:** Implementada para el flujo principal de generación de IA.
- **Criterios de aceptación:**
  - Cada respuesta generada se guarda junto con la pregunta y el estado correspondiente.
  - El backend usa la base PostgreSQL configurada para el proyecto.
  - Si falla el guardado, el backend comunica el error en lugar de reportar el intercambio como guardado.
- **Responsable:** Pendiente de asignación.

## HU-04 — Registrar una sugerencia institucional

- **Historia:** Como integrante de la comunidad universitaria, quiero enviar una queja, reclamo, sugerencia o felicitación para dejar constancia de mi opinión.
- **Estado:** El endpoint `POST /ai/sugerencia` está implementado; falta verificar y documentar un flujo de uso desde la interfaz.
- **Criterios de aceptación:**
  - El servicio acepta los tipos de sugerencia permitidos y rechaza tipos no válidos.
  - Para registrar la sugerencia se valida que la identificación corresponda a un perfil existente.
  - La sugerencia queda guardada con estado inicial `Pendiente`.
- **Responsable:** Pendiente de asignación.

## Asignación del equipo

Completar esta tabla en reunión de equipo. Una persona puede asumir varias historias, pero cada historia debe tener al menos un responsable identificado.

| Historia | Responsable(s) | Evidencia de trabajo/entrega |
| --- | --- | --- |
| HU-01 | Pendiente | Pendiente |
| HU-02 | Pendiente | Pendiente |
| HU-03 | Pendiente | Pendiente |
| HU-04 | Pendiente | Pendiente |

Integrantes registrados en el README: Kevin Mateo Gómez Díez, Jhon Freddy Asprilla, Tomás Mercado Ramos y Mario Andrade.

\# Taller Inspección - Reglas del Proyecto



\## Objetivo



Desarrollar una plataforma SaaS profesional para talleres mecánicos especializada en inspecciones precompra de vehículos.



Todo el código debe ser de calidad producción.



Nunca generar código temporal.



Nunca generar ejemplos simplificados.



\---



\# Arquitectura



Seguir estrictamente:



\- Clean Architecture

\- SOLID

\- Domain Driven Design (DDD)

\- Repository Pattern

\- Feature First

\- Dependency Injection

\- Separation of Concerns



Nunca mezclar capas.



\---



\# Stack



Frontend



\- Flutter 3

\- Material 3

\- Riverpod

\- GoRouter

\- Freezed

\- Json Serializable



Backend



\- Python 3.12

\- FastAPI

\- Firebase Admin SDK

\- Firestore Native



Base de datos



\- Firebase Firestore



Autenticación



\- Firebase Authentication

\- JWT

\- Refresh Token



\---



\# Calidad del código



Siempre escribir código limpio.



No duplicar lógica.



Crear componentes reutilizables.



Crear servicios reutilizables.



Todo debe ser tipado.



No escribir funciones enormes.



Preferir funciones pequeñas.



No crear clases gigantes.



Aplicar SOLID.



\---



\# Organización



Mantener siempre esta estructura.



apps/



backend/



packages/



docs/



scripts/



infra/



Nunca modificar la estructura sin justificarlo.



\---



\# Flutter



Usar Riverpod.



Usar GoRouter.



Widgets pequeños.



Evitar lógica dentro de Widgets.



Usar Providers únicamente para estado.



No usar setState salvo casos excepcionales.



\---



\# Backend



FastAPI.



Endpoints REST.



Versionados.



api/v1



Preparar api/v2.



Siempre documentar con OpenAPI.



\---



\# Firestore



Toda colección debe incluir



tenantId



createdAt



updatedAt



createdBy



updatedBy



Nunca eliminar registros críticos.



Usar Soft Delete cuando corresponda.



\---



\# Seguridad



Nunca confiar en validaciones del frontend.



Validar todo en backend.



Implementar:



\- JWT

\- Refresh Tokens

\- Rate Limit

\- Firestore Rules

\- HTTPS

\- CORS



\---



\# Testing



Antes de finalizar cualquier tarea:



\- ejecutar lint

\- verificar compilación

\- actualizar tests afectados



Mantener cobertura mínima del 80%.



\---



\# Documentación



Cada cambio importante debe actualizar:



README.md



docs/



Diagramas Mermaid



Arquitectura



No dejar documentación desactualizada.



\---



\# Tamaño de archivos



Evitar archivos enormes.



Objetivo:



\- máximo 300 líneas por archivo



Máximo absoluto:



500 líneas.



Si un archivo supera ese tamaño debe dividirse.



\---



\# Commits



Al finalizar una tarea importante proponer un mensaje usando Conventional Commits.



Ejemplo



feat(inspections): add inspection workflow



fix(auth): refresh token expiration



refactor(vehicle): extract repository



\---



\# Antes de escribir código



Siempre:



1\. Analizar el problema.



2\. Buscar la solución más simple.



3\. Pensar en escalabilidad.



4\. Pensar en mantenibilidad.



5\. Pensar en rendimiento.



6\. Pensar en seguridad.



7\. Explicar brevemente las decisiones técnicas.



\---



\# Nunca



Nunca eliminar funcionalidades existentes.



Nunca romper compatibilidad.



Nunca duplicar código.



Nunca mezclar responsabilidades.



Nunca crear deuda técnica intencionalmente.



Nunca generar código sin explicar dónde debe ubicarse.



\---



\# Preferencias



Priorizar:



legibilidad



mantenibilidad



escalabilidad



seguridad



performance



sobre escribir menos código.



\---

\# Optimización de contexto

Para ahorrar contexto y tokens:

- No resumas documentación ya conocida.
- No expliques nuevamente la arquitectura salvo que cambie.
- No listes archivos sin que se solicite.
- No repitas código existente.
- Responde de forma breve cuando no se requiera una explicación extensa.
- Lee únicamente los archivos necesarios para la tarea actual.
- Reutiliza componentes existentes antes de crear nuevos.
\---


\# Objetivo final



Construir una plataforma SaaS profesional lista para producción y preparada para miles de talleres utilizando Flutter, FastAPI y Firebase.

---

# Modo de Trabajo



Este proyecto es grande y debe desarrollarse por fases.



Nunca intentes implementar todo el sistema en una sola respuesta.



Siempre mantén el proyecto compilable.



Antes de comenzar una nueva fase:



\- Lee README.md

\- Lee docs/ROADMAP.md

\- Lee docs/ARCHITECTURE.md

\- Lee docs/TASKS.md

\- Revisa el estado del proyecto.



Al finalizar cada fase debes:



\- Actualizar README.md

\- Actualizar docs/TASKS.md

\- Actualizar docs/ROADMAP.md

\- Actualizar la documentación técnica relacionada.

\- Proponer un commit usando Conventional Commits.

\- Indicar claramente cuál es la siguiente fase.



Si una tarea es demasiado grande:



Divídela automáticamente en subtareas pequeñas.



Nunca avances a la siguiente fase sin terminar completamente la anterior.



Si el contexto de la conversación comienza a agotarse:



Resume el estado del proyecto en docs/HANDOFF.md para poder continuar exactamente donde quedó en la siguiente conversación.



Siempre prioriza:



1\. Arquitectura

2\. Seguridad

3\. Escalabilidad

4\. Legibilidad

5\. Mantenibilidad

6\. Rendimiento



Nunca sacrifiques arquitectura por velocidad.


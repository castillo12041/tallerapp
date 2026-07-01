Actúa como un Arquitecto de Software Principal (Principal Software Architect), Tech Lead y Senior Full Stack Engineer con más de 20 años de experiencia desarrollando plataformas SaaS empresariales.

Tu objetivo NO es crear un MVP.

Tu objetivo es diseñar y desarrollar una plataforma SaaS comercial, preparada para producción, escalable y mantenible durante muchos años.

La calidad del código debe ser equivalente a un producto comercial.

No simplifiques ninguna parte de la arquitectura.

Siempre sigue las mejores prácticas actuales.

==================================================
OBJETIVO DEL PROYECTO
==================================================

Desarrollar una plataforma SaaS Multi-Tenant de gestión para talleres mecánicos especializada en inspecciones precompra de vehículos.

El producto debe estar preparado para comercializarse como servicio SaaS.

Debe soportar desde pequeños talleres hasta cientos o miles de talleres trabajando simultáneamente.

Debe estar preparado para crecer durante muchos años.

No desarrollar código temporal.

No desarrollar ejemplos.

Todo el código debe ser producción.

==================================================
DOMINIO
==================================================

https://tallerinspeccion.tapsolutions.cl

Rutas

/

Aplicación principal

/admin

Panel Super Administrador

/app

Panel del Taller

/cliente

Portal Cliente

/informe/{id}

/presupuesto/{id}

==================================================
STACK TECNOLÓGICO
==================================================

Frontend

Flutter 3.x

Material Design 3

Riverpod

GoRouter

Freezed

Json Serializable

Responsive

Android

iOS

Flutter Web

Backend

Python 3.12

FastAPI

Pydantic v2

Firebase Admin SDK

Firestore Native

JWT

Refresh Tokens

Background Tasks

WebSockets preparados

Base de datos

Firebase Firestore

Firebase Authentication

Firebase Storage

Firebase Hosting

Firebase Cloud Messaging

Crashlytics

Analytics

Performance Monitoring

Correo

SMTP

SendGrid

WhatsApp

Twilio

WhatsApp Business API

PDF

ReportLab

WeasyPrint

QR

qrcode

==================================================
ARQUITECTURA
==================================================

Implementar estrictamente

Clean Architecture

SOLID

DDD

Repository Pattern

CQRS preparado

Dependency Injection

Feature First

Vertical Slice

Separation of Concerns

No mezclar lógica.

==================================================
ESTRUCTURA
==================================================

apps/

mobile

web_admin

web_client

backend/

api

workers

notifications

pdf_service

integrations

packages/

shared_models

shared_widgets

shared_theme

shared_utils

domain/

application/

infrastructure/

presentation/

shared/

==================================================
MULTITENANT
==================================================

Cada taller es un Tenant.

Toda la información debe contener

tenantId

Debe existir middleware obligatorio.

Nunca permitir consultas cruzadas.

Todos los índices deben considerar tenantId.

Todas las reglas Firestore deben considerar tenantId.

==================================================
ROLES
==================================================

SuperAdmin

TenantAdmin

WorkshopManager

Inspector

Mechanic

Receptionist

Customer

Crear sistema RBAC completo.

No depender únicamente del rol.

Crear permisos independientes.

==================================================
PLANES SaaS
==================================================

Basic

Professional

Premium

Enterprise

Cada plan debe tener restricciones automáticas.

Ejemplos

usuarios

almacenamiento

inspecciones

portal cliente

API

dominio personalizado

branding

WhatsApp

Dashboard

Middleware obligatorio.

==================================================
MÓDULOS
==================================================

Autenticación

Usuarios

Roles

Permisos

Configuración

Clientes

Vehículos

API Patentes

Inspecciones

Checklists

Fotos

Audio

Firmas

PDF

QR

Portal Cliente

Presupuestos

Órdenes de Trabajo

Agenda

Dashboard

CRM

Historial Vehículo

Notificaciones

Correos

WhatsApp

Auditoría

Logs

Suscripciones

Facturación

API Pública

Webhooks

Configuración

Centro de Ayuda

==================================================
INSPECCIÓN PRECOMPRA
==================================================

Debe soportar

Más de 150 puntos.

Cada punto

Categoría

Estado

Comentario

Múltiples fotografías

Audio

Observaciones

Valor reparación

==================================================
ESTADOS
==================================================

Bueno

Regular

Malo

No aplica

==================================================
SECCIONES
==================================================

Exterior

Interior

Motor

Transmisión

Caja

Suspensión

Dirección

Frenos

Llantas

Neumáticos

Eléctrico

Electrónica

Chasis

Documentación

Prueba Ruta

==================================================
FOTOS
==================================================

Compresión automática.

Subida paralela.

Edición.

Anotaciones.

Zoom.

Timestamp.

GPS opcional.

Offline.

==================================================
OFFLINE FIRST
==================================================

Toda inspección debe funcionar sin internet.

Cache local.

Sincronización automática.

Resolver conflictos.

==================================================
PDF
==================================================

Diseño profesional.

Logo.

Colores.

Firmas.

Fotos.

Checklist.

Valor reparación.

Código QR.

Pie personalizado.

Texto legal.

==================================================
QR
==================================================

Cada QR debe validar

Hash

Firma

Estado

Fecha

No utilizar únicamente el ID.

==================================================
TOKEN PÚBLICO
==================================================

Nunca utilizar URLs públicas únicamente con ID.

Utilizar tokens firmados.

Ejemplo

/informe/{id}?token=...

o

/r/{token}

==================================================
CLIENTES
==================================================

Portal independiente.

Puede

Descargar PDFs

Aceptar presupuestos

Rechazar presupuestos

Ver historial

Actualizar datos

==================================================
WORKFLOW
==================================================

Inspector

↓

Revisión

↓

Aprobación

↓

PDF

↓

Correo

↓

WhatsApp

↓

Cliente

==================================================
NOTIFICACIONES
==================================================

Email

Push

WhatsApp

Automáticas.

==================================================
AUDITORÍA
==================================================

Registrar absolutamente todo.

Nunca eliminar registros.

Guardar

usuario

rol

fecha

hora

IP

tenant

colección

documento

valor anterior

valor nuevo

==================================================
API
==================================================

Documentar completamente mediante Swagger.

Versionar

/api/v1

Preparar

/api/v2

==================================================
SEGURIDAD
==================================================

HTTPS obligatorio.

JWT.

Refresh Tokens.

Rate Limit.

CORS.

Firestore Rules.

Validaciones Backend.

Validaciones Frontend.

bcrypt o Argon2.

Protección XSS.

Protección CSRF.

Headers de seguridad.

==================================================
FIRESTORE
==================================================

Diseñar completamente.

Colecciones

tenants

plans

subscriptions

users

roles

permissions

clients

vehicles

vehicle_history

inspections

inspection_templates

inspection_items

inspection_photos

inspection_audio

inspection_signatures

estimates

estimate_items

work_orders

work_order_items

calendar

notifications

audit_logs

settings

storage_files

emails

whatsapp_messages

public_tokens

api_keys

webhooks

reports

analytics

logs

==================================================
DASHBOARD
==================================================

Métricas.

Gráficos.

KPIs.

Productividad.

Ingresos.

Uso Firestore.

Uso Storage.

Usuarios activos.

==================================================
BRANDING
==================================================

Cada taller puede personalizar

Logo

Favicon

Colores

Nombre

Plantillas

Correos

PDF

Portal

Subdominio

Ejemplo

tallerabc.tallerinspeccion.tapsolutions.cl

==================================================
PWA
==================================================

Instalable.

Modo offline.

Push.

Sincronización.

==================================================
API PATENTES
==================================================

Preparar integración.

Ejemplo

GET

https://api.boostr.cl/vehicle/fake/{PATENTE}.json

Autocompletar vehículo.

==================================================
IA
==================================================

Preparar arquitectura para IA.

No implementar aún.

Debe permitir posteriormente

Detección de daños

Resumen automático

Observaciones

Clasificación fotografías

Estimación costos

==================================================
CALIDAD
==================================================

No duplicar código.

Crear componentes reutilizables.

Crear servicios reutilizables.

Tipado completo.

Comentarios únicamente cuando agreguen valor.

Código limpio.

No generar archivos gigantes.

Dividir responsabilidades.

==================================================
TESTING
==================================================

Unit Tests.

Widget Tests.

Integration Tests.

Backend Tests.

==================================================
CI/CD
==================================================

Preparar

GitHub Actions

Lint

Tests

Build Android

Build iOS

Deploy Firebase Hosting

Deploy FastAPI

==================================================
DOCUMENTACIÓN
==================================================

Generar automáticamente

README

Arquitectura

Diagramas Mermaid

OpenAPI

Colecciones Firestore

Reglas Firestore

Variables de entorno

Manual instalación

Manual despliegue

Manual desarrollador

==================================================
FORMA DE TRABAJO
==================================================

NO intentes generar todo el proyecto en una sola respuesta.

Trabaja como un arquitecto de software profesional.

Antes de escribir código:

1. Analiza todos los requisitos.
2. Detecta posibles problemas de arquitectura.
3. Propón mejoras justificadas.
4. Diseña la arquitectura completa.
5. Diseña Firestore.
6. Diseña las APIs.
7. Diseña los diagramas.
8. Diseña los casos de uso.
9. Diseña el modelo de dominio.
10. Diseña la seguridad.
11. Diseña la estructura de carpetas.
12. Diseña el flujo de autenticación.
13. Diseña la sincronización offline.
14. Diseña el sistema de permisos.
15. Diseña el sistema de branding.
16. Diseña el sistema de suscripciones.

Una vez aprobada la arquitectura, desarrolla el proyecto por fases.

==================================================
FASES OBLIGATORIAS
==================================================

Fase 1
Arquitectura completa.

Fase 2
Modelo Firestore.

Fase 3
Backend FastAPI.

Fase 4
Autenticación.

Fase 5
Flutter Base.

Fase 6
Panel Administrador.

Fase 7
Portal Cliente.

Fase 8
Inspecciones.

Fase 9
PDF.

Fase 10
QR.

Fase 11
Presupuestos.

Fase 12
Órdenes.

Fase 13
Agenda.

Fase 14
Dashboard.

Fase 15
Notificaciones.

Fase 16
Auditoría.

Fase 17
PWA.

Fase 18
Testing.

Fase 19
CI/CD.

Fase 20
Optimización final.

En cada fase:

- Explica las decisiones técnicas.
- Genera únicamente los archivos necesarios.
- Mantén el proyecto compilable en todo momento.
- Verifica que no existan regresiones.
- Actualiza la documentación automáticamente.
- Nunca rompas la arquitectura definida.
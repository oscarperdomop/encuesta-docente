# Changelog
Todas las novedades relevantes de este proyecto se documentan aquí.

Este archivo sigue el formato de [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
y el versionado [SemVer](https://semver.org/lang/es/).

## [Unreleased]
### Added
- (Reserva esta sección para lo que esté en desarrollo y aún no liberado)

---

## [1.0.0] - 2025-09-19
### Added
- **PRD v1.0.0 (congelado)**: alcance, UX/flows, H1–H10 con criterios de aceptación, requisitos funcionales/no funcionales.
- **Modelo de datos (alto nivel)**: entidades, relaciones, índice parcial para envío único por docente.
- **API (resumen)**: auth/login, queue/summary, attempts (crear/autosave/submit), admin (pesos, roles, +1 intento, asignaciones), export/reportes.
- **PWA**: alcance offline (assets) y **autosave local** sin botón visible.
- **Panel Admin**: edición de pesos, roles (elevación a admin), intentos extra, asignación de docentes (catálogo global).
- **Reportes/Export**: CSV/Excel con Q1..Q15, Q16(3), scores por sección y total; dashboard con media, desviación, histograma 1–5.
- **Resumen y cierre de turno**: pantalla de resumen y botón **Finalizar turno** (si todos enviados).

### Changed
- **Login**: se adopta **acceso directo por email** presente en BD y dominio `@usco.edu.co` (**sin OTP/2FA**).
- **Iteración por docente**: modelo de **cola**; al enviar se avanza al siguiente y se bloquea reenvío.

### Removed
- Requerimiento de magic link/OTP para autenticación (reemplazado por acceso directo por email).

### Security
- Restricción de dominio `@usco.edu.co` + verificación de existencia en BD.
- Sesiones **JWT** de corta duración, **rate limiting**, **audit logs** (IP/UA), CORS/CSP estrictas y HTTPS.



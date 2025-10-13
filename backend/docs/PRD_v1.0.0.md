PRD v1.0.0 — Proyecto Encuesta Docente (USCO)
Fecha: 2025-09-19
Estado: CONGELADO (versión 1.0.0)
Stakeholders: Facultad de Educación USCO, Coordinación del programa, Equipo de TI.
Producto: PWA (Progressive Web App) para evaluación docente.
________________________________________
1. Resumen ejecutivo
PWA ligera para evaluar docentes con 4 perfiles (Estudiante, Docente, Jefe de programa, Administrador). Login directo por correo @usco.edu.co existente en BD (sin OTP). El encuestador selecciona uno o varios docentes y responde una encuesta de 16 preguntas (Q1–Q15 escala 1–5; Q16 texto opcional con 3 campos). Flujo en dos pasos, validación estricta, cola por docente, timer de 30 min por intento y bloqueo ≥2 intentos fallidos, con capacidad del Admin de otorgar +1 intento. Panel Admin: pesos por pregunta, reportes (media, desviación, histograma), export CSV/Excel y gestión de roles.
KPI clave: tasa de finalización de turno ≥ 85%, tiempo medio de carga < 2 s, errores de validación < 1% por sesión, export funcional 100%.
________________________________________
2. Alcance
2.1 In scope
•	Gestión de usuarios (importación CSV; validación de dominio y existencia en BD; roles).

•	Login por email sin OTP (sesión JWT corta).

•	Selección de docentes (grid 2 columnas, buscador, cola).

•	Encuesta de 16 ítems en 2 pasos; validación (1–5) y Q16 texto.

•	Control de intentos (2 fallidos ⇒ bloqueo; Admin puede +1).

•	Resumen de turno y Finalizar turno (cierre de sesión).

•	Panel Admin: pesos, asignación de docentes (catálogo global; permisos finos opcionales), roles, intentos extra.

•	Export CSV/Excel; dashboard con KPIs (media, desviación, histograma 1–5).

•	PWA con autosave local (sin botón visible) y SW para assets.
2.2 Out of scope (v1)
•	SSO institucional; anonimato legal avanzado; editor libre de formularios; multilenguaje (ES únicamente).
________________________________________
3. Perfiles y permisos
•	Estudiante / Docente / Jefe de programa: solo encuestar.

•	Administrador: todos los permisos (encuestas, pesos, docentes, usuarios, roles, intentos extra, reportes, export). Puede encuestar.

•	Identidad visible del encuestador al Admin (para analítica).

•	Permisos finos: Admin puede elevar usuarios a Administrador.
________________________________________
4. Historias de usuario (H1–H10) y Criterios de Aceptación
H1 Auth: login por email @usco.edu.co existente/activo → sesión JWT; error si no autorizado; header con nombre/rol.
H2 Presentación/Justificación: dos pantallas secuenciales con botón Continuar.
H3 Selección: grid 2 columnas + buscador; botón Iniciar con ≥1 seleccionado; al agregar docentes desde la lista se encolan al final; header muestra intentos.
H4 Encuesta en pasos: Paso 1 (Q1–Q9), Paso 2 (Q10–Q15 + Q16 texto opc.); Siguiente/Enviar solo si 1–5 completos; Regresar (docente anterior / lista).
H5 Confirmación: modal “¿Desea terminar la encuesta?” Sí/No; Sí → registra y bloquea docente; avanza en la cola.
H6 Intentos/Timeout: 30 min por intento; expira consume 1; ≥2 fallidos ⇒ bloqueo; Admin puede +1.
H7 Pesos: Admin edita peso por pregunta (default 1) con validación.
H8 Reportes/Export: export CSV/Excel con Q1..Q15, Q16(3), scores por sección/total; dashboard con media, desviación e histograma 1–5 (filtros).
H9 Roles: Admin asigna/retira rol admin (efecto inmediato).
H10 Finalizar turno: pantalla Resumen; Finalizar solo si todos Enviado; backend revalida, registra audit y cierra sesión.
Detalle de CA (Given/When/Then): ver Anexo A al final (copiable a issues).
________________________________________
5. UX / Flujo
1)	Login → 2) Presentación → 3) Justificación → 4) Selección de docentes (grid 2 col, header con usuario + intentos) → 5) Encuesta Paso 1 (Q1–Q9, timer 30:00) → 6) Paso 2 (Q10–Q15 + Q16) → 7) Confirmación envío → 8) Siguiente docente (cola) → 9) Resumen de turno → 10) Finalizar turno (si todos Enviado) → Despedida.
Componentes clave: header fijo con temporizador y intentos; botón Regresar (menú contextual); toasts de éxito/error.
________________________________________
6. Requisitos funcionales
6.1 Autenticación
•	POST /auth/login { email } concede sesión si email ∈ BD y termina en @usco.edu.co; JWT corto con expiración por inactividad.

•	GET /auth/me, POST /auth/logout.
6.2 Selección y cola
•	Listado filtrable de docentes (catálogo por encuesta).

•	Crear cola al iniciar; nuevos docentes añadidos desde “lista” → al final de la cola.

•	Elegibilidad: solo docentes seleccionados por el usuario (y en catálogo de la encuesta).
6.3 Encuesta
•	Q1–Q15: select {Seleccionar,1,2,3,4,5} (no avanza si hay “Seleccionar”).

•	Q16: 3 textareas (positivos, a mejorar, comentarios) opcionales.

•	Validaciones server-side y cliente.
6.4 Intentos y timeout
•	Intentos por usuario x encuesta: máx. 2 fallidos (expirado/fallido) → bloqueo; Admin +1.

•	Por docente: 1 envío inmutable.

•	Temporizador 30:00 visible; alerta a 5:00.
6.5 Resumen y cierre
•	Resumen con estados (Enviado/Pendiente/En progreso).

•	Finalizar turno habilitado solo si todos Enviado; back valida y cierra sesión.
6.6 Admin
•	Pesos por pregunta; asignación de docentes (global; opcional permisos finos por usuario); roles; intentos extra.

•	Export CSV/Excel; reportes con media, desviación, histograma (filtros por periodo/programa/rol).
________________________________________
7. Requisitos no funcionales
•	Performance: TTI < 2 s (3G), API p95 lectura < 300 ms.

•	Disponibilidad: ≥ 99.5% durante aplicación.

•	Accesibilidad: WCAG 2.1 AA; idioma ES.

•	Compatibilidad: Chrome/Edge/Firefox/Safari recientes; Android/iOS modernos.

•	PWA: SW para assets; autosave local; envío requiere conexión.

•	Observabilidad: logs estructurados, métricas básicas, uptime.
________________________________________
8. Seguridad y cumplimiento
•	Dominio y existencia en BD obligatoria; normalización de email (minúsculas).

•	JWT de corta duración; rate limiting; re-auth para acciones admin sensibles.

•	Audit logs: user_id, acción, IP, UA.

•	HTTPS, CORS y CSP estrictas; cifrado en reposo.
________________________________________
9. Modelo de datos (alto nivel)
•	users (UUID, email UNIQUE CITEXT, nombre, estado, timestamps)

•	roles / user_roles

•	teachers

•	periods

•	surveys / survey_sections / questions(peso)

•	survey_teacher_assignments (catálogo por encuesta)

•	user_teacher_permissions (opcional)

•	attempts (user, survey, teacher, intento_nro, estado, expires_at, progreso_json)

•	responses (attempt, question, valor_likert 1–5, texto JSONB para Q16)

•	attempt_limits (max=2, extra_otorgados)

•	audit_logs
Constraints/índices clave:
- UNIQUE responses (attempt_id, question_id);
- Índice parcial para un único envío por docente: UNIQUE (user_id, survey_id, teacher_id) WHERE estado='enviado'.
________________________________________
10. API (resumen)
Auth/Sesión: POST /auth/login, GET /auth/me, POST /auth/logout, POST /sessions/close
Cola/Resumen: GET /queue?survey_id=, GET /attempts/summary?survey_id=
Catálogos: GET /surveys/activas, GET /surveys/{id}/teachers, GET /surveys/{id}/questions
Intentos/Respuestas: POST /attempts, PATCH /attempts/{id}, POST /attempts/{id}/responses, POST /attempts/{id}/submit
Admin: POST /surveys, PUT /surveys/{id}/questions/{qid}, POST /surveys/{id}/teachers/assign, POST /permissions/user-teachers, POST /roles/grant, POST /attempts/extra, GET /reports/overview, GET /exports/respuestas.csv
________________________________________
11. Lógica de intentos (máquina de estados)
•	en_progreso → enviado (si Q1–Q15 válidas)

•	en_progreso → expirado (timeout 30 min)

•	en_progreso → fallido (abandono/cierre)

•	Bloqueo: (expirado + fallido) ≥ 2 sin ningún enviado en la encuesta → bloquear; Admin puede +1.
________________________________________
12. Reportes y exportación
•	Export: CSV/Excel con survey, periodo, docente, rol, fecha, Q1..Q15, Q16(3), score sección, score total.

•	Dashboard: media, desviación, histograma por docente y pregunta; filtros por periodo/programa/rol; KPIs de envío y finalización.
________________________________________
13. Plan de entrega (Roadmap v1)
1)	Modelo de datos + migraciones + seed (16 preguntas peso=1).

2)	Auth + catálogos.

3)	Intentos/Timeout + Encuesta en pasos + Cola.

4)	Resumen/Finalizar turno.

5)	Admin: Pesos, Intentos extra, Roles, Asignaciones.

6)	Export + Reportes (básico).

7)	QA, hardening, despliegue.
________________________________________
14. Aceptación y éxito
•	Criterios de aceptación: cumplimiento de CA H1–H10; export sin errores; bloqueo ≥2 fallidos probado; “Finalizar turno” habilitado solo con todos Enviado; KPIs mínimos alcanzados.

•	Go/No-Go: demo funcional en staging superada y checklist de despliegue completo.
________________________________________
Anexo A — Criterios Given/When/Then (resumen copiable)
•	H1: Dado email en BD → Cuando Entrar → Entonces sesión; Dado email no válido → error; header con nombre/rol.

•	H2: Dado Presentación → Cuando Continuar → Entonces Justificación; Dado Justificación → Continuar → Selección.

•	H3: Dado Selección → Cuando marco ≥1 → Entonces Iniciar habilitado; Dado regreso → agrego docente → se encola; header muestra intentos.

•	H4: Dado Paso 1 → Si hay “Seleccionar” → Siguiente inactivo; Dado Paso 2 → Q10–Q15 en 1–5 → Enviar activo; Regresar abre menú.

•	H5: Dado Enviar → Modal Sí/No; Sí → bloquea docente y avanza; No → permanece.

•	H6: Dado intento activo → 30 min → expira y consume; Dado ≥2 fallidos → bloqueo; Dado +1 admin → contador actualizado.

•	H7: Dado editor de pesos → cambio y guardo → persiste; afecta scores siguientes.

•	H8: Dado export → descarga CSV/Excel con campos; Dado dashboard → filtros → media, desviación, histograma.

•	H9: Dado Roles → asigno/quito admin → permisos cambian.

•	H10: Dado cola completa → todos Enviado → aparece Finalizar; al pulsar → valida, audita y cierra sesión.



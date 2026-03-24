# Zero Risk Runbook (Producción)

Objetivo: aplicar saneamiento sin cambios destructivos ni conversiones de tipo en caliente.

## 1) Preflight (solo lectura)

Desde `backend/api`:

```bash
python scripts/db_preflight_zero_risk.py
```

Resultado esperado:
- Exit code `0` si no hay críticos.
- JSON con `findings` (`warn`/`critical`) y versión(es) de alembic detectadas.

## 2) Migración aditiva e idempotente

Migración incluida: `0007_zero_risk_compat_layer`.

Qué hace:
- Crea `turnos` si no existe.
- Agrega columnas de compatibilidad si faltan:
  - `attempts.creado_en`, `attempts.actualizado_en`
  - `responses.created_at`
  - `attempt_limits.max_intentos`, `attempt_limits.extra_otorgados`
  - `audit_logs.user_id`, `audit_logs.accion`, `audit_logs.actor_user_id`, `audit_logs.action`, `audit_logs.creado_en`
- No elimina columnas ni convierte tipos existentes.

Aplicación:

```bash
alembic upgrade 0007_zero_risk_compat_layer
```

### Caso especial: `alembic_version` ausente

Si el preflight muestra advertencia de `alembic_version` ausente/no legible:

1. **No ejecutar `upgrade` directo** (evita re-ejecutar historial completo).
2. Validar preflight sin críticos.
3. Registrar estado actual con `stamp` en la revisión de corte:

```bash
alembic stamp 0006_add_audit_logs
```

4. Aplicar solo capa aditiva:

```bash
alembic upgrade 0007_zero_risk_compat_layer
```

## 3) Smoke checks post-migración

1. `GET /health`
2. `GET /api/v1/health/db`
3. Login de usuario normal (`/api/v1/auth/login`)
4. Endpoint admin protegido (`/api/v1/admin/reports/stats/overview`)
5. Flujo corto de turnos:
   - `POST /api/v1/sessions/turno/open`
   - `GET /api/v1/sessions/turno/current`

## 4) Criterios de rollback seguro

La `0007` tiene downgrade no destructivo (no-op) para evitar drops automáticos en producción.
Si hay incidente:
- pausar tráfico,
- restaurar desde snapshot/backup de la BD,
- revisar findings del preflight y logs de app.

## 5) Pendientes fuera de “cero riesgo”

Estos temas requieren proyecto aparte (no incluidos aquí por riesgo):
- normalización de tipos UUID/Integer en modelos legacy,
- reconciliación completa de `audit_logs` a un solo contrato canónico,
- estrategia de migración para constraints NOT NULL/UNIQUE con validación previa de datos.

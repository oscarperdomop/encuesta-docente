#!/usr/bin/env python3
import os, csv, uuid
import psycopg2
from collections import defaultdict

DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://encuesta:encuesta@localhost:5432/encuesta")

def read_csv(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        print(f"[WARN] No encontrado: {path}")
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def main():
    print("[INFO] DATA_DIR:", DATA_DIR)
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Roles
    for i, r in enumerate(['admin','enc_estudiante','enc_docente','enc_jefe_programa'], start=1):
        cur.execute("INSERT INTO roles (id,nombre) VALUES (%s,%s) ON CONFLICT (id) DO NOTHING;", (i, r))

    # Users
    for u in read_csv('usuarios_import.csv'):
        cur.execute("""
            INSERT INTO users (email, nombre, estado)
            VALUES (lower(%s), %s, 'activo')
            ON CONFLICT (email) DO NOTHING;
        """, (u.get('email'), u.get('nombre')))
        # role
        cur.execute("SELECT id FROM users WHERE email=lower(%s);", (u.get('email'),))
        row = cur.fetchone()
        if not row: continue
        user_id = row[0]
        cur.execute("SELECT id FROM roles WHERE nombre=%s;", (u.get('rol','enc_estudiante'),))
        role_id = cur.fetchone()[0]
        cur.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s,%s) ON CONFLICT DO NOTHING;", (user_id, role_id))

    # Periods
    for p in read_csv('periodos.csv'):
        cur.execute("INSERT INTO periods (nombre, anyo, semestre) VALUES (%s, %s, %s) ON CONFLICT (nombre) DO NOTHING;", (p['nombre'], int(p['anyo']), int(p['semestre'])))

    # Teachers
    for t in read_csv('docentes_import.csv'):
        cur.execute("""
            INSERT INTO teachers (identificador, nombre, programa, estado)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (identificador) DO NOTHING;
        """, (t['identificador'], t['nombre'], t.get('programa'), t.get('estado','activo')))

    # Surveys
    for s in read_csv('encuestas.csv'):
        cur.execute("SELECT id FROM periods WHERE nombre=%s;", (s['periodo_nombre'],))
        per = cur.fetchone()
        if not per:
            continue
        cur.execute("""
            INSERT INTO surveys (codigo, nombre, periodo_id, estado, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (codigo) DO NOTHING;
        """, (s['codigo'], s['nombre'], per[0], s.get('estado','activa'), s.get('fecha_inicio') or None, s.get('fecha_fin') or None))

    # Sections + Questions
    preguntas = read_csv('preguntas_import.csv')
    if preguntas:
        # survey id
        cur.execute("SELECT id FROM surveys WHERE codigo=%s;", (preguntas[0]['survey_codigo'],))
        srow = cur.fetchone()
        if srow:
            survey_id = srow[0]
            # group by section preserving order
            seen_sections = []
            section_ids = {}
            for r in preguntas:
                sec = r['section']
                if sec not in seen_sections:
                    seen_sections.append(sec)
                    cur.execute("INSERT INTO survey_sections (survey_id, titulo, orden) VALUES (%s,%s,%s) RETURNING id;", (survey_id, sec, len(seen_sections)))
                    section_ids[sec] = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO questions (survey_id, section_id, codigo, enunciado, orden, tipo, peso)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (survey_id, section_ids[sec], r['question_codigo'], r['enunciado'], int(r['orden']), r['tipo'], 1))

    # Pesos
    for w in read_csv('pesos_preguntas.csv'):
        cur.execute("""
            UPDATE questions q SET peso=%s
            FROM surveys s
            WHERE q.survey_id=s.id AND s.codigo=%s AND q.codigo=%s;
        """, (w['peso'], w['survey_codigo'], w['question_codigo']))

    # Assignments
    for a in read_csv('asignacion_docentes.csv'):
        cur.execute("SELECT id FROM surveys WHERE codigo=%s;", (a['survey_codigo'],))
        s = cur.fetchone()
        cur.execute("SELECT id FROM teachers WHERE identificador=%s;", (a['teacher_identificador'],))
        t = cur.fetchone()
        if s and t:
            cur.execute("INSERT INTO survey_teacher_assignments (survey_id, teacher_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (s[0], t[0]))

    conn.commit()
    cur.close(); conn.close()
    print('[OK] Importación finalizada')

if __name__ == '__main__':
    main()

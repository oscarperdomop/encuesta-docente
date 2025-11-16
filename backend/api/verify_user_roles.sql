-- Script para verificar y corregir roles de usuario admin
-- Ejecutar en la base de datos PostgreSQL

-- 1. Verificar que exista el rol 'admin'
SELECT * FROM roles WHERE nombre IN ('admin', 'Admin', 'Administrador');

-- 2. Verificar el usuario admin2@usco.edu.co
SELECT id, email, nombre, estado FROM users WHERE email = 'admin2@usco.edu.co';

-- 3. Ver los roles asignados al usuario
SELECT 
    u.email,
    u.nombre,
    r.nombre AS rol
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON r.id = ur.role_id
WHERE u.email = 'admin2@usco.edu.co';

-- 4. Si el usuario existe pero no tiene rol admin, ejecutar estos comandos:
-- (Descomentar y ejecutar solo si es necesario)

-- Primero, asegurarse de que existe el rol 'admin'
-- INSERT INTO roles (nombre) VALUES ('admin') ON CONFLICT (nombre) DO NOTHING;

-- Luego, asignar el rol al usuario
-- INSERT INTO user_roles (user_id, role_id)
-- SELECT 
--     u.id,
--     r.id
-- FROM users u, roles r
-- WHERE u.email = 'admin2@usco.edu.co'
--   AND r.nombre = 'admin'
-- ON CONFLICT DO NOTHING;

-- 5. Verificar después de asignar
-- SELECT 
--     u.email,
--     u.nombre,
--     r.nombre AS rol
-- FROM users u
-- JOIN user_roles ur ON ur.user_id = u.id
-- JOIN roles r ON r.id = ur.role_id
-- WHERE u.email = 'admin2@usco.edu.co';

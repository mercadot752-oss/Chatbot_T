-- Perfiles y datos académicos sintéticos para las pruebas locales del chatbot.
-- Los seis perfiles de usuarios conservan sus IDs y roles actuales.
INSERT INTO usuarios (id, nombre, apellidos, rol, tipo_id)
VALUES
  (999000001, 'Usuario', 'Prueba General', 'usuario', 'TEST'),
  (999000002, 'Profesor', 'Prueba Academica', 'profesor', 'TEST'),
  (999000003, 'Valentina', 'Demo Consulta', 'usuario', 'TEST'),
  (999000004, 'Mateo', 'Usuario Muestra', 'usuario', 'TEST'),
  (999000005, 'Laura', 'Profesora Demo', 'profesor', 'TEST'),
  (999000006, 'Andres', 'Docente Muestra', 'profesor', 'TEST')
ON CONFLICT (id) DO UPDATE SET
  nombre = EXCLUDED.nombre,
  apellidos = EXCLUDED.apellidos,
  rol = EXCLUDED.rol,
  tipo_id = EXCLUDED.tipo_id;

-- Estudiantes de demostración separados de los perfiles genéricos y docentes.
INSERT INTO estudiante (id, nombre, apellidos, tipo_id)
VALUES
  (999000007, 'Camila', 'Estudiante Demo', 'TEST'),
  (999000008, 'Santiago', 'Estudiante Demo', 'TEST'),
  (999000009, 'Isabella', 'Estudiante Demo', 'TEST')
ON CONFLICT (id) DO UPDATE SET
  nombre = EXCLUDED.nombre,
  apellidos = EXCLUDED.apellidos,
  tipo_id = EXCLUDED.tipo_id;

-- Catálogo académico ficticio para probar consultas y priorización por créditos.
INSERT INTO materias (id_materia, nombre_materia, creditos)
VALUES
  (9101, 'Fundamentos de Programación', 4),
  (9102, 'Bases de Datos', 4),
  (9103, 'Redes y Conectividad', 3),
  (9104, 'Soporte de Sistemas Institucionales', 2),
  (9105, 'Seguridad Informática', 3),
  (9106, 'Análisis y Diseño de Sistemas', 4)
ON CONFLICT (id_materia) DO UPDATE SET
  nombre_materia = EXCLUDED.nombre_materia,
  creditos = EXCLUDED.creditos;

-- Matrículas variadas. La condición evita duplicados al volver a ejecutar el script.
INSERT INTO estudiante_materias (id_estudiante, id_materia)
SELECT datos.id_estudiante, datos.id_materia
FROM (VALUES
  (999000007, 9101), (999000007, 9102), (999000007, 9103),
  (999000008, 9102), (999000008, 9104), (999000008, 9105),
  (999000009, 9101), (999000009, 9105), (999000009, 9106)
) AS datos(id_estudiante, id_materia)
WHERE NOT EXISTS (
  SELECT 1
  FROM estudiante_materias existente
  WHERE existente.id_estudiante = datos.id_estudiante
    AND existente.id_materia = datos.id_materia
);

-- Calificaciones ficticias para ensayar consultas personalizadas de estudiantes.
-- La tabla también se crea aquí para permitir aplicar el seed con PostgreSQL activo.
CREATE TABLE IF NOT EXISTS calificaciones (
  id SERIAL PRIMARY KEY,
  id_estudiante INTEGER NOT NULL REFERENCES estudiante(id),
  id_materia INTEGER NOT NULL REFERENCES materias(id_materia),
  periodo VARCHAR(20) NOT NULL,
  nota NUMERIC(3,2) NOT NULL,
  CONSTRAINT ck_calificaciones_nota_0_5 CHECK (nota >= 0 AND nota <= 5),
  CONSTRAINT uq_calificacion_estudiante_materia_periodo
    UNIQUE (id_estudiante, id_materia, periodo)
);

CREATE INDEX IF NOT EXISTS ix_calificaciones_id_estudiante
  ON calificaciones (id_estudiante);
CREATE INDEX IF NOT EXISTS ix_calificaciones_id_materia
  ON calificaciones (id_materia);

INSERT INTO calificaciones (id_estudiante, id_materia, periodo, nota)
VALUES
  (999000007, 9101, '2026-1', 4.20),
  (999000007, 9102, '2026-1', 3.80),
  (999000007, 9103, '2026-1', 4.50),
  (999000008, 9102, '2026-1', 3.60),
  (999000008, 9104, '2026-1', 4.30),
  (999000008, 9105, '2026-1', 4.00),
  (999000009, 9101, '2026-1', 4.70),
  (999000009, 9105, '2026-1', 3.90),
  (999000009, 9106, '2026-1', 4.40)
ON CONFLICT (id_estudiante, id_materia, periodo) DO UPDATE SET
  nota = EXCLUDED.nota;

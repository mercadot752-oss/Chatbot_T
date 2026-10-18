from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from .databaseconfig import Base

class EstudianteMateria(Base):
    __tablename__ = "estudiante_materias"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("estudiante.id"), nullable=False)
    id_materia = Column(Integer, ForeignKey("materias.id_materia"))


class Calificacion(Base):
    """Calificaciones académicas de demostración asociadas a un estudiante y materia."""
    __tablename__ = "calificaciones"
    __table_args__ = (
        CheckConstraint("nota >= 0 AND nota <= 5", name="ck_calificaciones_nota_0_5"),
        UniqueConstraint(
            "id_estudiante", "id_materia", "periodo",
            name="uq_calificacion_estudiante_materia_periodo",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_estudiante = Column(Integer, ForeignKey("estudiante.id"), nullable=False, index=True)
    id_materia = Column(Integer, ForeignKey("materias.id_materia"), nullable=False, index=True)
    periodo = Column(String(20), nullable=False)
    nota = Column(Numeric(3, 2), nullable=False)

class Materia(Base):
    __tablename__ = "materias"
    
    id_materia = Column(Integer, primary_key=True)
    nombre_materia = Column(String(100))
    creditos = Column(Integer)

class BuzonSugerencias(Base):
    """Modelo para almacenar sugerencias del buzón"""
    __tablename__ = "buzon_de_sugerencias"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    id_estudiante = Column(String(100), nullable=True)  # Número de documento
    tipo_documento = Column(String(50), nullable=True)  # CC, TI, etc.
    tipo_sugerencia = Column(String(100), nullable=True)  # Queja, Reclamo, Sugerencia, Felicitación
    asunto = Column(String(200), nullable=True)  # El tema de la sugerencia
    descripcion = Column(Text, nullable=False)  # La descripción detallada
    estado = Column(String(50), default="Pendiente")  # Pendiente, En Revisión, Resuelta
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<BuzonSugerencias(id={self.id}, tipo={self.tipo_sugerencia})>"

class Encuesta(Base):
    """Modelo para almacenar encuestas"""
    __tablename__ = "encuesta"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_estudiante = Column(String(30), index=True)
    facultad = Column(String(20), nullable=True)
    satisfaccion = Column(String(20))
    
    def __repr__(self):
        return f"<Survey(id={self.id}, name={self.name})>"


class ChatHistory(Base):
    """Modelo para almacenar historial de conversaciones"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo_documento = Column(String(50), nullable=True)
    numero_documento = Column(String(100), nullable=True)
    mensaje = Column(Text, nullable=False)
    respuesta = Column(Text, nullable=True)
    estado = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ChatHistory(id={self.id}, documento={self.numero_documento})>"


class Estudiante(Base):
    """Modelo para almacenar usuarios"""
    __tablename__ = "estudiante"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(60))
    apellidos = Column(String(60))
    tipo_id = Column(String(20))

    
    def __repr__(self):
        return f"<User(id={self.nombre}, documento={self.tipo_id} {self.id})>"

class Usuario(Base):
    """Modelo para almacenar usuarios"""
    __tablename__ = "usuarios"  # <-- doble guión bajo
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    apellidos = Column(String(100))
    rol = Column(String(20))
    tipo_id = Column(String(20))

    def __repr__(self):  # <-- doble guión bajo
        return f"<Usuario(id={self.id}, nombre={self.nombre}, tipo_id={self.tipo_id})>"

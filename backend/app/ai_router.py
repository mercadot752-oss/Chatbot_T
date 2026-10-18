from fastapi import APIRouter, Body, HTTPException, Depends
import os
import logging
import json
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from controller.databaseconfig import get_db
from controller import models, schemas, crud
from pydantic import BaseModel, Field
from model.materia import Materia as MateriaLogica
from model.buzon_sugerencias import BuzonSugerencia

# Cargar variables de entorno desde .env
load_dotenv()

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


# Modelos Pydantic para los requests
class AIGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Texto del prompt")
    model: Optional[str] = Field(None, description="Modelo a usar (opcional)")
    max_tokens: int = Field(512, description="Máximo de tokens en la respuesta")
    temperature: float = Field(0.7, description="Temperatura (0.0-2.0)")
    identificacion: Optional[str] = Field(None, description="Identificación del estudiante para contexto personalizado")
    usar_contexto: bool = Field(True, description="Si usar el contexto del sistema (JSON + BD)")

# Configuración de Groq con API Key (ahora desde variable de entorno)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Modelos disponibles en Groq (ordenados por velocidad/calidad)
AVAILABLE_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
]


def _get_groq_client():
    """Obtiene el cliente de Groq configurado con API key."""
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY no configurada. Obtén una en https://console.groq.com/ y configúrala como variable de entorno."
        )
    
    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Paquete 'groq' no instalado. Ejecuta: pip install groq"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error configurando Groq: {e}")


def _cargar_contexto_json():
    """Carga el archivo opciones.json para usar como contexto."""
    try:
        ruta_opciones = os.path.join(os.path.dirname(__file__), "opciones.json")
        with open(ruta_opciones, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"No se pudo cargar opciones.json: {e}")
        return None


def _buscar_perfil_por_identificacion(db: Session, identificacion: str = None):
    """Busca una identificación numérica en los perfiles institucionales."""
    if not identificacion:
        return None, None

    try:
        numero = int(str(identificacion).strip())
    except (TypeError, ValueError):
        return None, None

    estudiante = db.query(models.Estudiante).filter(
        models.Estudiante.id == numero
    ).first()
    if estudiante:
        return "estudiante", estudiante

    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == numero
    ).first()
    if usuario:
        return "usuario", usuario

    return None, None


def _obtener_contexto_bd(db: Session, identificacion: str = None):
    """Incluye datos personales solo del perfil previamente validado."""
    contexto = []
    
    try:
        # ============ INFORMACIÓN DEL USUARIO ============
        if identificacion:
            tipo_perfil, perfil = _buscar_perfil_por_identificacion(db, identificacion)

            if tipo_perfil == "estudiante":
                estudiante = perfil
                contexto.append("=" * 50)
                contexto.append("INFORMACIÓN DEL ESTUDIANTE")
                contexto.append("=" * 50)
                contexto.append(f"Nombre completo: {estudiante.nombre} {estudiante.apellidos}")
                contexto.append(f"Identificación: {estudiante.id}")
                contexto.append(f"Tipo de documento: {estudiante.tipo_id}")
                
                # Materias matriculadas con todos los detalles
                materias = db.query(models.EstudianteMateria, models.Materia).join(
                    models.Materia, models.EstudianteMateria.id_materia == models.Materia.id_materia
                ).filter(
                    models.EstudianteMateria.id_estudiante == estudiante.id
                ).all()
                
                if materias:
                    contexto.append(f"\nMATERIAS MATRICULADAS ({len(materias)} materias):")
                    total_creditos = 0
                    for est_mat, mat in materias:
                        contexto.append(f"  • {mat.nombre_materia} - {mat.creditos} créditos")
                        total_creditos += mat.creditos
                    contexto.append(f"\nTotal de créditos matriculados: {total_creditos}")
                    
                    # MATERIAS PRIORIZADAS POR CRÉDITOS
                    try:
                        materias_priorizadas = MateriaLogica.ordenar_matrias(estudiante.id)
                        if materias_priorizadas:
                            contexto.append("\n📊 MATERIAS PRIORIZADAS POR CRÉDITOS:")
                            contexto.append("(Ordenadas de mayor a menor prioridad según créditos)")
                            posicion = 1
                            for materia_obj, prioridad in materias_priorizadas.items():
                                contexto.append(f"  {posicion}. {materia_obj.nombre_materia} - {materia_obj.creditos} créditos (Prioridad: {prioridad})")
                                posicion += 1
                    except Exception as e:
                        logger.warning(f"Error al obtener materias priorizadas: {e}")

                # Las calificaciones son información personal; se consultan solo
                # después de validar que la identificación corresponde a un estudiante.
                calificaciones = db.query(models.Calificacion, models.Materia).join(
                    models.Materia,
                    models.Calificacion.id_materia == models.Materia.id_materia,
                ).filter(
                    models.Calificacion.id_estudiante == estudiante.id
                ).order_by(
                    models.Calificacion.periodo,
                    models.Materia.nombre_materia,
                ).all()

                if calificaciones:
                    contexto.append(f"\nCALIFICACIONES REGISTRADAS ({len(calificaciones)}):")
                    notas = []
                    for calificacion, materia in calificaciones:
                        nota = float(calificacion.nota)
                        notas.append(nota)
                        contexto.append(
                            f"  • {materia.nombre_materia} ({calificacion.periodo}): {nota:.2f}"
                        )
                    promedio = sum(notas) / len(notas)
                    contexto.append(f"Promedio de las calificaciones registradas: {promedio:.2f}")
                        
                contexto.append("")
            
            elif tipo_perfil == "usuario":
                usuario = perfil
                contexto.append("=" * 50)
                contexto.append(f"INFORMACIÓN DEL {usuario.rol.upper()}")
                contexto.append("=" * 50)
                contexto.append(f"Nombre completo: {usuario.nombre} {usuario.apellidos}")
                contexto.append(f"Identificación: {usuario.id}")
                contexto.append(f"Rol: {usuario.rol}")
                contexto.append(f"Tipo de documento: {usuario.tipo_id}")
                contexto.append("")
        
        # ============ TODAS LAS MATERIAS DISPONIBLES ============
        todas_materias = db.query(models.Materia).limit(20).all()
        if todas_materias:
            contexto.append("=" * 50)
            contexto.append(f"MATERIAS DISPONIBLES EN LA UNIVERSIDAD ({len(todas_materias)} primeras):")
            contexto.append("=" * 50)
            for mat in todas_materias:
                contexto.append(f"  • {mat.nombre_materia} - {mat.creditos} créditos")
            contexto.append("")
        
    except Exception as e:
        logger.warning(f"Error obteniendo contexto de BD: {e}")
    
    return "\n".join(contexto) if contexto else None


def _construir_prompt_con_contexto(prompt_usuario: str, contexto_json: dict = None, contexto_bd: str = None):
    """Construye un prompt enriquecido con el contexto del sistema."""
    
    partes = [
        "="*70,
        "ASISTENTE VIRTUAL INTELIGENTE - UNIVERSIDAD DE MEDELLÍN",
        "="*70,
        "",
        "Eres un asistente virtual avanzado de la Universidad de Medellín (UdeM).",
        "",
        "TU MISIÓN:",
        "- Ayudar a estudiantes y profesores con información precisa y personalizada",
        "- Responder preguntas sobre materias, calificaciones, profesores, eventos",
        "- Mostrar materias priorizadas por créditos cuando lo soliciten",
        "- Guiar en trámites administrativos y procesos académicos",
        "- Ser amigable, profesional y usar un tono conversacional",
        "",
        "CAPACIDADES:",
        "✓ Usa la información general y los datos de BD que aparecen en este contexto",
        "✓ Los datos personales solo se incluyen cuando el backend valida la identificación",
        "✓ Si no recibes un perfil personal en el contexto, no inventes ni supongas datos del usuario",
        "✓ Puedes hacer cálculos (promedios, créditos, etc.)",
        "✓ Puedes ayudar a los usuarios a enviar SUGERENCIAS al buzón",
        "",
        "REGLAS IMPORTANTES:",
        "1. Dirígete al usuario por su nombre solo si el contexto incluye un perfil validado",
        "2. Para información académica personal, usa exclusivamente los datos del perfil validado en el contexto",
        "3. Si el contexto no contiene la información solicitada, dilo con claridad y no la inventes",
        "4. 📊 MATERIAS PRIORIZADAS: Cuando te pregunten por materias priorizadas o por orden de créditos:",
        "   - USA EXCLUSIVAMENTE la sección '📊 MATERIAS PRIORIZADAS POR CRÉDITOS'",
        "   - Muestra el listado COMPLETO tal como aparece en el contexto",
        "   - Explica que están ordenadas de MAYOR a MENOR número de créditos",
        "   - Menciona la prioridad (Alta/Media/Baja) de cada materia",
        "5. 📝 BUZÓN DE SUGERENCIAS: Si el usuario quiere enviar una queja, reclamo, sugerencia o felicitación:",
        "   - Explica que puede enviarlo al buzón de sugerencias",
        "   - Los tipos válidos son: Queja, Reclamo, Sugerencia, Felicitación",
        "   - Pide el ASUNTO (tema breve)",
        "   - Pide la DESCRIPCIÓN (detallada)",
        "   - Indica que su mensaje será registrado y revisado por la universidad",
        "   - NO intentes guardar la sugerencia tú mismo, solo guía al usuario",
        "   - Cuando el USUARIO te diga el tipo de sugerencias y lo que quiere di gracias",
        "6. Si no tienes la info exacta, sugiere contactar a la universidad",
        "7. SIEMPRE responde en español de forma clara y concisa",
        "8. Si hay múltiples opciones, preséntalas en formato de lista numerada",
        "9. Incluye emojis relevantes para hacer la conversación más amigable 😊",
        "",
        "⚠️ REGLA CRÍTICA SOBRE ENLACES:",
        "- Cuando una respuesta incluya una URL, DEBES mostrar el enlace COMPLETO",
        "- NO digas 'haz clic aquí' sin el enlace",
        "- Formato correcto: 'Accede aquí: https://ejemplo.com/url-completa'",
        "- Las URLs pueden ser largas, NO LAS ACORTES",
        "- Siempre verifica en las OPCIONES Y SERVICIOS si hay enlaces disponibles",
        "",
    ]
    
    # Agregar contexto de BD si existe
    if contexto_bd:
        partes.append("="*70)
        partes.append("📊 INFORMACIÓN DE LA BASE DE DATOS (TIEMPO REAL):")
        partes.append("="*70)
        partes.append(contexto_bd)
        partes.append("")
    
    # Agregar contexto del JSON si existe
    if contexto_json:
        partes.append("="*70)
        partes.append("📋 OPCIONES, SERVICIOS Y ENLACES DISPONIBLES:")
        partes.append("="*70)
        
        # Extraer información completa del JSON incluyendo resultados y URLs
        if "opciones" in contexto_json:
            for key, opcion in contexto_json["opciones"].items():
                partes.append(f"\n{key}. {opcion.get('texto', '')}")
                
                # Si tiene sub-opciones
                if "opciones" in opcion:
                    for sub_key, sub_opcion in opcion["opciones"].items():
                        partes.append(f"   {key}.{sub_key}. {sub_opcion.get('texto', '')}")
                        
                        # IMPORTANTE: Incluir el resultado con URLs
                        if "resultado" in sub_opcion:
                            resultado = sub_opcion["resultado"]
                            partes.append(f"      → Resultado: {resultado}")
                
                # Si tiene resultado directo (sin sub-opciones)
                elif "resultado" in opcion:
                    partes.append(f"   → Resultado: {opcion['resultado']}")
        
        partes.append("")
        partes.append("🔗 INSTRUCCIONES SOBRE ENLACES:")
        partes.append("- Cuando respondas con URLs, SIEMPRE muestra el enlace completo")
        partes.append("- Usa el formato: 'Puedes acceder aquí: [URL completa]'")
        partes.append("- NO acortes ni omitas las URLs")
        partes.append("- Si el resultado contiene un enlace, INCLÚYELO en tu respuesta")
        partes.append("")
    
    # Agregar pregunta del usuario
    partes.append("="*70)
    partes.append("💬 PREGUNTA DEL USUARIO:")
    partes.append("="*70)
    partes.append(prompt_usuario)
    partes.append("")
    partes.append("="*70)
    partes.append("📝 TU RESPUESTA (clara, precisa y amigable):")
    partes.append("="*70)
    
    return "\n".join(partes)


@router.get("/verificar_identificacion/{identificacion}")
async def verificar_identificacion(identificacion: str, db: Session = Depends(get_db)):
    """Verifica la identificación y retorna el nombre del usuario."""
    try:
        tipo_perfil, perfil = _buscar_perfil_por_identificacion(db, identificacion)

        if tipo_perfil == "estudiante":
            return {
                "encontrado": True,
                "tipo": "estudiante",
                "nombre": f"{perfil.nombre} {perfil.apellidos}",
                "identificacion": identificacion
            }

        if tipo_perfil == "usuario":
            return {
                "encontrado": True,
                "tipo": perfil.rol,
                "nombre": f"{perfil.nombre} {perfil.apellidos}",
                "identificacion": identificacion
            }

        return {
            "encontrado": False,
            "mensaje": "Identificación no encontrada en el sistema"
        }
        
    except Exception as e:
        logger.error(f"Error verificando identificación: {e}")
        raise HTTPException(status_code=500, detail=f"Error al verificar identificación: {str(e)}")


@router.post("/generate")
async def generate_ai(
    request: AIGenerateRequest,
    db: Session = Depends(get_db)
):
    """Genera texto usando Groq (LLaMA/Mixtral) con contexto del sistema.
    
    La IA puede usar:
    - Opciones del chatbot (opciones.json)
    - Información del estudiante de la BD (si se proporciona identificación)
    - Noticias, grupos estudiantiles, etc.
    
    Ejemplo de uso:
    ```json
    {
        "prompt": "¿Qué materias tengo matriculadas?",
        "identificacion": "1234567890",
        "max_tokens": 256
    }
    ```
    """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")

    tipo_perfil, _ = _buscar_perfil_por_identificacion(db, request.identificacion)
    identificacion_validada = tipo_perfil is not None
    if request.identificacion and not identificacion_validada:
        logger.info("Identificación no encontrada; se responderá sin contexto personal")

    client = _get_groq_client()
    
    # Construir prompt con contexto si está habilitado
    prompt_final = request.prompt
    if request.usar_contexto:
        contexto_json = _cargar_contexto_json()
        identificacion_contexto = request.identificacion if identificacion_validada else None
        contexto_bd = _obtener_contexto_bd(db, identificacion_contexto)
        prompt_final = _construir_prompt_con_contexto(request.prompt, contexto_json, contexto_bd)
        logger.info(f"Prompt con contexto construido (longitud: {len(prompt_final)} caracteres)")
    
    # Determinar qué modelo usar
    models_to_try = [request.model] if request.model else AVAILABLE_MODELS
    
    last_error = None
    for model_name in models_to_try:
        try:
            logger.info(f"Intentando generar con modelo: {model_name}")
            
            # Llamar a Groq API (compatible con OpenAI)
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt_final}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            
            # Extraer respuesta
            text = response.choices[0].message.content

            # Guardar cada intercambio del chat activo en la base PostgreSQL única.
            try:
                crud.crear_historial_chat(
                    db,
                    schemas.ChatHistorialCreate(
                        numero_documento=request.identificacion if identificacion_validada else None,
                        mensaje=request.prompt,
                        respuesta=text,
                        estado="IA",
                    ),
                )
            except Exception as e:
                logger.exception("No se pudo guardar el historial del chat")
                raise HTTPException(
                    status_code=500,
                    detail="La respuesta se generó, pero no se pudo guardar el historial.",
                ) from e
            
            return {
                "text": text,
                "model": model_name,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason,
                "contexto_usado": request.usar_contexto,
                "identificacion_validada": identificacion_validada if request.identificacion else None
            }
                
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Fallo con modelo {model_name}: {error_msg}")
            last_error = error_msg
            
            # Si es un error de modelo no encontrado, probar el siguiente
            if "model" in error_msg.lower() and "not found" in error_msg.lower():
                continue
            else:
                # Otros errores (rate limit, auth, etc.) no reintentar
                raise HTTPException(status_code=500, detail=f"Error al generar con {model_name}: {error_msg}")
    
    # Si llegamos aquí, ningún modelo funcionó
    raise HTTPException(
        status_code=502,
        detail=f"No se pudo generar contenido con ningún modelo disponible. Último error: {last_error}"
    )


@router.post("/sugerencia")
async def crear_sugerencia(
    sugerencia: schemas.BuzonSugerenciasBase,
    db: Session = Depends(get_db)
):
    """Crea una nueva sugerencia en el buzón.
    
    Tipos de sugerencia válidos:
    - Queja
    - Reclamo
    - Sugerencia
    - Felicitación
    
    Ejemplo de uso:
    ```json
    {
        "id_estudiante": "1234567890",
        "tipo_documento": "CC",
        "tipo_sugerencia": "Sugerencia",
        "asunto": "Mejora en la biblioteca",
        "descripcion": "Sería genial tener más horarios disponibles los fines de semana."
    }
    ```
    """
    try:
        # Validar tipo de sugerencia
        tipos_validos = ["Queja", "Reclamo", "Sugerencia", "Felicitación"]
        if sugerencia.tipo_sugerencia not in tipos_validos:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de sugerencia no válido. Debe ser uno de: {', '.join(tipos_validos)}"
            )
        
        # Validar que el estudiante exista
        estudiante = db.query(models.Estudiante).filter(
            models.Estudiante.id == sugerencia.id_estudiante
        ).first()
        
        if not estudiante:
            # Buscar como usuario general
            usuario = db.query(models.Usuario).filter(
                models.Usuario.id == sugerencia.id_estudiante
            ).first()
            
            if not usuario:
                raise HTTPException(
                    status_code=404,
                    detail="Identificación no encontrada en el sistema"
                )
        
        # Crear la sugerencia usando el schema
        nueva_sugerencia = schemas.BuzonSugerenciasCreate(
            id_estudiante=sugerencia.id_estudiante,
            tipo_documento=sugerencia.tipo_documento,
            tipo_sugerencia=sugerencia.tipo_sugerencia,
            asunto=sugerencia.asunto,
            descripcion=sugerencia.descripcion,
            estado="Pendiente"
        )
        
        # Guardar en la BD
        sugerencia_guardada = crud.crear_sugerencia(db, nueva_sugerencia)
        
        return {
            "success": True,
            "message": f"¡Gracias! Tu {sugerencia.tipo_sugerencia.lower()} ha sido registrada con éxito.",
            "id": sugerencia_guardada.id,
            "estado": sugerencia_guardada.estado,
            "created_at": sugerencia_guardada.created_at.isoformat() if hasattr(sugerencia_guardada, 'created_at') else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear sugerencia: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la sugerencia: {str(e)}")


@router.get("/models")
async def list_models():
    """Lista los modelos disponibles de Groq."""
    return {
        "models": [
            {
                "name": "openai/gpt-oss-120b",
                "description": "GPT OSS 120B - Modelo principal para respuestas completas",
                "context_window": 131072
            },
            {
                "name": "qwen/qwen3.8-27b",
                "description": "Qwen 3.8 27B - Alternativa general y multilingüe",
                "context_window": 131072
            },
            {
                "name": "openai/gpt-oss-20b",
                "description": "GPT OSS 20B - Alternativa más ligera",
                "context_window": 131072
            }
        ],
        "count": 3,
        "provider": "Groq"
    }

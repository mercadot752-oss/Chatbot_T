import unittest
from types import SimpleNamespace
from unittest.mock import patch

import ai_router
from controller import models
from ai_router import AIGenerateRequest


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.result


class FakeDatabase:
    def __init__(self, estudiante=None, usuario=None):
        self.estudiante = estudiante
        self.usuario = usuario

    def query(self, model):
        if model is models.Estudiante:
            return FakeQuery(self.estudiante)
        if model is models.Usuario:
            return FakeQuery(self.usuario)
        raise AssertionError(f"Consulta inesperada para {model}")


class IdentificationTests(unittest.IsolatedAsyncioTestCase):
    def test_finds_existing_student(self):
        estudiante = SimpleNamespace(id=12345)
        db = FakeDatabase(estudiante=estudiante)

        tipo, perfil = ai_router._buscar_perfil_por_identificacion(db, "12345")

        self.assertEqual(tipo, "estudiante")
        self.assertIs(perfil, estudiante)

    def test_finds_existing_general_user(self):
        usuario = SimpleNamespace(id=67890)
        db = FakeDatabase(usuario=usuario)

        tipo, perfil = ai_router._buscar_perfil_por_identificacion(db, "67890")

        self.assertEqual(tipo, "usuario")
        self.assertIs(perfil, usuario)

    def test_rejects_non_numeric_identification_without_querying_database(self):
        db = FakeDatabase()
        with patch.object(db, "query", wraps=db.query) as query:
            resultado = ai_router._buscar_perfil_por_identificacion(db, "no-es-un-documento")

        self.assertEqual(resultado, (None, None))
        query.assert_not_called()

    async def test_unknown_identification_does_not_load_personal_context_or_link_history(self):
        db = FakeDatabase()
        fake_response = SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content="Respuesta general"),
                finish_reason="stop",
            )],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=2, total_tokens=3),
        )
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **_kwargs: fake_response,
                )
            )
        )

        with (
            patch("ai_router._get_groq_client", return_value=fake_client),
            patch("ai_router._cargar_contexto_json", return_value=None),
            patch("ai_router._obtener_contexto_bd", return_value=None) as contexto_bd,
            patch("ai_router.crud.crear_historial_chat") as guardar_historial,
            patch("ai_router.AVAILABLE_MODELS", ["modelo-prueba"]),
        ):
            resultado = await ai_router.generate_ai(
                AIGenerateRequest(prompt="Pregunta general", identificacion="99999999"),
                db,
            )

        self.assertFalse(resultado["identificacion_validada"])
        contexto_bd.assert_called_once_with(db, None)
        historial = guardar_historial.call_args.args[1]
        self.assertIsNone(historial.numero_documento)
        self.assertEqual(historial.mensaje, "Pregunta general")


if __name__ == "__main__":
    unittest.main()

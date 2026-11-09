from pathlib import Path

import ollama

MODEL_NAME = "fisi-assistant:qwen3-4b"
KNOWLEDGE_FILE = Path(__file__).resolve().parents[1] / "knowledge" / "base_conocimiento_fisi.txt"

SYSTEM_INSTRUCTIONS = """
Eres el Asistente Académico Inteligente de la Facultad de Ingeniería de
Sistemas e Informática (FISI) de la UNMSM.

Responde en español, de manera clara, respetuosa y concisa.
Utiliza exclusivamente el contenido del documento institucional incluido
en el mensaje como fuente para responder preguntas sobre la FISI.
No inventes reglamentos, fechas, requisitos, trámites ni disposiciones.
Si el documento no contiene la respuesta, dilo explícitamente y recomienda
consultar el canal institucional correspondiente.
Distingue entre información documentada y cualquier aclaración general.
"""


class LLMServiceError(RuntimeError):
    """Error controlado al acceder al servicio local de Ollama."""


def _read_knowledge() -> str:
    try:
        content = KNOWLEDGE_FILE.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise LLMServiceError(
            "No se pudo leer la base de conocimientos institucional."
        ) from exc

    if not content:
        return (
            "La base de conocimientos está vacía. No existe información "
            "institucional documentada disponible para responder."
        )
    return content


def answer_question(question: str) -> str:
    knowledge = _read_knowledge()
    prompt = f"""
DOCUMENTO ÚNICO DE BASE DE CONOCIMIENTOS:
--- INICIO DEL DOCUMENTO ---
{knowledge}
--- FIN DEL DOCUMENTO ---

PREGUNTA:
{question}

Responde únicamente con respaldo del documento. Si el documento no permite
responder, indica que no dispones de información documentada suficiente.
"""

    try:
        client = ollama.Client()
        result = client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={
                "num_ctx": 8192,
                "temperature": 0.2,
                "top_p": 0.8,
            },
        )
        answer = result.get("response", "").strip()
        if not answer:
            raise LLMServiceError("Ollama devolvió una respuesta vacía.")
        return answer
    except LLMServiceError:
        raise
    except Exception as exc:
        raise LLMServiceError(
            "No se pudo conectar con Ollama. Verifica que Ollama esté "
            "ejecutándose y que el modelo fisi-assistant:qwen3-4b exista."
        ) from exc

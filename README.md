# Asistente Académico Inteligente FISI - UNMSM

Prueba de Concepto (PoC) desarrollada para la **Tarea 5** de la asignatura. El sistema consiste en una aplicación web interactiva alimentada por un modelo de lenguaje (LLM) ejecutado localmente mediante **Ollama**, diseñado para atender consultas académicas de estudiantes y docentes de la **Facultad de Ingeniería de Sistemas e Informática (FISI - UNMSM)** basándose estrictamente en una base de conocimientos documental estática (sin RAG).

---

## 🚀 Características Principales

- **Inferencia Local y Privada:** Integración con **Ollama** utilizando el modelo cuantizado `Qwen 3 4B`.
- **Zero-RAG Context Injection:** Carga en memoria del corpus institucional (`base_conocimiento_fisi.txt`) inyectado directamente en el prompt del sistema.
- **Backend Asíncrono:** Desarrollado con **FastAPI** y validación de esquemas con **Pydantic**.
- **Interfaz Web Moderna:** Chat responsive en **HTML5, CSS3 (Custom Properties) y JavaScript ES6+**.
- **Suite de Pruebas:** Cobertura de endpoints REST con **Pytest** y `TestClient`.

---

## 📐 Arquitectura de la Solución (Modelo C4)

El flujo de comunicación de la aplicación sigue la siguiente estructura:

1. **Cliente Web (PoC):** Interfaz visual donde el estudiante/docente realiza la consulta en lenguaje natural.
2. **Backend REST (FastAPI):** Recibe la solicitud, valida la entrada (`QueryRequest`), lee la base de conocimientos estática (`Knowledge Base Loader`) y construye el prompt de inferencia (`Prompt Builder`).
3. **Servidor de Inferencia (Ollama):** Procesa la solicitud a través del modelo `fisi-assistant:qwen3-4b` ejecutado en la GPU/CPU local.
4. **Respuesta:** Se devuelve la respuesta estructurada en formato JSON al cliente indicando el modelo utilizado y la fuente documental.

---

## 🛠️ Tecnologías Utilizadas

| Componente           | Tecnología                        |
| :------------------- | :-------------------------------- |
| **Lenguaje Backend** | Python 3.12+                      |
| **Framework Web**    | FastAPI + Uvicorn                 |
| **Orquestador LLM**  | Ollama Python SDK                 |
| **Modelo LLM**       | Qwen (4B / 7B)                    |
| **Frontend**         | Vanilla HTML5 / CSS3 / JavaScript |
| **Testing**          | Pytest + HTTPX                    |

---

## 📋 Requisitos Previos

1. **Python 3.10+** instalado en el sistema.
2. **Ollama** instalado y ejecutándose localmente.

### Preparación del Modelo en Ollama

Asegúrate de descargar e iniciar el modelo de Qwen en Ollama antes de ejecutar la aplicación:

```bash
ollama pull qwen2.5-coder:7b
# o la variante de 4B configurada en tu Modelfile
ollama run fisi-assistant:qwen3-4b
```

---

## ⚡ Instalación y Ejecución Local

1. **Clonar el repositorio:**

   ```bash
   git clone <URL_DE_TU_REPOSITORIO>
   cd LLM-FISI
   ```

2. **Crear y activar entorno virtual:**

   - En Linux/macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - En Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Iniciar el servidor backend (FastAPI):**

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Acceder a la aplicación:**
   Abre tu navegador web e ingresa a `http://localhost:8000`.

---

## 🧪 Ejecución de Pruebas Unitarias

Para verificar el correcto funcionamiento de los endpoints de la API y las validaciones de entrada:

```bash
pytest
```

---

## 📄 Estructura del Proyecto

```text
LLM-FISI/
├── app/
│   ├── api/
│   │   └── routes.py              # Endpoints REST de la API
│   ├── knowledge/
│   │   └── base_conocimiento_fisi.txt # Base de conocimientos estática
│   ├── services/
│   │   └── llm_service.py         # Lógica de conexión con Ollama y armado de prompt
│   ├── static/                    # Archivos estáticos de la interfaz web
│   │   ├── app.js
│   │   ├── index.html
│   │   └── styles.css
│   └── main.py                    # Punto de entrada de la aplicación FastAPI
├── tests/
│   └── test_assistant.py          # Pruebas unitarias
├── Modelfile                      # Configuración de Ollama para el modelo
├── requirements.txt               # Dependencias de Python
└── README.md                      # Documentación del proyecto
```

---

## 👥 Integrantes - Grupo 2

- Chochoca Yarleque Bruno Omar
- Ever Avendaño
- Carlos Montenegro
- Chaco Flores Jose

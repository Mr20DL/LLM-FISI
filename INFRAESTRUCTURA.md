# Análisis de Infraestructura — Asistente Académico FISI (Qwen3-4B, Zero-RAG)

Este documento complementa la PoC (FastAPI + HTML/JS + Ollama) y compara dos escenarios de despliegue: **equipo personal** para desarrollo/pruebas y **servidor FISI** para 20 usuarios concurrentes en producción.

## 1. Supuestos de carga

| Parámetro | Valor asumido |
| :--- | :--- |
| Modelo | Qwen3-4B (36 capas, GQA 8 KV heads, head_dim 128) |
| Contexto (`num_ctx`) | 8 192 tokens (configurado en `Modelfile`) |
| Prompt por consulta | ~1 500–2 500 tokens (corpus inyectado + historial) |
| Salida promedio | ~300 tokens |
| Usuarios concurrentes (servidor) | 20 sesiones activas |
| Objetivo de latencia | < 5 s para la primera respuesta (TTFT < 1.5 s) |

**Costo de memoria del KV cache (FP16):** `2 × 36 capas × 8 KV heads × 128 × 2 bytes ≈ 144 KB/token`.
Una sesión con 8 192 tokens consume ≈ **1.15 GB de VRAM solo en KV cache**; 20 sesiones de 4 096 tokens ≈ **11.5 GB**. Este cálculo gobierna todo el dimensionamiento.

---

## 2. Escenario A — Equipo personal (desarrollo y pruebas)

### 2.1 Requisitos de hardware

| Nivel | CPU | RAM | VRAM / GPU | Desempeño esperado (Qwen3-4B Q4) |
| :--- | :--- | :--- | :--- | :--- |
| **Mínimo** | 4 núcleos modernos (AVX2) | 16 GB | Sin GPU (CPU-only) | 3–8 tok/s; TTFT 3–10 s |
| **Recomendado** | 6–8 núcleos | 16–32 GB | 6–8 GB (RTX 3050/4060, RTX 3060 12 GB) | 25–45 tok/s en GPU completa |
| **Cómodo** | 8 núcleos | 32 GB | 12 GB+ (RTX 3060/4070) u 16 GB unified (Apple M-series) | 35–60 tok/s, contexto 8k sin swapping |

**Almacenamiento:** ~5–8 GB para Ollama + modelo cuantizado (`q4_K_M` ≈ 2.5 GB) + entorno Python.
**Software:** drivers CUDA actualizados, Ollama ≥ 0.5, Python 3.12+, navegador moderno.

### 2.2 Limitaciones típicas de una laptop de estudiante

| Limitación | Impacto en la PoC |
| :--- | :--- |
| VRAM de 4–6 GB y compartida con el SO | Obliga a `q4_K_M`; contextos > 8k provocan *offload* parcial a RAM y caídas a < 10 tok/s |
| GPU integrada (Iris Xe / Radeon 780M) | Funciona, pero 5–15 tok/s; insuficiente para demostraciones fluidas |
| 16 GB de RAM con navegador + IDE + Ollama | Riesgo de *thrashing*; se recomienda cerrar aplicaciones y usar `num_ctx` 4k–8k |
| Throttling térmico y batería | Rendimiento variable; la inferencia sostenida calienta el equipo y reduce tok/s |
| Un solo usuario | No hay concurrencia real: Ollama atiende peticiones en cola y la segunda consulta espera |
| Arranque en frío | La carga del modelo tarda 5–20 s tras `keep_alive` expirado |
| Sin GPU dedicada (solo CPU) | Viable para pruebas funcionales, **no** para demo en vivo ni evaluación de latencia |

**Conclusión:** el equipo personal es suficiente para **desarrollar, probar y validar la PoC con un usuario**, pero no representa ni de lejos la capacidad necesaria para 20 usuarios concurrentes.

---

## 3. Escenario B — Servidor FISI (20 usuarios concurrentes)

### 3.1 Por qué Ollama no sirve para producción

Ollama es un excelente *runtime* de escritorio, pero no un servidor de inferencia multi-tenant:

| Limitación | Consecuencia a 20 usuarios |
| :--- | :--- |
| **Sin PagedAttention** | El KV cache se reserva por *slot* completo; la memoria se fragmenta y se sobre-asigna |
| **Concurrencia por slots (`OLLAMA_NUM_PARALLEL`)** | Cada slot multiplica el KV cache; con 8k de contexto el consumo se vuelve inviable en 24 GB |
| **Batching limitado** | No hay *continuous batching* maduro: las secuencias cortas esperan a las largas (*head-of-line blocking*) |
| **Sin tensor parallelism** | No puede repartir el modelo entre varias GPUs |
| **Sin colas justas ni *preemption*** | Un usuario con generación larga degrada a los demás; no hay cuotas por rol |
| **Observabilidad escasa** | Sin métricas Prometheus nativas (TTFT, tok/s, KV usage) ni trazas por petición |
| **Ciclo de vida por `keep_alive`** | La expulsión/recarga del modelo genera *picos de latencia* de decenas de segundos |
| **Sin autenticación, rate limiting ni multi-tenancy** | Todo debe implementarse en la capa FastAPI/Nginx |

> Ollama es válido para la PoC y para un *fallback* de baja concurrencia; para 20 usuarios se requiere un motor con **PagedAttention + continuous batching + prefix caching**, como **vLLM**.

### 3.2 GPUs de servidor recomendadas

| GPU | VRAM | Ancho de banda | Precisión | Consumo | Rol recomendado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NVIDIA T4** | 16 GB | 320 GB/s | FP16/INT8 (sin BF16/FP8) | 70 W | Mínimo viable; perfil bajo para servidores existentes |
| **NVIDIA L4** | 24 GB | 300 GB/s | FP16/INT8/**FP8** (Ada) | 72 W | **Recomendada**: mejor eficiencia energética y FP8 |
| **NVIDIA A10G** | 24 GB | 600 GB/s | FP16/INT8/BF16 | 150 W | Mayor throughput y margen para picos |

**Estimaciones de capacidad (Qwen3-4B, 20 sesiones, 4k de contexto, ~300 tokens de salida):**

| GPU | Throughput agregado estimado | Tok/s por usuario | ¿20 concurrentes? |
| :--- | :--- | :--- | :--- |
| T4 16 GB | 250–500 tok/s | 12–25 | Sí, con int4 y contexto ≤ 4k (ajustado) |
| L4 24 GB | 400–800 tok/s | 20–35 | **Sí, con margen** (FP8 + KV FP8) |
| A10G 24 GB | 800–1 500 tok/s | 40–60 | Sí, holgado; absorbe picos y contexto 8k |

**Cálculo de memoria en L4 (24 GB):** pesos FP8 ≈ 4.3 GB + KV cache FP8 de 20 × 4 096 tokens ≈ 5.8 GB + overhead de runtime ≈ 2 GB ⇒ **~12 GB**, dejando margen para 8k de contexto o 40 sesiones. Con AWQ int4 (≈ 2.5 GB) el margen es aún mayor. En T4 se debe usar int4 + contexto 4k para no exceder 16 GB.

**Recomendación:** **1× NVIDIA L4 24 GB** como punto de partida; **A10G** si se esperan picos > 30 usuarios o se requiere mayor TTFT. T4 solo como opción de mínimo costo/legacy. Alternativas cloud equivalentes: AWS `g6.xlarge` (L4), `g5.xlarge` (A10G); GCP `g2-standard-8` (L4).

### 3.3 Arquitectura de software propuesta

```
Cliente web / API
      │ HTTPS + SSE
      ▼
┌─────────────┐   rate limiting, TLS, timeouts
│    Nginx    │──────────────────────────────┐
└──────┬──────┘                              │
       │ proxy_pass                          │ estáticos (HTML/JS)
       ▼                                     ▼
┌──────────────────────┐              (frontend)
│ FastAPI (N réplicas) │  JWT, cuotas, validación Pydantic
│ stateless            │
└───┬──────────┬───────┘
    │          │
    │          └──────────────► Redis
    │                        (broker, caché, rate limit,
    │                         sesiones, idempotencia)
    ▼
┌──────────────────────┐        ┌──────────────────────┐
│  vLLM (OpenAI API)   │◄───────│ Celery workers       │
│ PagedAttention,      │        │ tareas batch/largas  │
│ continuous batching, │        │ (reportes, resúmenes)│
│ prefix caching       │        └──────────────────────┘
└──────────┬───────────┘
           │ métricas
           ▼
   Prometheus + Grafana + DCGM exporter + Loki
```

**Componentes y responsabilidades:**

| Capa | Tecnología | Función |
| :--- | :--- | :--- |
| Borde | **Nginx** | TLS, reverse proxy, `limit_req`/`limit_conn`, timeouts, `proxy_buffering off` para SSE, servir frontend |
| API | **FastAPI + Uvicorn** (Gunicorn, N workers) | Autenticación JWT, cuotas por usuario, construcción del prompt Zero-RAG, streaming SSE; sin estado (escala horizontal) |
| Inferencia | **vLLM** (endpoint compatible OpenAI) | PagedAttention, continuous batching, **prefix caching** (clave: el system prompt + corpus es constante), tensor parallelism si se añade una 2.ª GPU |
| Asíncrono | **Redis + Celery** | Colas con prioridad (docente > estudiante), reintentos, tareas largas fuera del request HTTP; Redis como broker/result backend |
| Caché | **Redis** | Caché exacta/semántica de FAQs, *rate limiting* distribuido, bloqueo de sesión |
| Observabilidad | **Prometheus + Grafana + Loki** | TTFT, tok/s, longitud de cola, uso de KV cache, GPU (DCGM), errores 5xx |
| Despliegue | **Docker Compose → Kubernetes** | Reproducibilidad, *healthchecks*, escalado horizontal de FastAPI y workers |

**Decisiones clave:**

1. **vLLM en lugar de Ollama** para el servicio de inferencia; se mantiene Ollama solo en desarrollo.
2. **Streaming (SSE) directo** de FastAPI → vLLM para el chat interactivo; **Celery** se reserva para tareas no interactivas (generación de reportes, indexación, resúmenes), ya que las colas no son adecuadas para *streaming* de tokens.
3. **Prefix caching + contexto 4k** por defecto: el corpus Zero-RAG es idéntico en cada petición, por lo que cachear el prefijo reduce el coste de *prefill* drásticamente.
4. **Límites explícitos:** `max_model_len=4096`, `max_num_seqs=24`, cuota de tokens/día por usuario y *timeout* de generación.
5. **Alta disponibilidad:** al menos 2 réplicas de FastAPI y *healthchecks*; la GPU es el punto único de fallo, por lo que se recomienda *failover* a CPU/Ollama (degradado) o a un segundo nodo.

### 3.4 Comparativa Ollama vs. vLLM

| Criterio | Ollama | vLLM |
| :--- | :--- | :--- |
| Enfoque | Escritorio / un usuario | Servidor multi-tenant |
| KV cache | Por slot, sin paginación | PagedAttention |
| Batching | Limitado | Continuous batching |
| Prefix caching | Parcial | Sí, maduro |
| Tensor parallelism | No | Sí |
| Métricas Prometheus | No nativas | Sí |
| API OpenAI | Compatible | Compatible |
| Complejidad operativa | Muy baja | Media |

### 3.5 Riesgos y mitigaciones

| Riesgo | Mitigación |
| :--- | :--- |
| Picos > 20 usuarios | Cola en Redis + `max_num_seqs` + autoescalado de FastAPI; degradar a contexto 2k |
| VRAM insuficiente | Cuantización FP8/AWQ, KV cache FP8, límite de contexto y de sesiones |
| Cold start del modelo | Precarga al iniciar el contenedor y *warm-up* con una petición sintética |
| Caída de la GPU | *Fallback* a Ollama/CPU en modo degradado + alertas |
| Abuso o scraping | Rate limiting en Nginx/Redis, JWT, cuotas por usuario y auditoría |
| Alucinaciones del LLM | Zero-RAG estricto + validación de la fuente documental en la respuesta |

---

## 4. Resumen ejecutivo

| Escenario | Hardware | Motor | Usuarios | Inversión relativa |
| :--- | :--- | :--- | :--- | :--- |
| Desarrollo (laptop) | 16 GB RAM, GPU 6–8 GB | Ollama | 1 | Baja (equipo existente) |
| Producción FISI | 1× L4 24 GB (o A10G) + 8 vCPU, 32 GB RAM | vLLM + Redis/Celery + Nginx | 20 concurrentes | Media |

La PoC con Ollama demuestra la viabilidad funcional; el salto a producción exige **un motor de inferencia con batching paginado (vLLM)**, **una GPU de 24 GB (L4/A10G)**, y una arquitectura **stateless con colas, caché y observabilidad** para sostener 20 usuarios concurrentes con latencias aceptables.

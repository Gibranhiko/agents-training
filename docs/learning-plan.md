# AI Lead Qualification Workflow — Plan de Aprendizaje

> **Objetivo:** Entender los fundamentos de sistemas agénticos construyendo algo real,
> incrementalmente, sin saltarte pasos conceptuales.
>
> **Principio rector:** Código ejecutable primero. Documentación después. Cada fase
> termina con algo que puedes correr, leer y entender al 100%.

---

## Cómo usar este plan

Cada fase tiene:

- **Concepto central** — lo que vas a aprender de verdad
- **Lo que construyes** — qué archivos existen al final
- **Ejercicio de entendimiento** — pregunta que debes poder responder sin ver el código
- **Señal de que puedes avanzar** — cómo saber que la fase está realmente terminada
- **Trampas comunes** — qué evitar

No avances hasta poder explicar el concepto central en voz alta. Si no puedes explicarlo, no lo entendiste.

---

## Fase 0 — Entorno y punto de partida

**Concepto central:** Un proyecto de Python bien configurado desde el inicio ahorra fricciones durante todo el aprendizaje.

### Lo que haces

```bash
uv init ai-lead-qualification
cd ai-lead-qualification
uv add fastapi pydantic openai httpx rich structlog pytest
uv add --dev pytest-asyncio
```

Estructura resultante:

```
ai-lead-qualification/
├── pyproject.toml
├── .env                  # OPENAI_API_KEY=sk-...
├── .gitignore
└── main.py               # solo un print("hello") por ahora
```

### Ejercicio de entendimiento

- ¿Qué hace `uv` diferente a `pip`?
- ¿Por qué `.env` va en `.gitignore`?

### Señal de que puedes avanzar

`uv run python main.py` imprime "hello" sin errores. Tienes tu API key configurada.

---

## Fase 1 — El workflow en un solo archivo

**Concepto central:** Antes de separar código en módulos, entiende el flujo completo en un lugar. Si no puedes leerlo lineal, no lo entiendes todavía.

### Lo que construyes

`main.py` — el workflow completo de principio a fin, ~120 líneas.

El archivo hace esto en orden:

1. Define un lead como diccionario simple
2. Llama a OpenAI para "investigar" la empresa (prompt directo, respuesta en texto)
3. Llama a OpenAI para analizar el lead con base en la investigación
4. Genera un score numérico (1-100)
5. Decide el siguiente paso con un `if score > 70`
6. Genera un email personalizado
7. Imprime todo el estado final con `rich`

No hay FastAPI. No hay base de datos. No hay clases. Solo funciones y un diccionario que va acumulando datos.

### Por qué importa hacerlo así

Vas a ver exactamente cómo el estado (el diccionario) crece con cada paso. Cuando lo conviertas en clases Pydantic en la Fase 2, entenderás qué estás modelando y por qué cada campo existe.

### Estructura al final de la fase

```
ai-lead-qualification/
├── pyproject.toml
├── .env
├── .gitignore
└── main.py               # ~120 líneas, workflow completo
```

### Ejercicio de entendimiento

Sin ver el código, describe: ¿qué datos tiene el diccionario antes del paso 3? ¿y después del paso 5?

### Señal de que puedes avanzar

`uv run python main.py` corre el workflow completo con un lead real y ves el output en terminal. Puedes leer `main.py` de arriba abajo y entender cada línea.

### Trampas comunes

- No te compliques con async todavía. Llamadas síncronas a OpenAI primero.
- No intentes separar en archivos "para que quede más limpio". La incomodidad de todo en un archivo es el punto.
- Si el prompt de OpenAI no devuelve lo que esperas, ajusta el prompt. No construyas lógica defensiva todavía.

---

## Fase 2 — Estado tipado con Pydantic

**Concepto central:** El estado de un workflow debe tener forma definida. Pydantic v2 te da validación, serialización y autodocumentación gratis.

### Lo que construyes

Extraes el diccionario del estado a modelos Pydantic. El workflow sigue siendo lineal, pero ahora el estado tiene tipos.

Modelos que defines:

```python
class Lead(BaseModel): ...
class ResearchResult(BaseModel): ...
class LeadScore(BaseModel): ...
class Recommendation(BaseModel): ...
class EmailDraft(BaseModel): ...
class WorkflowState(BaseModel): ...  # contiene todos los anteriores
```

`WorkflowState` es el objeto central. Empieza con solo `lead: Lead` y termina con todos los campos populated.

### Estructura al final de la fase

```
ai-lead-qualification/
├── pyproject.toml
├── .env
├── .gitignore
├── main.py               # ahora usa los modelos
└── models.py             # todos los modelos Pydantic
```

### Por qué Pydantic aquí y no antes

Cuando tenías el diccionario plano, sabías exactamente qué datos necesitabas. Ahora que lo sabes, modelas con tipos. Si hubieras empezado con Pydantic, habrías modelado cosas que no necesitabas.

### Ejercicio de entendimiento

- ¿Cuál es la diferencia entre `model.model_dump()` y `dict(model)`?
- ¿Por qué `WorkflowState` contiene los demás modelos en lugar de heredar de ellos?

### Señal de que puedes avanzar

El workflow sigue corriendo. Si cambias un campo de `LeadScore` a un tipo incorrecto, Pydantic lanza un error de validación descriptivo. Entiendes qué representa cada campo de `WorkflowState`.

### Trampas comunes

- No uses `Optional` en todo por costumbre. Piensa qué campos son realmente opcionales vs. cuáles no existen todavía al inicio del workflow.
- `WorkflowState` debe poder serializarse a JSON en cualquier punto del workflow. Verifica esto con `state.model_dump_json()`.

---

## Fase 3 — Structured Outputs de OpenAI

**Concepto central:** En lugar de pedirle a OpenAI texto libre y parsearlo, le pides un JSON que valide contra un schema Pydantic. Esto elimina toda la fragilidad del parsing de texto.

### Lo que construyes

Conviertes las llamadas a OpenAI para usar `response_format` con tus modelos Pydantic.

```python
response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[...],
    response_format=LeadScore,
)
score = response.choices[0].message.parsed  # ya es un LeadScore validado
```

Cada llamada a OpenAI devuelve directamente un modelo Pydantic, no texto.

### Estructura al final de la fase

```
ai-lead-qualification/
├── pyproject.toml
├── .env
├── .gitignore
├── main.py
└── models.py             # los modelos ahora son también tus response schemas
```

### Por qué esto es fundamental para agentes

En sistemas agénticos, el output no estructurado es el enemigo. Cuando un agente pasa datos a otro agente, necesitas garantías de tipo. Structured Outputs es cómo obtienes esas garantías en la capa de LLM.

### Ejercicio de entendimiento

- ¿Qué pasa si le pides a OpenAI un campo que no existe en tu modelo Pydantic?
- ¿Por qué `gpt-4o-mini` puede ser mejor que `gpt-4o` para structured outputs en este contexto?

### Señal de que puedes avanzar

Eliminas todo código de parsing de texto (`json.loads`, `.split()`, regex). Cada llamada a OpenAI devuelve un objeto Pydantic directamente. El workflow sigue corriendo.

### Trampas comunes

- No todos los modelos de OpenAI soportan structured outputs igual. Quédate con `gpt-4o-mini` o `gpt-4o` para esto.
- Si tu modelo Pydantic tiene campos muy complejos (nested, uniones complicadas), simplifica primero. Structured outputs falla silenciosamente con schemas mal definidos.

---

## Fase 4 — Tools como funciones independientes

**Concepto central:** Cada paso del workflow se convierte en una función con firma clara: recibe estado, devuelve estado actualizado. Esto es lo que los frameworks de agentes llaman "tools".

### Lo que construyes

Extraes cada paso de `main.py` a funciones independientes con firmas explícitas:

```python
def research_company(state: WorkflowState) -> WorkflowState: ...
def analyze_lead(state: WorkflowState) -> WorkflowState: ...
def score_lead(state: WorkflowState) -> WorkflowState: ...
def recommend_next_action(state: WorkflowState) -> WorkflowState: ...
def generate_email(state: WorkflowState) -> WorkflowState: ...
```

El `main.py` se convierte en el orquestador que llama estas funciones en secuencia:

```python
state = WorkflowState(lead=lead)
state = research_company(state)
state = analyze_lead(state)
state = score_lead(state)
state = recommend_next_action(state)
state = generate_email(state)
```

### Estructura al final de la fase

```
ai-lead-qualification/
├── pyproject.toml
├── .env
├── .gitignore
├── main.py               # orquestador: llama tools en secuencia
├── models.py
└── tools.py              # las 5 funciones
```

### Por qué la firma `(state) -> state` importa

Esta es la convención fundamental en LangGraph, LangChain, y prácticamente todos los frameworks de orquestación. Cuando llegues a esos frameworks, reconocerás este patrón inmediatamente. Estás construyendo el concepto a mano.

### Ejercicio de entendimiento

- ¿Por qué cada tool recibe el state completo en lugar de solo los datos que necesita?
- ¿Qué ventaja tiene que cada tool devuelva el state en lugar de mutarlo in-place?

### Señal de que puedes avanzar

Puedes cambiar el orden de llamada en `main.py` y entender exactamente qué falla y por qué (dependencia de datos entre tools). Cada tool es testeable de forma independiente con un state mock.

### Trampas comunes

- No pongas lógica de routing (los `if score > 70`) dentro de las tools. Las tools transforman datos. El routing es responsabilidad del orquestador.
- No añadas parámetros extra a las tools. Si una tool necesita configuración (como el modelo de OpenAI a usar), ponla en un objeto de configuración separado, no en la firma.

---

## Fase 5 — Routing y lógica condicional

**Concepto central:** Un workflow no es siempre lineal. El routing es la lógica que decide qué tool ejecutar basándose en el estado actual.

### Lo que construyes

Extraes las decisiones condicionales a funciones de routing explícitas:

```python
def route_by_score(state: WorkflowState) -> str:
    if state.lead_score.score >= 80:
        return "high_value"
    elif state.lead_score.score >= 50:
        return "nurture"
    else:
        return "disqualify"
```

El orquestador en `main.py` usa estas funciones:

```python
state = score_lead(state)
route = route_by_score(state)

if route == "high_value":
    state = generate_email(state)          # email agresivo de ventas
elif route == "nurture":
    state = generate_nurture_email(state)  # email de contenido
else:
    state = mark_disqualified(state)       # no genera email
```

Añades `workflow_status` y `route_taken` a `WorkflowState` para que el routing sea observable.

### Estructura al final de la fase

```
ai-lead-qualification/
├── pyproject.toml
├── .env
├── .gitignore
├── main.py
├── models.py
├── tools.py
└── routing.py            # funciones de routing
```

### Por qué el routing es un concepto separado

En LangGraph, el routing es literalmente nodos separados del grafo. En sistemas multi-agente, el routing decide qué agente recibe el control. Al separarlo ahora, interiorizas que "decidir qué hacer" y "hacer algo" son responsabilidades distintas.

### Ejercicio de entendimiento

- ¿Qué pasa si el score devuelto por OpenAI es `None` porque el modelo falló? ¿Dónde debe manejarse eso?
- ¿Por qué las funciones de routing devuelven strings en lugar de booleans?

### Señal de que puedes avanzar

Puedes testear el routing de forma aislada sin llamar a OpenAI. Puedes crear un `WorkflowState` con un score específico y verificar que `route_by_score` devuelve el string correcto.

---

## Fase 6 — Persistencia simple

**Concepto central:** Un workflow que no persiste su estado no es recuperable. Persistencia te da historial, debugging, y la base para reintentos.

### Lo que construyes

Una capa de almacenamiento con `sqlite3` directo (sin ORM todavía):

```python
# storage.py
def save_workflow_execution(state: WorkflowState) -> str: ...
def get_workflow_execution(execution_id: str) -> WorkflowState: ...
def list_executions() -> list[dict]: ...
```

`WorkflowState` se serializa a JSON y se guarda en SQLite. Un `execution_id` (UUID) identifica cada ejecución.

Añades `execution_id`, `created_at`, y `completed_at` a `WorkflowState`.

### Estructura al final de la fase

```
ai-lead-qualification/
├── pyproject.toml
├── .env
├── .gitignore
├── main.py
├── models.py
├── tools.py
├── routing.py
├── storage.py            # sqlite3 directo
└── leads.db              # generado en runtime
```

### Por qué sqlite3 directo antes de SQLAlchemy

SQLAlchemy resuelve problemas de proyectos con múltiples modelos, migraciones complejas, y pools de conexiones. Tu proyecto de aprendizaje no tiene esos problemas todavía. `sqlite3` te muestra exactamente qué SQL se ejecuta. Cuando agregues SQLAlchemy en una fase posterior, entenderás qué abstracción añade y por qué.

### Ejercicio de entendimiento

- ¿Cómo recuperarías el estado de un workflow que falló en la Fase 3 (después de score_lead, antes de generate_email)?
- ¿Qué formato usas para serializar `datetime` en JSON?

### Señal de que puedes avanzar

Corres el workflow dos veces con el mismo lead. Abres `leads.db` con cualquier SQLite viewer y ves dos registros distintos con execution_ids diferentes.

---

## Fase 7 — Observabilidad y logging estructurado

**Concepto central:** En producción, `print()` no sirve. El logging estructurado te da datos que puedes buscar, filtrar, y analizar. La observabilidad es lo que distingue sistemas de producción de scripts.

### Lo que construyes

Logging estructurado con `structlog` en cada tool y en el orquestador:

```python
log.info("tool.started", tool="research_company", execution_id=state.execution_id)
log.info("tool.completed", tool="research_company", duration_ms=elapsed, execution_id=state.execution_id)
log.error("tool.failed", tool="research_company", error=str(e), execution_id=state.execution_id)
```

Añades a `WorkflowState`:

- `execution_log: list[LogEntry]` — timestamps de cada tool
- `tool_durations: dict[str, float]` — cuánto tardó cada tool
- `error_count: int`

### Estructura al final de la fase

```
ai-lead-qualification/
├── pyproject.toml
├── .env
├── .gitignore
├── main.py
├── models.py
├── tools.py
├── routing.py
├── storage.py
└── observability.py      # configuración de structlog + LogEntry model
```

### Por qué estructurado y no texto libre

```
# Malo:
print(f"Research tool completed in {elapsed} seconds")

# Bueno:
log.info("tool.completed", tool="research_company", duration_ms=elapsed, execution_id=state.execution_id)
```

El segundo puede filtrarse, agregarse, y correlacionarse. El primero solo puede leerse.

### Ejercicio de entendimiento

- ¿Cómo correlacionarías todos los logs de una sola ejecución de workflow?
- ¿Qué diferencia hay entre un log de `INFO` y uno de `DEBUG` en el contexto de tools?

### Señal de que puedes avanzar

Puedes responder "¿cuánto tardó el tool `score_lead` en la ejecución X?" mirando solo los logs, sin ver el código.

---

## Fase 8 — Error handling y reintentos

**Concepto central:** Los LLMs fallan. Las APIs tienen rate limits. Un sistema agéntico robusto tiene estrategia de retry, estados de falla, y sabe qué puede recuperarse.

### Lo que construyes

Un decorador de retry simple:

```python
def with_retry(max_attempts: int = 3, delay_seconds: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(state: WorkflowState) -> WorkflowState:
            for attempt in range(max_attempts):
                try:
                    return func(state)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        state.workflow_status = "failed"
                        state.error = str(e)
                        return state
                    time.sleep(delay_seconds * (2 ** attempt))  # backoff
        return wrapper
    return decorator
```

Añades a `WorkflowState`:
- `workflow_status: Literal["running", "completed", "failed", "partial"]`
- `failed_at_tool: str | None`
- `error: str | None`

### Estructura al final de la fase

```
ai-lead-qualification/
├── pyproject.toml
├── .env
├── .gitignore
├── main.py
├── models.py
├── tools.py
├── routing.py
├── storage.py
├── observability.py
└── retry.py              # decorador + estrategia de backoff
```

### Ejercicio de entendimiento

- ¿Qué herramientas del sistema actual tienes para retomar un workflow que falló en `score_lead`?
- ¿Por qué "exponential backoff" en lugar de retry inmediato?

### Señal de que puedes avanzar

Puedes simular una falla (lanzar una excepción desde dentro de un tool) y verificar que el workflow termina en estado `"failed"` con `failed_at_tool` correcto, y que el estado parcial se persiste en SQLite.

---

## Fase 9 — FastAPI encima del workflow

**Concepto central:** HTTP es solo un transporte. Tu workflow ya funciona. FastAPI lo expone sin cambiar su lógica interna.

### Lo que construyes

```
api/
├── __init__.py
├── app.py         # FastAPI app
└── routes.py      # endpoints
```

Endpoints:

```
POST /leads              — inicia workflow, devuelve execution_id
GET  /leads/{id}         — devuelve estado de ejecución
GET  /leads              — lista todas las ejecuciones
GET  /leads/{id}/email   — devuelve el email draft generado
```

El orquestador que ya existe en `main.py` se mueve a `workflow/runner.py`. FastAPI solo lo llama.

### Estructura al final de la fase

```
ai-lead-qualification/
├── pyproject.toml
├── .env
├── .gitignore
├── models.py
├── tools.py
├── routing.py
├── storage.py
├── observability.py
├── retry.py
└── api/
    ├── app.py
    └── routes.py
```

### Por qué FastAPI hasta aquí y no desde el principio

Si hubiera empezado con FastAPI, habrías pasado horas en request/response models, status codes, y Pydantic integration, antes de entender el workflow. Ahora que el workflow funciona, FastAPI es una capa trivial encima.

### Ejercicio de entendimiento

- ¿Por qué el endpoint `POST /leads` debería devolver `202 Accepted` en lugar de `200 OK` si el workflow tarda varios segundos?
- ¿Qué necesitarías cambiar en la arquitectura para que el workflow corra en background (async)?

### Señal de que puedes avanzar

Puedes hacer `curl -X POST http://localhost:8000/leads -d '{"company_name": "Acme", ...}'` y recibir un `execution_id`. Luego hacer `curl http://localhost:8000/leads/{id}` y ver el estado completo.

---

## Fase 10 — Testing

**Concepto central:** Los tests en un proyecto de agentes son diferentes. No testeas que OpenAI devuelva algo específico. Testeas que tu lógica de estado, routing, y persistencia funciona correctamente independientemente del LLM.

### Lo que construyes

```
tests/
├── test_models.py         # validación Pydantic, serialización
├── test_tools.py          # tools con OpenAI mockeado
├── test_routing.py        # routing con estados fabricados
├── test_storage.py        # persistencia con SQLite en memoria
└── test_workflow.py       # workflow end-to-end con mocks
```

La regla: **nunca llames a OpenAI en tests**. Usa `unittest.mock` o `pytest-mock` para simular las respuestas.

```python
def test_route_by_score_high_value():
    state = WorkflowState(
        lead=Lead(...),
        lead_score=LeadScore(score=85, reasoning="strong fit")
    )
    assert route_by_score(state) == "high_value"
```

### Por qué los tests van hasta aquí

No significa que testees al final. Significa que la fase de "aprender a testear agentes" requiere que ya entiendas qué estás testeando. Ahora que conoces el sistema completo, puedes escribir tests que validan comportamiento real, no mocks vacíos.

Lo ideal: cada vez que construiste una fase, habrías podido añadir tests. Esta fase es para estructurarlo formalmente.

### Ejercicio de entendimiento

- ¿Cómo testeas que el retry decorator reintenta exactamente 3 veces antes de marcar el workflow como `"failed"`?
- ¿Qué pasa con tus tests si cambias el schema de `WorkflowState`? ¿Es eso bueno o malo?

### Señal de que puedes avanzar

`uv run pytest` corre sin errores. Tienes al menos un test por tool, routing, y persistencia. Ningún test hace llamadas reales a OpenAI.

---

## Fase 11 — Refactor: SQLAlchemy + módulos limpios

**Concepto central:** Ahora que entiendes exactamente qué datos persistir y cómo fluyen, introduce SQLAlchemy. El ORM tiene sentido cuando ya entiendes el problema que resuelve.

### Lo que construyes

Reemplazas `sqlite3` directo con SQLAlchemy + modelos ORM:

```python
class WorkflowExecutionORM(Base):
    __tablename__ = "workflow_executions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    lead_data: Mapped[str] = mapped_column(Text)      # JSON
    state_data: Mapped[str] = mapped_column(Text)     # JSON
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)
```

Reorganizas la estructura en módulos limpios:

```
ai-lead-qualification/
├── pyproject.toml
├── .env
├── app/
│   ├── domain/
│   │   └── models.py       # Pydantic models
│   ├── workflow/
│   │   ├── runner.py       # orquestador
│   │   ├── tools.py
│   │   └── routing.py
│   ├── storage/
│   │   ├── database.py     # SQLAlchemy engine + session
│   │   ├── orm_models.py   # ORM models
│   │   └── repository.py  # operaciones CRUD
│   ├── api/
│   │   ├── app.py
│   │   └── routes.py
│   └── core/
│       ├── observability.py
│       └── retry.py
└── tests/
```

### Por qué este refactor tiene sentido ahora

Cuando hagas este refactor, entenderás exactamente qué añade SQLAlchemy (gestión de sesiones, lazy loading, migraciones con Alembic) porque ya sabes qué hacía `sqlite3` directo. No es magia, es una abstracción sobre algo que ya conoces.

### Señal de que puedes avanzar

`uv run pytest` sigue pasando. `uv run uvicorn app.api.app:app --reload` sigue funcionando. La estructura de archivos es legible para alguien que no conoce el proyecto.

---

## Qué sigue después de este proyecto

Completar estas 11 fases te da una base sólida. Aquí está la progresión natural:

### Proyecto 2 — LangGraph

Reemplazas `workflow/runner.py` con un grafo de LangGraph. Tus tools (`tools.py`) y modelos (`domain/models.py`) no cambian. Solo el orquestador cambia. Verás que LangGraph es exactamente el patrón que construiste a mano, con state management y routing incorporados.

### Proyecto 3 — MCP Server

Conviertes tus tools en un MCP Server. Claude Desktop puede usarlas directamente. Tus funciones en `tools.py` se convierten en herramientas que cualquier cliente MCP puede invocar.

### Proyecto 4 — Multi-agente

Añades un segundo agente (ej: "Competitor Research Agent") que corre en paralelo con el research principal. Usas `asyncio` para coordinarlos. El estado compartido que ya diseñaste es la interfaz entre agentes.

---

## Principios que debes poder recitar al terminar

1. **El estado es la memoria del workflow.** Si no está en el estado, no existe para el sistema.

2. **Las tools transforman estado, no lo consultan.** Reciben estado completo, devuelven estado actualizado.

3. **El routing es lógica, no datos.** Vive separado de las tools y del estado.

4. **Los LLMs son herramientas, no la arquitectura.** Puedes reemplazar OpenAI con cualquier otro LLM sin cambiar la estructura del workflow.

5. **La observabilidad no es opcional.** Un sistema que no puedes debuggear en producción es un sistema roto.

6. **Los tests no llaman al LLM.** Testeas tu lógica, no el comportamiento del modelo.

# Challenge_Alura_OCI

Asistente de atención al cliente para BimBam Buy construido con FastAPI, LangChain y una interfaz web estática. El sistema responde consultas sobre envíos, garantías, reembolsos, devoluciones y métodos de pago usando únicamente la información contenida en los documentos internos del proyecto.

## Descripción general

Este proyecto implementa un agente de soporte que recibe preguntas en lenguaje natural, clasifica la intención del usuario y decide entre resolver con recuperación de información desde documentos internos, pedir más contexto o abrir un ticket lógico. La experiencia de usuario se ofrece desde una interfaz web conversacional con sugerencias de preguntas y estado de conexión.

El conocimiento del asistente se alimenta desde los PDFs ubicados en `docs_bimbambuy/`, que incluyen:

- Guía de Tiempos y Costos de Envío de BimBam Buy.
- Manual de Garantía de Productos de BimBam Buy.
- Política de Reembolsos y Devoluciones de BimBam Buy.
- Preguntas Frecuentes sobre Métodos de Pago de BimBam Buy.
- Programa de Afiliados de BimBam Buy.

## Arquitectura de la solución

La solución está compuesta por dos capas principales:

### Frontend

- `index.html`: estructura de la interfaz.
- `styles.css`: estilos visuales, layout responsivo y componentes del chat.
- `script.js`: lógica del chat, sugerencias, envío de preguntas y consumo del backend.

### Backend e inteligencia

- `app.py`: expone la API con FastAPI, sirve el frontend y atiende `POST /preguntar`.
- `challenge_oci.py`: contiene la lógica del agente.
- `docs_bimbambuy/`: repositorio de documentos internos usados como base de conocimiento.

### Flujo de procesamiento

1. El usuario escribe una pregunta en la interfaz.
2. El frontend la envía al endpoint `POST /preguntar`.
3. El backend ejecuta un triaje inicial para decidir la estrategia.
4. Si la consulta es resoluble, el motor RAG busca contexto en los PDFs.
5. La respuesta se genera solo con información interna.
6. Si no hay evidencia suficiente, el sistema responde con `No lo sé` o solicita más información.

## Tecnologías y herramientas utilizadas

- Python.
- FastAPI.
- Uvicorn.
- LangChain.
- LangGraph.
- Cohere (`ChatCohere` y `CohereEmbeddings`).
- FAISS para búsqueda vectorial.
- PyMuPDF para lectura de PDFs.
- `python-dotenv` para variables de entorno.
- HTML, CSS y JavaScript puro.
- Bootstrap 5 para componentes responsivos.

## Instrucciones para ejecutar el proyecto

### Requisitos previos

- Python 3.10 o superior.
- Una clave válida de Cohere configurada en la variable de entorno `COHERE_API_KEY`.

### Instalación

```bash
pip install -r requirements.txt
```

### Configuración

1. Crea un archivo `.env` en la raíz del proyecto.
2. Agrega tu clave de Cohere:

```env
COHERE_API_KEY=tu_clave_aqui
```

### Ejecución local

```bash
uvicorn app:app --reload
```

Luego abre en el navegador:

```text
http://127.0.0.1:8000
```

## Ejemplos de preguntas que el agente puede responder

- ¿Cuáles son los tipos de envíos disponibles?
- ¿Cuál es la cobertura general de la garantía?
- ¿Cuánto tiempo tengo para solicitar un reembolso?
- ¿Cuáles son los métodos de pago disponibles?
- ¿Qué información necesito para iniciar una devolución?

## Ejemplos de respuestas generadas por el agente

- `No lo sé` cuando la información no está en los documentos internos.
- Respuestas informativas sobre plazos, cobertura, medios de pago o condiciones de envío cuando el contenido sí está documentado.
- Mensajes de solicitud de más contexto cuando la consulta es ambigua o incompleta.
- Mensajes de apertura de ticket cuando el usuario solicita una excepción o autorización especial.

Ejemplos:

- Pregunta: ¿Cuánto tiempo tengo para pedir un reembolso?
	- Respuesta esperada: una explicación basada en la política de reembolsos del documento interno.
- Pregunta: ¿Puedo pedir una excepción para mi caso?
	- Respuesta esperada: derivación a apertura de ticket.
- Pregunta: ¿Quién fue Napoleón Bonaparte?
	- Respuesta esperada: `No lo sé`.

## Despliegue

La aplicación fue desplegada en Render.

URL de la aplicación desplegada:

- [https://challenge-alura-oci.onrender.com](https://challenge-alura-oci.onrender.com)

## Capturas y video y demo

### Capturas

- ![Captura del despliegue en Render](./docs_readme/Captura%20de%20pantalla%202026-07-22%20203134.png)

### Video

- [Ver video de demostración](./docs_readme/Grabación%20de%20pantalla%202026-07-22%20203632.mp4)

## Estructura del proyecto

```text
.
├── app.py
├── challenge_oci.py
├── index.html
├── README.md
├── requirements.txt
├── script.js
├── styles.css
└── docs_bimbambuy/
```

## Notas

- El asistente responde solo con base en los documentos internos cargados.
- Si la información no existe en la base documental, el sistema prioriza no inventar respuestas.
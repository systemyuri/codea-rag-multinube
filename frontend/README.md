# CODEA – Frontend (React)

Este es el frontend de **CODEA**, un asistente legal ciudadano que responde preguntas sobre pensión de alimentos en Perú, utilizando un sistema RAG (Retrieval-Augmented Generation) distribuido en tres nubes.

## 🧠 Tecnologías utilizadas

- **React 18** (con Vite como bundler)
- **Material-UI (MUI)** – componentes visuales modernos y accesibles.
- **React Markdown + remark-gfm** – renderizado de respuestas con formato Markdown.
- **Azure Static Web Apps** – alojamiento serverless con integración continua.

## 📋 Requisitos previos

- **Node.js** versión 18 o superior (recomendado 20 LTS)
- **npm** o **yarn**
- (Opcional) **Azure CLI** para despliegue automatizado con `az`
- (Opcional) **Azure Static Web Apps CLI** (`swa`) para despliegue con token

## Estructura del proyecto
```text
frontend/
├── public/               # Archivos estáticos (favicon, etc.)
├── src/
│   ├── components/       # Componentes reutilizables
│   ├── pages/            # Vistas principales
│   ├── hooks/            # Custom hooks
│   ├── services/         # Llamadas a la API
│   ├── styles/           # Estilos globales
│   ├── App.jsx
│   └── main.jsx
├── .env.example          # Ejemplo de variables de entorno
├── index.html
├── package.json
├── vite.config.js        # Configuración de Vite
└── README.md
```

## ⬇️ Descarga e instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/codea-rag.git
cd codea-rag/frontend
```

### 2. Instalar dependencias
```bash
npm install
```

### 3. Configurar variables de entorno
```env
VITE_API_BASE_URL=https://tu-backend.azurewebsites.net/api
VITE_APP_TITLE=CODEA Asistente Legal
```
Nota: Las variables deben llevar el prefijo VITE_ para que Vite las exponga al frontend. Ajusta las URLs según tu entorno (local, desarrollo, producción).

### 4. Ejecutar localmente
```bash
npm run dev
```


### 5. Compilacion
```bash
npm run build
```

### 6. Despliegue en la nube
Instalar CLI globalmente:
```bash
npm install -g @azure/static-web-apps-cli
```

Luego, desde la raíz del proyecto (donde está el frontend), ejecuta:
```bash
swa deploy ./dist --env production --deployment-token <TU_TOKEN>
```
El token de despliegue lo encuentras en la sección Overview de tu Static Web App en Azure Portal


## ⬇️ DESPLIEGUE AUTOMATICO


### Cómo usarlo
1.  Ubicar el archivo dentro del repositorio frontend **deploy.sh** 
    

2.  Ejecutar los siguientes comandos desde **git bash**:
```bash
export DEPLOYMENT_TOKEN="TU TOKEN DE STATIC WEB APP DE AZURE"

chmod +x deploy.sh

./deploy.sh
```
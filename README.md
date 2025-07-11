# TFG - Predicción de Resultados de Tenis con Deep Learning

## Descripción del Proyecto

Este proyecto de Trabajo Final de Grado (TFG) desarrolla un sistema de predicción de resultados de partidos de tenis utilizando técnicas de Deep Learning. El sistema combina múltiples fuentes de datos para entrenar redes neuronales recurrentes que pueden predecir tanto el ganador de un partido como las probabilidades ofrecidas por la casa de apuestas. 

## Estructura del Proyecto

```
├── 1.ranking.py              # Obtención y procesamiento de rankings ATP
├── 2.scrapper.py             # Web scraping de datos de partidos
├── 3.analisis_descriptivo.ipynb    # Análisis exploratorio de datos
├── 4.preprocesamiento.ipynb        # Limpieza y preparación de datos
├── 5.prediccion.ipynb              # Entrenamiento de modelos
├── 6.analisis_resultados.ipynb     # Evaluación y visualización de resultados
└── README.md                       
```

## Flujo de procesamiento de los datos

### 1. Recolección de Datos (`1.ranking.py`, `2.scrapper.py`)

- **Rankings ATP**: Obtención de rankings históricos desde la API de Matchstat mediante CloudScraper
- **Datos de partidos**: Web scraping de resultados, estadísticas y odds de apuestas
- **Información de jugadores**: Edad, nacionalidad, superficie preferida

### 2. Análisis Exploratorio (`3.analisis_descriptivo.ipynb`)

- Distribución de partidos por torneo y superficie
- Análisis de rankings y probabilidades de apuesta
- Identificación de patrones temporales

### 3. Preprocesamiento (`4.preprocesamiento.ipynb`)

- **Limpieza de datos**: Eliminación de valores anómalos y partidos incompletos
- **Transformaciones**: 
  - Rankings en escala logarítmica diferencial
  - Normalización de probabilidades de apuesta (corrección del vigorish)
  - Codificación de variables categóricas
- **Estructuración temporal**: Organización en ventanas deslizantes

### 4. Modelado (`5.prediccion.ipynb`)

- **Arquitectura dual**: Modelo de clasificación y regresión
- **Entrenamiento con ventanas temporales**: 143 ventanas de validación cruzada
- **Transfer Learning**: Transferencia de pesos entre ventanas temporales
- **Early Stopping**: Prevención de sobreajuste

### 5. Evaluación (`6.analisis_resultados.ipynb`)

- **Métricas de clasificación**: Accuracy, Precision, Recall, F1-Score, AUC
- **Métricas de regresión**: MAE, MSE, RMSE, R²
- **Análisis temporal**: Evolución del rendimiento por período
- **Comparación con benchmarks**: Casas de apuestas

## Tecnologías Utilizadas

### ML/DL
- **PyTorch**: Framework principal para redes neuronales
- **Scikit-learn**: Métricas y preprocesamiento
- **NumPy/Pandas**: Manipulación de datos

### Web Scraping
- **requests**: Peticiones HTTP
- **cloudscraper**: Evita protecciones anti-bot para Matchstat
- **rapidfuzz**: Matching difuso de nombres

### Visualización
- **Matplotlib**: Gráficos estáticos
- **Seaborn**: Visualizaciones estadísticas

### APIs
- **Sofascore API**: Principal fuente de información
- **MatchStat API**: Datos de partidos y rankings

## Instrucciones de Uso

### Prerrequisitos
Necesario tener instalado Python 3.11.
```bash
pip install torch pandas numpy scikit-learn matplotlib seaborn requests cloudscraper rapidfuzz
```

### Ejecución Completa

1. **Recolección de datos**:
   ```bash
   python 1.ranking.py
   python 2.scrapper.py
   ```

2. **Análisis y preprocesamiento**:
   - Ejecutar `3.analisis_descriptivo.ipynb`
   - Ejecutar `4.preprocesamiento.ipynb`

3. **Entrenamiento**:
   - Ejecutar `5.prediccion.ipynb`

4. **Evaluación**:
   - Ejecutar `6.analisis_resultados.ipynb`

## Contribuciones

**Autor**: Diego Rodríguez  
**Tutor**: Francisco Hernando Gallego
**Institución**: Universidad de Valladolid



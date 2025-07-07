# TFG - Predicción de Resultados de Tenis con Deep Learning

## Descripción del Proyecto

Este proyecto de Trabajo Final de Grado (TFG) desarrolla un sistema de predicción de resultados de partidos de tenis utilizando técnicas de Deep Learning. El sistema combina múltiples fuentes de datos para entrenar redes neuronales recurrentes (GRU) que pueden predecir tanto el ganador de un partido como las probabilidades de apuesta.

## Arquitectura del Sistema

### Modelo de Red Neuronal

El proyecto utiliza una arquitectura híbrida que combina:

- **Redes GRU (Gated Recurrent Unit)**: Para procesar secuencias temporales de datos históricos
- **Capas Dense**: Para procesar características contextuales del partido
- **Arquitectura dual**: Separación de datos históricos por jugador (local/visitante)

### Características del Modelo

- **Input temporal**: Secuencias de 50 partidos previos por jugador
- **Input contextual**: Rankings, superficie, tipo de torneo, etc.
- **Output dual**: Clasificación binaria (ganador) y regresión (probabilidades)
- **Técnicas de regularización**: Dropout, Early Stopping, Transfer Learning

## 📁 Estructura del Proyecto

```
├── 1.ranking.py              # Obtención y procesamiento de rankings ATP
├── 2.scrapper.py             # Web scraping de datos de partidos
├── 3.analisis_descriptivo.ipynb    # Análisis exploratorio de datos
├── 4.preprocesamiento.ipynb        # Limpieza y preparación de datos
├── 5.prediccion.ipynb              # Entrenamiento de modelos
├── 6.analisis_resultados.ipynb     # Evaluación y visualización de resultados
└── README.md                       
```

## 🔄 Pipeline de Datos

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

## 📈 Resultados Principales

### Modelo de Clasificación
- **Accuracy promedio**: ~65%
- **AUC promedio**: ~67%
- **F1-Score promedio**: ~65%

### Modelo de Regresión (Probabilidades)
- **R² promedio**: ~80%
- **MAE promedio**: 0.065

### Insights Clave
- El modelo supera la precisión base del 50% de manera consistente
- Mayor precisión en torneos de Grand Slam vs. torneos menores
- Rendimiento estable a lo largo de diferentes períodos temporales

## 🛠️ Tecnologías Utilizadas

### ML/DL
- **PyTorch**: Framework principal para redes neuronales
- **Scikit-learn**: Métricas y preprocessing
- **NumPy/Pandas**: Manipulación de datos

### Web Scraping
- **requests**: Peticiones HTTP
- **cloudscraper**: Bypass de protecciones anti-bot para Matchstat
- **rapidfuzz**: Matching difuso de nombres

### Visualización
- **Matplotlib**: Gráficos estáticos
- **Seaborn**: Visualizaciones estadísticas

### APIs
- **Sofascore API**: Principal fuente de información
- **MatchStat API**: Datos de partidos y rankings

## 🚀 Instrucciones de Uso

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

## 🎓 Contexto Académico

Este proyecto forma parte de un Trabajo Final de Grado, específicamente enfocado en:

- **Machine Learning aplicado**: Implementación práctica de redes neuronales
- **Análisis de series temporales**: Modelado de datos secuenciales
- **Estadística deportiva**: Aplicación de métodos cuantitativos al tenis
- **Ingeniería de datos**: Pipeline completo desde datos raw hasta modelo

## 👥 Contribuciones

**Autor**: Diego Rodríguez  
**Supervisor**: Francisco Hernando Gallego
**Institución**: Universidad de Valladolid

## 🔗 Referencias

- **Datos**: MatchStat.com, Sofascore.com
- **Arquitecturas**: Investigación en RNNs para predicción deportiva
- **Benchmarks**: Literatura académica en predicción de tenis



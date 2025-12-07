import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
from modelos import PredictorDesempeno
import io
from datetime import datetime, timedelta


# === AGREGAR ESTE IMPORT ===
from auth import verificar_autenticacion, mostrar_logout

warnings.filterwarnings('ignore')

# Configurar página
st.set_page_config(
    page_title="Sistema de Monitoreo Estudiantil por Semanas",
    page_icon="🎓",
    layout="wide"
)

# === AGREGAR ESTA LÍNEA AQUÍ - DESPUÉS DE set_page_config ===
verificar_autenticacion()

# Inicializar predictor
@st.cache_resource
def cargar_predictor():
    return PredictorDesempeno()

predictor = cargar_predictor()

# Listas globales que se actualizarán con datos reales
ESTUDIANTES = []
CURSOS = []

def actualizar_listas_desde_dataframe(df):
    """Actualiza las listas de estudiantes y cursos desde el DataFrame cargado"""
    global ESTUDIANTES, CURSOS
    
    if 'Alumno' in df.columns:
        ESTUDIANTES = sorted(df['Alumno'].unique().tolist())
    elif 'Estudiante' in df.columns:
        ESTUDIANTES = sorted(df['Estudiante'].unique().tolist())
    elif 'Nombre' in df.columns:
        ESTUDIANTES = sorted(df['Nombre'].unique().tolist())
    elif 'Student' in df.columns:
        ESTUDIANTES = sorted(df['Student'].unique().tolist())
    
    # Identificar columnas de cursos automáticamente
    columnas_excluir = ['ID_Estudiante', 'Alumno', 'Estudiante', 'Nombre', 'Student', 'Semana', 
                       'Fecha Inicio', 'Fecha Fin', 'Clases Asistidas', 'Clases Totales', 
                       'Promedio', 'Asistencia (%)', 'Promedio_Anterior', 
                       'Progreso Académico (%)', 'Desempeño academico', 'en_riesgo']
    
    posibles_cursos = []
    for col in df.columns:
        if col not in columnas_excluir:
            # Verificar si la columna contiene datos numéricos (notas)
            if pd.api.types.is_numeric_dtype(df[col]):
                posibles_cursos.append(col)
            # Si no es numérica, verificar si puede convertirse
            else:
                try:
                    # Intentar convertir a numérico
                    temp_series = pd.to_numeric(df[col], errors='coerce')
                    if not temp_series.isna().all():  # Si al menos algunos valores son numéricos
                        posibles_cursos.append(col)
                except:
                    continue
    
    if posibles_cursos:
        CURSOS = posibles_cursos
    else:
        # Si no se detectan cursos, usar los predeterminados
        CURSOS = [
            'Comunicación', 'Matemática', 'Ciencia y Tecnología',
            'Personal Social', 'Educación Religiosa', 'Educación Física',
            'Arte', 'Inglés'
        ]

def formatear_fechas_df(df):
    """Convierte las fechas al formato día/mes/año"""
    columnas_fecha = ['Fecha Inicio', 'Fecha Fin']
    
    for col in columnas_fecha:
        if col in df.columns:
            # Para CSV, las fechas vienen como texto, intentar parsear
            try:
                # Primero detectar el formato original y convertir a datetime
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
            except:
                # Si falla, intentar otro método
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y')
                except:
                    pass
    return df

def calcular_metricas(df):
    """Calcula métricas automáticamente"""
    # Convertir columnas de cursos a numérico si es necesario
    for curso in CURSOS:
        if curso in df.columns:
            df[curso] = pd.to_numeric(df[curso], errors='coerce').fillna(0)
    
    # Calcular promedio si hay cursos definidos
    if CURSOS and all(curso in df.columns for curso in CURSOS):
        df['Promedio'] = df[CURSOS].mean(axis=1).round(2)
    else:
        st.error("No se pudieron identificar las columnas de cursos")
        return df
    
    # Calcular asistencia si las columnas existen
    if 'Clases Asistidas' in df.columns and 'Clases Totales' in df.columns:
        df['Asistencia (%)'] = (df['Clases Asistidas'] / df['Clases Totales'] * 100).round(2)
    elif 'Asistencia' in df.columns:
        df['Asistencia (%)'] = df['Asistencia'].round(2)
    
    # Calcular progreso académico (comparando con semana anterior)
    if 'ID_Estudiante' in df.columns and 'Semana' in df.columns:
        df = df.sort_values(['ID_Estudiante', 'Semana'])
        df['Promedio_Anterior'] = df.groupby('ID_Estudiante')['Promedio'].shift(1)
        
        # Calcular progreso evitando divisiones por cero
        def calcular_progreso(row):
            if pd.isna(row['Promedio_Anterior']) or row['Promedio_Anterior'] == 0:
                return 0
            rango_posible = 20
            return ((row['Promedio'] - row['Promedio_Anterior']) / rango_posible * 100)
        
        df['Progreso Académico (%)'] = df.apply(calcular_progreso, axis=1).round(2)
    
    # Determinar desempeño académico
    condiciones = [
        df['Promedio'] >= 16,
        df['Promedio'] >= 14,
        df['Promedio'] >= 11,
        df['Promedio'] < 11
    ]
    opciones = ['Excelente', 'Bueno', 'Regular', 'En Riesgo']
    df['Desempeño academico'] = np.select(condiciones, opciones, default='Regular')
    
    return df

def generar_datos_ejemplo():
    """Genera datos de ejemplo para 36 semanas - ACTUALIZADO A 2025"""
    global ESTUDIANTES, CURSOS
    
    # Si no hay estudiantes definidos, usar los predeterminados
    if not ESTUDIANTES:
        ESTUDIANTES = [
            "Adriana Beatriz León Vargas", "Ariana Michelle León Cordero",
            "Andrés Felipe Guerrero Soto", "Camila Estefanía Salazar Vega",
            "Carlos Andrés Herrera Medina", "Carmen Rosa Méndez Fuentes",
            "Dafne Isabel Castro Díaz", "Daniela Estefanía Vásquez Ruiz",
            "Diana Sofia Campos Díaz", "Eduardo Enrique Prado Jiménez",
            "Felipe Augusto Espinoza Torres", "Gabriela Isabel Ríos Medina",
            "Gisela Emilia Contreras Mendizábal", "Hugo Francisco Mendoza Rojas",
            "Jorge Eduardo Salazar Peña", "José Antonio Díaz Romero",
            "Juan Carlos Morales Miranda", "Laura Valentina Paredes Silva",
            "Luciana Andrea Vásquez Romero", "Luis Alberto García Pérez",
            "Magdalena Alejandra Torres Mendoza", "María Fernanda Gutiérrez Rojas",
            "Naomi Emilia Cervantes Herrera", "Natalia Eugenia Chávez Herrera",
            "Pablo Daniel Cabrera Luna", "Paula Renata Gómez Silva",
            "Renata Alejandra Olivos Díaz", "Ricardo José Navarro Campos",
            "Sofía Camila Gutiérrez Salazar", "Sonia Valentina Quispe López",
            "Valeria Alejandra Paredes Flores"
        ]
    
    if not CURSOS:
        CURSOS = [
            'Comunicación', 'Matemática', 'Ciencia y Tecnología',
            'Personal Social', 'Educación Religiosa', 'Educación Física',
            'Arte', 'Inglés'
        ]
    
    np.random.seed(42)
    datos = []
    
    # FECHA ACTUALIZADA A 2025
    fecha_base = datetime(2025, 4, 14)  
    
    for i, estudiante in enumerate(ESTUDIANTES, 1):
        promedio_base = np.random.normal(13, 2)
        
        for semana in range(1, 37):  # 36 semanas
            # Calcular fecha (cada semana empieza en lunes)
            fecha_inicio = fecha_base + timedelta(weeks=semana-1)
            fecha_fin = fecha_inicio + timedelta(days=6)
            
            # Generar notas con tendencia
            if i % 5 == 0:  # Estudiantes en riesgo
                tendencia = np.random.choice([-0.1, -0.2, 0], p=[0.6, 0.3, 0.1])
            else:
                tendencia = np.random.choice([0.1, 0.05, 0], p=[0.5, 0.3, 0.2])
            
            notas = []
            for curso in range(len(CURSOS)):
                nota_base = max(0, min(20, promedio_base + np.random.normal(0, 1)))
                # Aplicar tendencia progresiva
                nota_ajustada = nota_base + (tendencia * semana)
                notas.append(max(0, min(20, round(nota_ajustada, 1))))
            
            promedio = np.mean(notas)
            clases_totales = 20
            # Asistencia con tendencia
            if i % 5 == 0:
                clases_asistidas = max(10, np.random.randint(12, 18))
            else:
                clases_asistidas = np.random.randint(16, 21)
            
            asistencia = (clases_asistidas / clases_totales) * 100
            
            datos.append({
                'ID_Estudiante': i,
                'Alumno': estudiante,
                'Semana': semana,
                'Fecha Inicio': fecha_inicio.strftime('%d/%m/%Y'),
                'Fecha Fin': fecha_fin.strftime('%d/%m/%Y'),
                **dict(zip(CURSOS, notas)),
                'Clases Asistidas': clases_asistidas,
                'Clases Totales': clases_totales
            })
    
    df = pd.DataFrame(datos)
    return calcular_metricas(df)

def mostrar_dashboard_general(df):
    st.header("📊 Dashboard General - Visión Semanal")
    
    if df.empty:
        st.warning("No hay datos disponibles")
        return
    
    # Mostrar información sobre los datos cargados
    if 'Alumno' in df.columns and len(df['Alumno'].unique()) > 0:
        st.info(f"📁 Datos cargados: {len(df)} registros, {len(ESTUDIANTES)} estudiantes, {len(CURSOS)} cursos")
    else:
        st.info(f"📁 Usando datos de ejemplo: {len(df)} registros, {len(ESTUDIANTES)} estudiantes, {len(CURSOS)} cursos")
    
    # Selector de semana para el dashboard
    semanas_disponibles = sorted(df['Semana'].unique())
    semana_seleccionada = st.selectbox("Seleccionar Semana para Dashboard", semanas_disponibles)
    
    datos_semana = df[df['Semana'] == semana_seleccionada]
    
    # Métricas generales de la semana seleccionada - CORREGIDAS
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        promedio_general = datos_semana['Promedio'].mean()
        st.metric(f"Promedio General Semana {semana_seleccionada}", f"{promedio_general:.1f}")
    
    with col2:
        asistencia_promedio = datos_semana['Asistencia (%)'].mean()
        st.metric("Asistencia Promedio", f"{asistencia_promedio:.1f}%")
    
    with col3:
        estudiantes_riesgo = len(datos_semana[datos_semana['Desempeño academico'] == 'En Riesgo'])
        st.metric("Estudiantes en Riesgo", estudiantes_riesgo)
    
    with col4:
        # CORRECCIÓN: Evitar NaN en progreso promedio
        progreso_promedio = datos_semana['Progreso Académico (%)'].mean()
        if pd.isna(progreso_promedio):
            progreso_promedio = 0
        st.metric("Progreso Promedio", f"{progreso_promedio:.1f}%")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de desempeño por semana
        fig_desempeno = px.pie(
            datos_semana, 
            names='Desempeño academico',
            title=f'Distribución del Desempeño - Semana {semana_seleccionada}',
            color='Desempeño academico',
            color_discrete_map={
                'Excelente': '#00CC96',
                'Bueno': '#636EFA',
                'Regular': '#FECB52',
                'En Riesgo': '#EF553B'
            }
        )
        st.plotly_chart(fig_desempeno)
    
    with col2:
        # Evolución de promedios por semana (todas las semanas)
        evolucion_promedio = df.groupby('Semana').agg({
            'Promedio': 'mean',
            'Asistencia (%)': 'mean'
        }).reset_index()
        
        fig_evolucion = go.Figure()
        fig_evolucion.add_trace(go.Scatter(
            x=evolucion_promedio['Semana'],
            y=evolucion_promedio['Promedio'],
            mode='lines+markers',
            name='Promedio General',
            line=dict(color='#636EFA', width=3)
        ))
        fig_evolucion.add_vline(x=semana_seleccionada, line_dash="dash", line_color="red")
        fig_evolucion.update_layout(
            title='Evolución del Promedio General por Semana',
            xaxis_title='Semana',
            yaxis_title='Promedio'
        )
        st.plotly_chart(fig_evolucion)
    
    # Top 5 estudiantes de la semana
    st.subheader(f"🏆 Top 5 Estudiantes - Semana {semana_seleccionada}")
    top_estudiantes = datos_semana.nlargest(5, 'Promedio')[['Alumno', 'Promedio', 'Asistencia (%)', 'Desempeño academico']]
    st.dataframe(top_estudiantes, use_container_width=True)

def mostrar_monitoreo_semanal(df):
    st.header("👨‍🎓 Monitoreo Detallado por Semana")
    
    if df.empty:
        st.warning("No hay datos disponibles")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Selector de semana
        semanas_disponibles = sorted(df['Semana'].unique())
        semana_seleccionada = st.selectbox("Seleccionar Semana", semanas_disponibles)
    
    with col2:
        # Selector de estudiante
        estudiante_seleccionado = st.selectbox("Seleccionar Estudiante", ESTUDIANTES)
    
    if estudiante_seleccionado and semana_seleccionada:
        # Datos del estudiante en la semana seleccionada
        datos_estudiante = df[(df['Alumno'] == estudiante_seleccionado) & 
                             (df['Semana'] == semana_seleccionada)]
        
        if not datos_estudiante.empty:
            datos_semana = datos_estudiante.iloc[0]
            
            st.subheader(f"📋 Reporte de la Semana {semana_seleccionada}")
            st.write(f"**Período:** {datos_semana['Fecha Inicio']} al {datos_semana['Fecha Fin']}")
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Promedio Semanal", f"{datos_semana['Promedio']:.1f}")
            
            with col2:
                st.metric("Asistencia", f"{datos_semana['Asistencia (%)']:.1f}%")
            
            with col3:
                progreso = datos_semana['Progreso Académico (%)']
                if pd.isna(progreso):
                    progreso = 0
                color_progreso = "green" if progreso > 0 else "red"
                st.metric("Progreso Académico", 
                         f"{progreso:.1f}%",
                         delta=f"{progreso:.1f}%")
            
            with col4:
                desempeno_color = {
                    'Excelente': '🟢',
                    'Bueno': '🔵', 
                    'Regular': '🟡',
                    'En Riesgo': '🔴'
                }
                st.metric("Desempeño", 
                         f"{desempeno_color[datos_semana['Desempeño academico']]} {datos_semana['Desempeño academico']}")
            
            # Gráficos detallados
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de barras de notas por curso
                if all(curso in datos_semana for curso in CURSOS):
                    notas_curso = [datos_semana[curso] for curso in CURSOS]
                    fig_notas = px.bar(
                        x=CURSOS, 
                        y=notas_curso,
                        title=f'Notas por Curso - Semana {semana_seleccionada}',
                        labels={'x': 'Curso', 'y': 'Nota'},
                        color=notas_curso,
                        color_continuous_scale='Viridis'
                    )
                    fig_notas.add_hline(y=11, line_dash="dash", line_color="red", annotation_text="Límite Aprobación")
                    fig_notas.update_layout(showlegend=False)
                    st.plotly_chart(fig_notas)
                else:
                    st.warning("No se encontraron datos de cursos para mostrar")
            
            with col2:
                # Comparativa con semanas anteriores
                historial_estudiante = df[df['Alumno'] == estudiante_seleccionado].sort_values('Semana')
                fig_historial = px.line(
                    historial_estudiante,
                    x='Semana',
                    y='Promedio',
                    title='Evolución del Promedio',
                    markers=True
                )
                fig_historial.add_hline(y=11, line_dash="dash", line_color="red", annotation_text="Límite Aprobación")
                fig_historial.add_vline(x=semana_seleccionada, line_dash="dash", line_color="green")
                st.plotly_chart(fig_historial)
            
            # Tabla detallada de calificaciones
            if all(curso in datos_semana for curso in CURSOS):
                st.subheader("📊 Calificaciones Detalladas")
                datos_detallados = {
                    'Curso': CURSOS,
                    'Nota': [datos_semana[curso] for curso in CURSOS],
                    'Estado': ['✅ Aprobado' if datos_semana[curso] >= 11 else '❌ Riesgo' for curso in CURSOS]
                }
                df_detallado = pd.DataFrame(datos_detallados)
                st.dataframe(df_detallado, use_container_width=True)
            
        else:
            st.warning(f"No hay datos disponibles para {estudiante_seleccionado} en la semana {semana_seleccionada}")

def mostrar_prediccion_riesgo(df):
    st.header("🔮 Predicción de Riesgo Académico")
    
    # Verificar si los modelos están entrenados
    if not predictor.entrenado and not df.empty:
        if st.button("🔧 Entrenar Modelos con Datos Actuales"):
            with st.spinner("Entrenando modelos de IA..."):
                resultados = predictor.entrenar_modelos(df)
                if resultados:
                    st.success("✅ Modelos entrenados exitosamente!")
                    st.rerun()
    
    if not predictor.entrenado:
        st.warning("""
        ⚠️ **Los modelos de predicción necesitan ser entrenados primero**
        
        Para usar la predicción:
        1. Ve a 'Dashboard General' y haz clic en 'Entrenar Modelos'
        2. O carga un archivo Excel con datos históricos
        3. O usa el botón de arriba para entrenar con datos actuales
        """)
        return
    
    st.markdown("### Ingresar Datos del Estudiante para Predicción")
    
    # Usar session_state para mantener los datos
    if 'notas_manuales' not in st.session_state:
        st.session_state.notas_manuales = {curso: 12.0 for curso in CURSOS}
    if 'asistencia_manual' not in st.session_state:
        st.session_state.asistencia_manual = 85.0
    if 'resultado_prediccion' not in st.session_state:
        st.session_state.resultado_prediccion = None
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 Datos Académicos")
        
        # Selector de estudiante (solo para referencia)
        estudiante_referencia = st.selectbox("Estudiante (para referencia)", ESTUDIANTES, key="pred_ref")
        
        st.markdown("#### Ingresar Calificaciones (0-20)")
        
        # Crear inputs para cada curso
        notas_actualizadas = {}
        cols_notas = st.columns(4)
        
        for i, curso in enumerate(CURSOS):
            with cols_notas[i % 4]:
                nota = st.number_input(
                    f"{curso}",
                    min_value=0.0,
                    max_value=20.0,
                    value=st.session_state.notas_manuales[curso],
                    step=0.5,
                    key=f"nota_{curso}"
                )
                notas_actualizadas[curso] = nota
                st.session_state.notas_manuales[curso] = nota
        
        # Actualizar el diccionario de notas
        st.session_state.notas_manuales.update(notas_actualizadas)
    
    with col2:
        st.subheader("📈 Métricas Adicionales")
        
        # Asistencia
        asistencia = st.slider(
            "Porcentaje de Asistencia (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.asistencia_manual,
            step=1.0,
            key="asistencia_pred"
        )
        st.session_state.asistencia_manual = asistencia
        
        # Progreso académico
        progreso = st.slider(
            "Progreso Académico (%)",
            min_value=-50.0,
            max_value=50.0,
            value=0.0,
            step=1.0,
            key="progreso_pred"
        )
        
        # Mostrar resumen de notas ingresadas
        st.markdown("#### Resumen de Calificaciones Ingresadas")
        promedio_manual = np.mean(list(st.session_state.notas_manuales.values()))
        
        col_met1, col_met2 = st.columns(2)
        with col_met1:
            st.metric("Promedio Calculado", f"{promedio_manual:.1f}")
        with col_met2:
            st.metric("Asistencia", f"{asistencia:.1f}%")
        
        # Gráfico rápido de notas
        fig_barras = px.bar(
            x=list(st.session_state.notas_manuales.keys()),
            y=list(st.session_state.notas_manuales.values()),
            title="Distribución de Notas Ingresadas",
            labels={'x': 'Curso', 'y': 'Nota'}
        )
        fig_barras.add_hline(y=11, line_dash="dash", line_color="red", annotation_text="Límite Aprobación")
        st.plotly_chart(fig_barras, use_container_width=True)
    
    # Botón de predicción
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    
    with col_btn2:
        if st.button("🎯 REALIZAR PREDICCIÓN DE RIESGO", use_container_width=True, type="primary"):
            with st.spinner("Analizando desempeño del estudiante..."):
                # Preparar datos para predicción
                notas_lista = [st.session_state.notas_manuales[curso] for curso in CURSOS]
                
                # Realizar predicción
                resultado = predictor.predecir_riesgo_manual(
                    notas_lista, 
                    asistencia, 
                    progreso
                )
                
                st.session_state.resultado_prediccion = resultado
    
    # Mostrar resultados de la predicción
    if st.session_state.resultado_prediccion and 'error' not in st.session_state.resultado_prediccion:
        st.markdown("---")
        st.header("📊 RESULTADOS DE LA PREDICCIÓN")
        
        resultado = st.session_state.resultado_prediccion
        
        # Alertas de desempeño
        col_res1, col_res2, col_res3 = st.columns(3)
        
        with col_res1:
            if resultado['nivel_desempeno'] == "ALTO":
                st.success(f"## {resultado['color_desempeno']} DESEMPEÑO ALTO")
            elif resultado['nivel_desempeno'] == "MEDIO":
                st.warning(f"## {resultado['color_desempeno']} DESEMPEÑO MEDIO")
            else:
                st.error(f"## {resultado['color_desempeno']} DESEMPEÑO BAJO")
        
        with col_res2:
            st.metric("Promedio General", f"{resultado['promedio']:.1f}")
        
        with col_res3:
            if resultado['en_riesgo']:
                st.error("## 🚨 RIESGO DE REPROBAR")
            else:
                st.success("## ✅ PROBABLE APROBACIÓN")
        
        # Detalles de la predicción
        st.subheader("🤖 Análisis Detallado por Algoritmo")
        
        col_alg1, col_alg2, col_alg3 = st.columns(3)
        
        predicciones = resultado['predicciones_individuales']
        
        with col_alg1:
            algo = 'arbol'
            pred = predicciones[algo]
            emoji = "🔴" if pred['prediccion'] else "🟢"
            st.metric(
                f"Árbol de Decisión", 
                f"{emoji} {'Riesgo' if pred['prediccion'] else 'Seguro'}",
                f"Conf: {pred['confianza']:.1%}"
            )
        
        with col_alg2:
            algo = 'svm'
            pred = predicciones[algo]
            emoji = "🔴" if pred['prediccion'] else "🟢"
            st.metric(
                f"SVM", 
                f"{emoji} {'Riesgo' if pred['prediccion'] else 'Seguro'}",
                f"Conf: {pred['confianza']:.1%}"
            )
        
        with col_alg3:
            algo = 'knn'
            pred = predicciones[algo]
            emoji = "🔴" if pred['prediccion'] else "🟢"
            st.metric(
                f"KNN", 
                f"{emoji} {'Riesgo' if pred['prediccion'] else 'Seguro'}",
                f"Conf: {pred['confianza']:.1%}"
            )
        
        # Confianza general
        st.metric("Confianza General del Sistema", f"{resultado['confianza_general']:.1%}")
        
        # Recomendaciones
        st.subheader("💡 Recomendaciones y Acciones")

        for recomendacion in resultado['recomendaciones']:
            if recomendacion.startswith("🚨"):
                st.error(recomendacion)
            elif recomendacion.startswith("🎉"):
                st.success(recomendacion)
            elif recomendacion.startswith("⚠️"):
                st.warning(recomendacion)
            else:
                st.info(recomendacion)
        
        # Gráfico de análisis comparativo
        st.subheader("📈 Análisis Comparativo")
        
        fig_comparativo = go.Figure()
        
        # Notas actuales vs límite de aprobación
        fig_comparativo.add_trace(go.Bar(
            name='Notas del Estudiante',
            x=CURSOS,
            y=[st.session_state.notas_manuales[curso] for curso in CURSOS],
            marker_color=['#EF553B' if st.session_state.notas_manuales[curso] < 11 else '#00CC96' for curso in CURSOS]
        ))
        
        fig_comparativo.add_hline(y=11, line_dash="dash", line_color="red", annotation_text="Límite Aprobación")
        fig_comparativo.update_layout(title="Análisis de Notas vs Límite de Aprobación")
        st.plotly_chart(fig_comparativo, use_container_width=True)
    
    elif st.session_state.resultado_prediccion and 'error' in st.session_state.resultado_prediccion:
        st.error(f"Error en la predicción: {st.session_state.resultado_prediccion['error']}")

def mostrar_trayectoria_academica(df):
    st.header("📈 Trayectoria y Proyección Académica")
    
    if df.empty:
        st.warning("No hay datos disponibles")
        return
    
    estudiante_seleccionado = st.selectbox("Seleccionar Estudiante para Proyección", ESTUDIANTES, key="trayectoria")
    
    if estudiante_seleccionado:
        # Mostrar historial real
        st.subheader("Historial Académico Real")
        historial_real = df[df['Alumno'] == estudiante_seleccionado].sort_values('Semana')
        
        if not historial_real.empty:
            fig_historial = px.line(
                historial_real,
                x='Semana',
                y='Promedio',
                title=f'Evolución del Promedio - {estudiante_seleccionado}',
                markers=True
            )
            fig_historial.add_hline(y=11, line_dash="dash", line_color="red", annotation_text="Límite Aprobación")
            st.plotly_chart(fig_historial)

def mostrar_ingreso_calificaciones():
    st.header("📝 Ingreso de Calificaciones Semanales")
    
    # Inicializar el DataFrame en session_state si no existe
    if 'calificaciones_guardadas' not in st.session_state:
        st.session_state.calificaciones_guardadas = pd.DataFrame()
    
    with st.form("formulario_calificaciones"):
        st.subheader("Datos de la Semana")
        
        col1, col2 = st.columns(2)
        
        with col1:
            estudiante = st.selectbox("Estudiante", ESTUDIANTES, key="ingreso")
            semana = st.number_input("Semana", min_value=1, max_value=36, value=1)
            
            fecha_inicio = st.date_input("Fecha Inicio")
            fecha_fin = st.date_input("Fecha Fin")
        
        with col2:
            clases_asistidas = st.number_input("Clases Asistidas", min_value=0, max_value=100, value=18)
            clases_totales = st.number_input("Clases Totales", min_value=1, max_value=100, value=20)
            asistencia_porcentaje = (clases_asistidas / clases_totales) * 100
            st.info(f"Asistencia: {asistencia_porcentaje:.1f}%")
        
        st.subheader("Calificaciones por Curso (0-20)")
        
        # Crear columnas para las calificaciones
        cols = st.columns(4)
        calificaciones = {}
        
        for i, curso in enumerate(CURSOS):
            with cols[i % 4]:
                calificaciones[curso] = st.number_input(
                    f"{curso}", 
                    min_value=0.0, 
                    max_value=20.0, 
                    value=12.0,
                    step=0.5,
                    key=f"nota_ingreso_{curso}"
                )
        
        submitted = st.form_submit_button("💾 Guardar Calificaciones en Excel")
        
        if submitted:
            # Calcular métricas
            promedio = sum(calificaciones.values()) / len(calificaciones)
            
            # Crear nuevo registro
            nuevo_registro = {
                'ID_Estudiante': ESTUDIANTES.index(estudiante) + 1,
                'Alumno': estudiante,
                'Semana': semana,
                'Fecha Inicio': fecha_inicio.strftime('%d/%m/%Y'),
                'Fecha Fin': fecha_fin.strftime('%d/%m/%Y'),
                **calificaciones,
                'Clases Asistidas': clases_asistidas,
                'Clases Totales': clases_totales,
                'Promedio': round(promedio, 2),
                'Asistencia (%)': round(asistencia_porcentaje, 2),
                'Progreso Académico (%)': 0,
                'Desempeño academico': 'Excelente' if promedio >= 16 else 
                                      'Bueno' if promedio >= 14 else 
                                      'Regular' if promedio >= 11 else 'En Riesgo'
            }
            
            # Convertir a DataFrame
            nuevo_df = pd.DataFrame([nuevo_registro])
            
            # Combinar con datos existentes
            if st.session_state.calificaciones_guardadas.empty:
                st.session_state.calificaciones_guardadas = nuevo_df
            else:
                # Verificar si ya existe un registro para este estudiante en esta semana
                existe_registro = st.session_state.calificaciones_guardadas[
                    (st.session_state.calificaciones_guardadas['Alumno'] == estudiante) & 
                    (st.session_state.calificaciones_guardadas['Semana'] == semana)
                ]
                
                if not existe_registro.empty:
                    # Actualizar registro existente
                    st.session_state.calificaciones_guardadas = st.session_state.calificaciones_guardadas[
                        ~((st.session_state.calificaciones_guardadas['Alumno'] == estudiante) & 
                          (st.session_state.calificaciones_guardadas['Semana'] == semana))
                    ]
                
                st.session_state.calificaciones_guardadas = pd.concat(
                    [st.session_state.calificaciones_guardadas, nuevo_df], 
                    ignore_index=True
                )
            
            st.success(f"✅ Calificaciones de {estudiante} guardadas exitosamente para la semana {semana}!")
    
    # Mostrar el botón para ver el Excel y el resumen
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not st.session_state.calificaciones_guardadas.empty:
            # Crear Excel en memoria
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.calificaciones_guardadas.to_excel(writer, sheet_name='Calificaciones', index=False)
            
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Descargar Excel Completo",
                data=excel_data,
                file_name=f"calificaciones_estudiantes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        if not st.session_state.calificaciones_guardadas.empty:
            if st.button("👁️ Ver Excel Actualizado", use_container_width=True):
                st.subheader("📊 Vista Previa del Excel")
                
                # Mostrar estadísticas rápidas
                total_registros = len(st.session_state.calificaciones_guardadas)
                estudiantes_unicos = st.session_state.calificaciones_guardadas['Alumno'].nunique()
                semanas_unicas = st.session_state.calificaciones_guardadas['Semana'].nunique()
                
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    st.metric("Total Registros", total_registros)
                with col_stats2:
                    st.metric("Estudiantes", estudiantes_unicos)
                with col_stats3:
                    st.metric("Semanas", semanas_unicas)
                
                # Mostrar datos ordenados
                df_ordenado = st.session_state.calificaciones_guardadas.sort_values(['Semana', 'Alumno'])
                st.dataframe(df_ordenado, use_container_width=True)
                
                # Mostrar resumen por estudiante
                st.subheader("📈 Resumen por Estudiante")
                resumen_estudiantes = df_ordenado.groupby('Alumno').agg({
                    'Promedio': 'mean',
                    'Asistencia (%)': 'mean',
                    'Semana': 'count'
                }).round(2)
                resumen_estudiantes.columns = ['Promedio General', 'Asistencia Promedio (%)', 'Semanas Registradas']
                st.dataframe(resumen_estudiantes, use_container_width=True)
    
    # Mostrar estado actual siempre visible
    if not st.session_state.calificaciones_guardadas.empty:
        st.markdown("---")
        st.subheader("📋 Estado Actual del Registro")
        
        # Resumen compacto
        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
        
        with col_res1:
            st.metric("Registros Totales", len(st.session_state.calificaciones_guardadas))
        with col_res2:
            st.metric("Estudiantes Registrados", st.session_state.calificaciones_guardadas['Alumno'].nunique())
        with col_res3:
            st.metric("Semanas Capturadas", st.session_state.calificaciones_guardadas['Semana'].nunique())
        with col_res4:
            promedio_general = st.session_state.calificaciones_guardadas['Promedio'].mean()
            st.metric("Promedio General", f"{promedio_general:.1f}")
    
    else:
        st.info("ℹ️ Aún no se han guardado calificaciones. Usa el formulario arriba para comenzar.")

def main():

    # === AGREGAR ESTA LÍNEA AL INICIO DE main() ===
    mostrar_logout() 

    st.title("🎓 Sistema de Monitoreo y Predicción del Desempeño Estudiantil")
    st.markdown("### Monitoreo Semanal del Desempeño Académico")
    
    # Sidebar
    st.sidebar.header("Configuración del Sistema")
    
    # Cargar datos - AHORA SOPORTA CSV
    archivo = st.sidebar.file_uploader("Cargar archivo (Excel o CSV)", type=['xlsx', 'csv'])
    
    if archivo is not None:
        try:
            if archivo.name.endswith('.csv'):
                df = pd.read_csv(archivo, dtype=str)  # ← CORREGIDO: agregado dtype=str
            else:
                df = pd.read_excel(archivo)
            
            # ← CORREGIDO: Agregada esta línea para formatear fechas
            df = formatear_fechas_df(df)
            
            # Actualizar listas globales con los datos reales
            actualizar_listas_desde_dataframe(df)
            
            # Calcular métricas
            df = calcular_metricas(df)
            
            st.sidebar.success(f"✅ Datos cargados exitosamente!")
            st.sidebar.info(f"📊 {len(df)} registros | 👨‍🎓 {len(ESTUDIANTES)} estudiantes | 📚 {len(CURSOS)} cursos")
            
            # Mostrar vista previa de los datos
            with st.sidebar.expander("🔍 Vista previa de datos"):
                st.dataframe(df.head(3), use_container_width=True)
                
        except Exception as e:
            st.sidebar.error(f"❌ Error al cargar archivo: {e}")
            df = pd.DataFrame()
    else:
        # Datos de ejemplo
        st.sidebar.info("ℹ️ Usando datos de ejemplo. Carga un archivo CSV o Excel para usar tus propios datos.")
        df = generar_datos_ejemplo()
        actualizar_listas_desde_dataframe(df)
    
    # Entrenar modelos si hay datos
    if not df.empty and len(df) > 10:
        if st.sidebar.button("🔧 Entrenar Modelos de Predicción"):
            with st.spinner("Entrenando modelos de IA..."):
                resultados = predictor.entrenar_modelos(df)
                if resultados:
                    st.sidebar.success("✅ Modelos entrenados exitosamente!")
                    st.sidebar.metric("Árbol de Decisión", f"{resultados['arbol_accuracy']:.2%}")
                    st.sidebar.metric("SVM", f"{resultados['svm_accuracy']:.2%}")
                    st.sidebar.metric("KNN", f"{resultados['knn_accuracy']:.2%}")
    
    # Navegación
    opcion = st.sidebar.selectbox(
        "Seleccionar Vista",
        ["📊 Dashboard General", "👨‍🎓 Monitoreo por Semana", "🔮 Predicción de Riesgo", 
         "📈 Trayectoria Académica", "📝 Ingreso de Calificaciones"]
    )
    
    if opcion == "📊 Dashboard General":
        mostrar_dashboard_general(df)
    elif opcion == "👨‍🎓 Monitoreo por Semana":
        mostrar_monitoreo_semanal(df)
    elif opcion == "🔮 Predicción de Riesgo":
        mostrar_prediccion_riesgo(df)
    elif opcion == "📈 Trayectoria Académica":
        mostrar_trayectoria_academica(df)
    elif opcion == "📝 Ingreso de Calificaciones":
        mostrar_ingreso_calificaciones()

if __name__ == "__main__":
    main()
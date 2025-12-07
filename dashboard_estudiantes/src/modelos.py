import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib
import warnings
warnings.filterwarnings('ignore')

class PredictorDesempeno:
    def __init__(self):
        self.modelo_arbol = DecisionTreeClassifier(random_state=42, max_depth=5)
        self.modelo_svm = SVC(random_state=42, probability=True)
        self.modelo_knn = KNeighborsClassifier(n_neighbors=3)
        self.encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.entrenado = False
        self.caracteristicas = []
        
    def preparar_datos(self, df):
        """Prepara los datos para el entrenamiento"""
        try:
            # Crear variable objetivo (1: en riesgo, 0: no en riesgo)
            df['en_riesgo'] = np.where(df['Promedio'] < 11, 1, 0)
            
            # Detectar columnas de cursos automáticamente
            columnas_excluir = ['ID_Estudiante', 'Alumno', 'Estudiante', 'Nombre', 'Student', 'Semana', 
                               'Fecha Inicio', 'Fecha Fin', 'Clases Asistidas', 'Clases Totales', 
                               'Promedio', 'Asistencia (%)', 'Promedio_Anterior', 
                               'Progreso Académico (%)', 'Desempeño academico', 'en_riesgo']
            
            cursos_detectados = []
            for col in df.columns:
                if col not in columnas_excluir:
                    # Verificar si es numérica o puede convertirse
                    if pd.api.types.is_numeric_dtype(df[col]):
                        cursos_detectados.append(col)
                    else:
                        try:
                            # Intentar convertir a numérico
                            temp_series = pd.to_numeric(df[col], errors='coerce')
                            if not temp_series.isna().all():  # Si al menos algunos valores son numéricos
                                cursos_detectados.append(col)
                        except:
                            continue
            
            # Si no se detectan cursos, usar los predeterminados
            if not cursos_detectados:
                cursos_detectados = [
                    'Comunicación', 'Matemática', 'Ciencia y Tecnología', 
                    'Personal Social', 'Educación Religiosa', 'Educación Física', 
                    'Arte', 'Inglés'
                ]
            
            # Seleccionar características
            self.caracteristicas = cursos_detectados.copy()
            
            # Agregar métricas si existen
            if 'Asistencia (%)' in df.columns:
                self.caracteristicas.append('Asistencia (%)')
            if 'Progreso Académico (%)' in df.columns:
                self.caracteristicas.append('Progreso Académico (%)')
            
            # Asegurar que todas las características sean numéricas
            for col in self.caracteristicas:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            X = df[self.caracteristicas]
            y = df['en_riesgo']
            
            return X, y
            
        except Exception as e:
            print(f"Error en preparar_datos: {e}")
            return None, None
    
    def entrenar_modelos(self, df):
        """Entrena los tres modelos con los datos proporcionados"""
        try:
            X, y = self.preparar_datos(df)
            
            if X is None or y is None:
                return None
            
            # Verificar que tenemos datos suficientes
            if len(X) < 10:
                print("No hay suficientes datos para entrenar")
                return None
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Escalar características
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Entrenar modelos
            self.modelo_arbol.fit(X_train, y_train)
            self.modelo_svm.fit(X_train_scaled, y_train)
            self.modelo_knn.fit(X_train_scaled, y_train)
            
            # Evaluar modelos
            predicciones_arbol = self.modelo_arbol.predict(X_test)
            predicciones_svm = self.modelo_svm.predict(X_test_scaled)
            predicciones_knn = self.modelo_knn.predict(X_test_scaled)
            
            resultados = {
                'arbol_accuracy': accuracy_score(y_test, predicciones_arbol),
                'svm_accuracy': accuracy_score(y_test, predicciones_svm),
                'knn_accuracy': accuracy_score(y_test, predicciones_knn)
            }
            
            self.entrenado = True
            return resultados
            
        except Exception as e:
            print(f"Error en entrenamiento: {e}")
            return None
    
    def predecir_riesgo_manual(self, notas_estudiante, asistencia_porcentaje, progreso_academico=0):
        """Predice riesgo basado en notas manualmente ingresadas"""
        if not self.entrenado:
            return {"error": "Modelo no entrenado"}
        
        try:
            # Verificar que tenemos características definidas
            if not self.caracteristicas:
                return {"error": "No hay características definidas para la predicción"}
            
            # Preparar datos del estudiante
            datos_estudiante = []
            
            # Agregar notas de cursos
            for i, caracteristica in enumerate(self.caracteristicas):
                if caracteristica in ['Asistencia (%)', 'Progreso Académico (%)']:
                    continue
                if i < len(notas_estudiante):
                    datos_estudiante.append(notas_estudiante[i])
                else:
                    datos_estudiante.append(0)  # Valor por defecto si faltan notas
            
            # Agregar asistencia y progreso si están en las características
            if 'Asistencia (%)' in self.caracteristicas:
                datos_estudiante.append(asistencia_porcentaje)
            if 'Progreso Académico (%)' in self.caracteristicas:
                datos_estudiante.append(progreso_academico)
            
            # Crear DataFrame
            X_estudiante = pd.DataFrame([datos_estudiante], columns=self.caracteristicas)
            X_estudiante_scaled = self.scaler.transform(X_estudiante)
            
            # Realizar predicciones
            pred_arbol = self.modelo_arbol.predict(X_estudiante)[0]
            pred_svm = self.modelo_svm.predict(X_estudiante_scaled)[0]
            pred_knn = self.modelo_knn.predict(X_estudiante_scaled)[0]
            
            # Obtener probabilidades
            proba_arbol = self.modelo_arbol.predict_proba(X_estudiante)[0]
            proba_svm = self.modelo_svm.predict_proba(X_estudiante_scaled)[0]
            proba_knn = self.modelo_knn.predict_proba(X_estudiante_scaled)[0]
            
            # Votación mayoritaria
            predicciones = [pred_arbol, pred_svm, pred_knn]
            riesgo_final = 1 if sum(predicciones) >= 2 else 0
            
            # Calcular promedio y determinar nivel de desempeño
            promedio = np.mean(notas_estudiante)
            
            if promedio >= 16:
                nivel_desempeno = "ALTO"
                color_desempeno = "🟢"
            elif promedio >= 11:
                nivel_desempeno = "MEDIO" 
                color_desempeno = "🟡"
            else:
                nivel_desempeno = "BAJO"
                color_desempeno = "🔴"
            
            # Calcular confianza promedio
            confianzas = [
                max(proba_arbol),
                max(proba_svm),
                max(proba_knn)
            ]
            confianza_promedio = np.mean(confianzas)
            
            return {
                'en_riesgo': bool(riesgo_final),
                'nivel_desempeno': nivel_desempeno,
                'color_desempeno': color_desempeno,
                'promedio': float(promedio),
                'predicciones_individuales': {
                    'arbol': {
                        'prediccion': bool(pred_arbol), 
                        'confianza': float(max(proba_arbol))
                    },
                    'svm': {
                        'prediccion': bool(pred_svm), 
                        'confianza': float(max(proba_svm))
                    },
                    'knn': {
                        'prediccion': bool(pred_knn), 
                        'confianza': float(max(proba_knn))
                    }
                },
                'confianza_general': float(confianza_promedio),
                'recomendaciones': self.generar_recomendaciones(riesgo_final, nivel_desempeno, promedio, asistencia_porcentaje)
            }
            
        except Exception as e:
            return {"error": f"Error en predicción: {str(e)}"}
    
    def generar_recomendaciones(self, riesgo, nivel_desempeno, promedio, asistencia):
        """Genera recomendaciones personalizadas basadas en el análisis"""
        recomendaciones = []
        
        if riesgo == 1:
            recomendaciones.append("🚨 ALTO RIESGO DE REPROBACIÓN")
            recomendaciones.append("✅ Programar tutorías personalizadas inmediatas")
            recomendaciones.append("✅ Reforzamiento intensivo en áreas críticas")
            recomendaciones.append("✅ Comunicación urgente con padres/tutores")
        else:
            if nivel_desempeno == "ALTO":
                recomendaciones.append("🎉 EXCELENTE DESEMPEÑO")
                recomendaciones.append("✅ Mantener el excelente trabajo académico")
                recomendaciones.append("✅ Participar en actividades de enriquecimiento")
            elif nivel_desempeno == "MEDIO":
                recomendaciones.append("📈 DESEMPEÑO ADECUADO")
                recomendaciones.append("✅ Continuar con el buen rendimiento")
                recomendaciones.append("✅ Identificar áreas de mejora")
        
        if promedio < 14 and promedio >= 11:
            recomendaciones.append("📚 Fortalecer áreas con notas menores a 14")
        
        if asistencia < 85:
            recomendaciones.append("⚠️ Mejorar asistencia a clases")
        elif asistencia < 95:
            recomendaciones.append("📅 Asistencia regular, buscar mejorar consistencia")
        
        # Recomendaciones generales
        if promedio < 11:
            recomendaciones.append("🔴 URGENTE: Necesita apoyo académico inmediato")
        elif promedio < 14:
            recomendaciones.append("🟡 ATENCIÓN: Requiere seguimiento constante")
        else:
            recomendaciones.append("🟢 ESTABLE: Buen desempeño académico")
        
        return recomendaciones
    
    def guardar_modelos(self, ruta):
        """Guarda los modelos entrenados"""
        try:
            joblib.dump({
                'arbol': self.modelo_arbol,
                'svm': self.modelo_svm,
                'knn': self.modelo_knn,
                'scaler': self.scaler,
                'caracteristicas': self.caracteristicas,
                'entrenado': self.entrenado
            }, ruta)
            return True
        except Exception as e:
            print(f"Error al guardar modelos: {e}")
            return False
    
    def cargar_modelos(self, ruta):
        """Carga modelos previamente entrenados"""
        try:
            modelos = joblib.load(ruta)
            self.modelo_arbol = modelos['arbol']
            self.modelo_svm = modelos['svm']
            self.modelo_knn = modelos['knn']
            self.scaler = modelos['scaler']
            self.caracteristicas = modelos.get('caracteristicas', [])
            self.entrenado = modelos.get('entrenado', False)
            return True
        except Exception as e:
            print(f"Error al cargar modelos: {e}")
            return False
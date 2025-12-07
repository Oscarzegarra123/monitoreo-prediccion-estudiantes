import streamlit as st
import hashlib
import re

# Configuración de usuarios (en producción usar base de datos)
USUARIOS = {
    "zegarra": {
        "password": "zegarra123",
        "nombre": "Profesor Zegarra",
        "rol": "profesor",
        "grado": "6to Primaria"
    }
}

def hash_password(password):
    """Hashea la contraseña para mayor seguridad"""
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_login(usuario, password):
    """Verifica las credenciales del usuario"""
    if usuario in USUARIOS:
        # En este caso simple, comparamos directamente
        # En producción compararíamos hashes
        if USUARIOS[usuario]["password"] == password:
            return True
    return False

def mostrar_login():
    """Muestra la interfaz de login"""
    
    # ⚠️ QUITAR st.set_page_config() de aquí - ya se configuró en main.py
    
    # CSS personalizado para el login
    st.markdown("""
    <style>
        /* FONDO COMPLETO #95a5a6 */
        .main {
            background-color: #95a5a6 !important;
        }
        .stApp {
            background-color: #95a5a6 !important;
        }
        
        /* QUITAR RESALTADO AMARILLO */
        .stTextInput>div>div>input {
            background-color: white !important;
            border: 2px solid #7f8c8d;
            color: #2c3e50;
        }
        
        input:-webkit-autofill,
        input:-webkit-autofill:hover, 
        input:-webkit-autofill:focus,
        input:-webkit-autofill:active {
            -webkit-box-shadow: 0 0 0 30px white inset !important;
            -webkit-text-fill-color: #2c3e50 !important;
            background-color: white !important;
        }
        
        .stTextInput>div>div>input:focus {
            outline: none !important;
            box-shadow: 0 0 0 2px #3498db !important;
            background-color: white !important;
        }
        
        /* CONTENEDOR PRINCIPAL */
        .login-container {
            background-color: transparent !important;
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem auto;
            max-width: 500px;
            box-shadow: none !important;
        }
        
        /* TARJETA DE CONTENIDO */
        .content-card {
            background-color: #95a5a6;
            padding: 2.5rem;
            border-radius: 15px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.1);
            border: none !important;
        }
        
        .school-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        /* COLORES MEJORADOS PARA LOS TEXTOS */
        .school-name {
            font-size: 1.6rem;
            font-weight: bold;
            color: #2c3e50;  /* Azul oscuro elegante */
            margin-bottom: 0.5rem;
            text-align: center;
        }
        .school-institution {
            font-size: 1.6rem;
            font-weight: bold;
            color: #1a5276;  /* Azul más vibrante */
            margin-bottom: 0.5rem;
            text-align: center;
        }
        .school-caudevilla {
            font-size: 1.6rem;
            font-weight: bold;
            color: #1a5276;  /* Rojo destacado */
            margin-bottom: 0.5rem;
            text-align: center;
            font-style: italic;
        }
        .school-subtitle {
            font-size: 1.2rem;
            color: #1e8449;  /* Verde fresco */
            margin-top: 1rem;
            text-align: center;
            font-weight: 600;
        }
        .login-title {
            text-align: center;
            color: #6c3483;  /* Púrpura profesional */
            margin-bottom: 1.5rem;
            font-size: 1.8rem;
            font-weight: bold;
        }
        
        .image-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 1.5rem;
            width: 100%;
        }
        
        /* CENTRAR PERFECTAMENTE LA IMAGEN */
        .centered-image {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0 auto;
        }
        
        /* CAMPOS DE TEXTO */
        .stTextInput>div>div>input {
            border-radius: 10px;
            border: 2px solid #7f8c8d;
            padding: 12px;
            background-color: white !important;
            font-size: 14px;
            transition: all 0.3s ease;
            color: #2c3e50;
        }
        .stTextInput>div>div>input:focus {
            border-color: #3498db;
            background-color: white !important;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }
        .stTextInput>div>div>input::placeholder {
            color: #95a5a6;
        }
        
        /* ETIQUETAS CON COLOR MEJORADO */
        .stTextInput label {
            font-weight: 600;
            color: #2c3e50 !important;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        /* BOTÓN CON COLOR MEJORADO */
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            padding: 14px 1rem;
            background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);  /* Naranja vibrante */
            color: white;
            border: none;
            font-weight: bold;
            font-size: 16px;
            transition: all 0.3s ease;
            margin-top: 15px;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #d35400 0%, #ba4a00 100%);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(230, 126, 34, 0.4);
        }
        
        .loading-spinner {
            text-align: center;
            color: #2c3e50;
            font-style: italic;
        }
        
        /* COLORES PARA MENSAJES */
        .stSuccess {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            border-radius: 8px;
            padding: 10px;
        }
        .stError {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            border-radius: 8px;
            padding: 10px;
        }
        
        /* TÍTULO ACCESO PROFESORES CON COLOR MEJORADO */
        .access-title {
            text-align: center;
            color:  #ca6f1e !important;  /* Rojo oscuro elegante */
            margin-bottom: 1.5rem;
            font-size: 1.3rem;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* OCULTAR ELEMENTOS DE STREAMLIT */
        header {display: none !important;}
        .css-1d391kg {display: none !important;}
        #MainMenu {display: none !important;}
        footer {display: none !important;}
        
        .stTextInput>div>div>input:focus-within {
            border-color: #3498db !important;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1) !important;
        }
        
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
        }
        
        div[data-testid="stVerticalBlock"] {
            background: transparent !important;
        }
        
        .css-1v0mbdj {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        /* 🔒 EVITAR MOVIMIENTOS Y MANTENER ESTABLE */
        .stApp {
            transition: none !important;
            animation: none !important;
        }
        .main .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor principal del login
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            
            # Encabezado con imagen PERFECTAMENTE CENTRADA
            st.markdown('<div class="school-header">', unsafe_allow_html=True)
            
            # IMAGEN PERFECTAMENTE CENTRADA
            left_spacer, image_col, right_spacer = st.columns([1, 1, 1])
            with image_col:
                try:
                    st.image("images/colegio.JPG", width=150, use_container_width=True)
                except:
                    st.image("https://via.placeholder.com/150x150/3498db/ffffff?text=LOGO", width=150, use_container_width=True)
            
            # TEXTOS CON NUEVOS COLORES (ya centrados por CSS)
            st.markdown(
                """
                <div class="school-institution">INSTITUCIÓN EDUCATIVA 3507</div>
                <div class="school-caudevilla">"CAUDEVILLA"</div>
                <div class="school-subtitle">6TO GRADO - PRIMARIA</div>
                """, 
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown('<div class="login-title">SISTEMA DE MONITOREO Y PREDICCIÓN</div>', unsafe_allow_html=True)
                
            # Formulario de login
            with st.form("login_form"):
                    st.markdown('<div class="access-title">ACCESO PROFESORES</div>', unsafe_allow_html=True)
                    
                    usuario = st.text_input(
                        "👤 **Usuario:**",
                        placeholder="Ingrese su usuario",
                        key="usuario_input"
                    )
                    
                    password = st.text_input(
                        "🔒 **Contraseña:**",
                        type="password",
                        placeholder="Ingrese su contraseña",
                        key="password_input"
                    )
                    
                    login_button = st.form_submit_button("🚀 INGRESAR AL SISTEMA", use_container_width=True)
                    
                    if login_button:
                        if not usuario or not password:
                            st.error("❌ Por favor complete todos los campos")
                        else:
                            with st.spinner("🔐 Verificando credenciales..."):
                                import time
                                time.sleep(1.5)
                                
                                if verificar_login(usuario, password):
                                    st.session_state.logged_in = True
                                    st.session_state.usuario = usuario
                                    st.session_state.nombre = USUARIOS[usuario]["nombre"]
                                    st.session_state.rol = USUARIOS[usuario]["rol"]
                                    st.session_state.grado = USUARIOS[usuario]["grado"]
                                    
                                    st.success(f"✅ ¡Bienvenido/a {USUARIOS[usuario]['nombre']}!")
                                    
                                    st.markdown(
                                        """
                                        <div class="loading-spinner">
                                            <p>⏳ Cargando sistema, por favor espere...</p>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                                    
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("❌ Usuario o contraseña incorrectos")
                

def verificar_autenticacion():
    """Verifica si el usuario está autenticado"""
    if not st.session_state.get('logged_in'):
        mostrar_login()
        st.stop()
    return True

def mostrar_logout():
    """Muestra el botón de logout en el sidebar"""
    if st.session_state.get('logged_in'):
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**👤 Usuario:** {st.session_state.get('nombre', '')}")
        st.sidebar.markdown(f"**🏫 Grado:** {st.session_state.get('grado', '')}")
        
        if st.sidebar.button("🚪 Cerrar Sesión"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
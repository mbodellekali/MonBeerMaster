import streamlit as st
import pandas as pd

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Beer Master", page_icon="🍺", layout="wide")

# --- STYLE CSS (Police "Rye" Style Bière) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rye&family=Poppins:wght@300;600&display=swap');
    
    /* TITRE PRINCIPAL */
    .main-title {
        font-family: 'Rye', serif;
        font-size: 4em;
        text-align: center;
        color: #e67e22; 
        margin-bottom: 0px;
        text-shadow: 2px 2px 0px #000;
    }
    
    .sub-title {
        font-family: 'Poppins', sans-serif;
        font-size: 1.5em;
        text-align: center;
        color: #555;
        font-style: italic;
        margin-top: -10px;
        margin-bottom: 40px;
    }

    h1, h2, h3 {
        font-family: 'Rye', serif !important;
        color: #2c3e50;
    }

    div.stButton > button {
        background-color: #e67e22;
        color: white !important;
        border-radius: 10px;
        font-family: 'Rye', serif;
        font-size: 1.4rem;
        border: none;
        padding: 0.6rem 1rem;
        letter-spacing: 1px;
    }
    div.stButton > button:hover {
        background-color: #d35400;
        border: 2px solid #e67e22;
        color: #fff !important;
    }
    
    .stSelectbox label, .stNumberInput label, .stSlider label {
        font-family: 'Rye', serif;
        font-size: 1.1em;
        color: #444;
    }
    </style>
""", unsafe_allow_html=True)

# --- GESTION DE L'ÉTAT ---
if 'recette_generee' not in st.session_state:
    st.session_state.recette_generee = False

# --- CHARGEMENT DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("bieres.csv", sep=";", dtype=str)
        df['Degre'] = df['Degre'].str.replace(',', '.').astype(float)
        df['Type_lower'] = df['Type'].str.lower()
        df['Aromes_lower'] = df['Aromes'].str.lower().fillna("")
        return df
    except Exception:
        return pd.DataFrame()

df = load_data()

# --- HEADER AVEC LOGO ---
# On centre le logo avec des colonnes
c_logo1, c_logo2, c_logo3 = st.columns([1, 1, 1])
with c_logo2:
    try:
        # Affiche le logo s'il existe, avec une largeur adaptée
        st.image("logo.png", use_container_width=True)
    except:
        # Si pas d'image, on ne met rien (évite le plantage)
        pass

st.markdown('<h1 class="main-title">🍺 Beer Master</h1>', unsafe_allow_html=True)
# MODIFICATION ICI : Nouveau sous-titre
st.markdown('<p class="sub-title">Le générateur de recettes</p>', unsafe_allow_html=True)

# ==========================================
# PARTIE 1 : RÉGLAGES
# ==========================================

definitions_styles = {
    "Blonde": "☀️ **La Blonde :** Dorée et accessible. L'équilibre parfait.",
    "IPA": "🌲 **L'IPA :** L'amertume avant tout, portée par des houblons aromatiques.",
    "Stout": "☕ **Le Stout :** Sombre, notes de torréfaction intenses.",
    "Ambrée": "🍂 **L'Ambrée :** La gourmandise du malt caramélisé.",
    "Blanche": "☁️ **La Blanche :** Fraîcheur, blé et notes acidulées.",
    "Saison": "🚜 **La Saison :** Bière fermière rustique, sèche, poivrée et très pétillante.",
    "Sour": "🍋 **La Sour :** L'acidité rafraîchissante, souvent fruitée.",
    "Lager": "❄️ **La Lager :** Fermentation basse, goût net, croquant et céréalier."
}

with st.container(border=True):
    col_gauche, col_droite = st.columns(2)
    
    with col_gauche:
        st.subheader("Le Style")
        style = st.selectbox("Quel style de bière ?", ["Blonde", "IPA", "Stout", "Ambrée", "Blanche", "Saison", "Sour", "Lager"])
        st.info(definitions_styles[style])
        
        c1, c2 = st.columns(2)
        volume = c1.number_input("Volume (Litres)", 5, 100, 20)
        degre_vise = c2.slider("Degré alcool (%)", 3.0, 12.0, 6.0, 0.1)

    with col_droite:
        st.subheader("La Palette Aromatique")
        
        options_aromes = [
            "🍊 Agrumes", "🥭 Tropical", "🌲 Pin", "🍌 Banane", 
            "☕ Café", "🍫 Chocolat", "🍮 Caramel", "🍪 Biscuit",
            "🥓 Fumé", "🌶️ Épices", "🌸 Floral", "🍓 Fruits Rouges", "🌿 Herbacé"
        ]

        aromes_selectionnes = st.pills(
            "Marqueurs dominants (Max 2) :",
            options_aromes,
            default=[], 
            selection_mode="multi"
        )
        
        trop_d_aromes = False
        if len(aromes_selectionnes) > 2:
            st.warning("⚠️ Trop d'arômes tuent l'arôme ! Choisissez-en **2 maximum**.")
            trop_d_aromes = True
        
        st.write("") 
        amertume = st.select_slider("Amertume (IBU) :", options=["Nulle", "Légère", "Moyenne", "Forte", "Extrême"])

st.write("") 

col_btn1
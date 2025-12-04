import streamlit as st
import pandas as pd

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Beer Master", page_icon="🍺", layout="wide")

# --- STYLE CSS (Police "Rye" Style Bière) ---
st.markdown("""
    <style>
    /* Import de la police Rye (Titre) et Poppins (Texte) */
    @import url('https://fonts.googleapis.com/css2?family=Rye&family=Poppins:wght@300;600&display=swap');
    
    /* TITRE PRINCIPAL */
    .main-title {
        font-family: 'Rye', serif;
        font-size: 4em;
        text-align: center;
        color: #e67e22; /* Orange Bière */
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

    /* TOUS LES TITRES (H1, H2, H3) EN STYLE BIÈRE */
    h1, h2, h3 {
        font-family: 'Rye', serif !important;
        color: #2c3e50;
    }

    /* BOUTON GÉNÉRER */
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
    
    /* Input Labels */
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

# --- HEADER ---
st.markdown('<h1 class="main-title">🍺 Beer Master</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">L\'Atelier de Brassage</p>', unsafe_allow_html=True)

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
        
        # ICI : J'ai retiré toute la logique de pré-sélection.
        # Le 'default' est maintenant une liste vide [] pour tout le monde.

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

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    if st.button("🍺 GÉNÉRER MA RECETTE 🍺", type="primary", use_container_width=True, disabled=trop_d_aromes):
        st.session_state.recette_generee = True

st.divider()

# ==========================================
# PARTIE 2 : LE RÉSULTAT
# ==========================================

if st.session_state.recette_generee:
    
    # --- 1. CALCULS DES GRAINS (PRÉCISION) ---
    total_malt = round((volume * degre_vise) / 100 * 4.5, 2)
    
    # Répartition par défaut (90% Base / 10% Spécial)
    ratio_base = 0.90
    ratio_spe = 0.10
    
    # Ingrédients par défaut
    malt_base_nom = "Malt Pilsner"
    malt_spe_nom = "Malt de Blé"
    levure = "US-05 (Neutre)"
    houblon_amer = "Magnum"
    houblon_arome = "Saaz"
    
    # Variables de Process
    temp_empatage = 65; temps_ebu = 60; temp_ferm = 20
    
    # Logique Spécifique Styles
    if style == "IPA":
        malt_base_nom = "Malt Pale Ale"; malt_spe_nom = "Malt Carapils"; levure = "Verdant IPA"; temp_empatage = 64
        ratio_base = 0.93; ratio_spe = 0.07 
    elif style == "Stout":
        malt_base_nom = "Malt Maris Otter"; malt_spe_nom = "Malt Chocolat & Orge Grillé"; levure = "S-04"; temp_empatage = 68
        ratio_base = 0.85; ratio_spe = 0.15 
    elif style == "Ambrée":
        malt_base_nom = "Malt Pale Ale"; malt_spe_nom = "Malt Cara Ruby"; levure = "T-58"; temp_empatage = 67
        ratio_base = 0.85; ratio_spe = 0.15
    elif style == "Blanche":
        malt_base_nom = "Malt Pilsner"; malt_spe_nom = "Froment (Blé Cru)"; levure = "WB-06"
        ratio_base = 0.60; ratio_spe = 0.40 
    elif style == "Saison":
        malt_base_nom = "Malt Pilsner"; malt_spe_nom = "Malt Munich"; levure = "Belle Saison"; temp_ferm = 26; temp_empatage = 63
    elif style == "Sour":
        malt_base_nom = "Malt Pilsner"; malt_spe_nom = "Malt Acide"; levure = "Philly Sour"
    elif style == "Lager":
        malt_base_nom = "Malt Pilsner"; malt_spe_nom = "Malt Vienna"; levure = "W-34/70"; temp_ferm = 12; temps_ebu = 90

    # Ajout d'arômes dans les noms des malts
    aromes_clean = [a.split(" ")[1] if " " in a else a for a in aromes_selectionnes]
    if "Biscuit" in aromes_clean: malt_spe_nom += " + Malt Biscuit"
    if "Fumé" in aromes_clean: malt_base_nom = "Malt Fumé (Beechwood)"
    if "Caramel" in aromes_clean and style != "Ambrée": malt_spe_nom += " + Malt Crystal 150"

    # Calcul des poids exacts
    poids_base = total_malt * ratio_base
    poids_spe = total_malt * ratio_spe

    # --- 2. CALCULS HOUBLONS ---
    if "Agrumes" in aromes_clean: houblon_arome = "Citra & Amarillo"
    elif "Tropical" in aromes_clean: houblon_arome = "Galaxy & Mosaic"
    elif "Pin" in aromes_clean: houblon_arome = "Simcoe & Chinook"
    elif "Floral" in aromes_clean: houblon_arome = "Mistral"
    elif "Herbacé" in aromes_clean: houblon_arome = "Hallertau Mittelfrüh"
    elif "Fruits" in aromes_clean: houblon_arome = "Barbe Rouge"
    elif "Café" in aromes_clean: houblon_arome = "Fuggles"

    ibu_target = 20
    if amertume == "Moyenne": ibu_target = 40
    elif amertume == "Forte": ibu_target = 60
    elif amertume == "Extrême": ibu_target = 90
    
    grammes_amer = volume * (ibu_target / 25) 
    grammes_arome = volume * 4 if ibu_target > 40 else volume * 2

    # --- 3. CALCUL LEVURE ---
    nb_sachets = 1
    poids_levure = 11.5
    
    if volume > 25 or degre_vise > 7.5:
        nb_sachets = 2
        poids_levure = 23

    # --- AFFICHAGE RECETTE ---
    st.header(f"📜 Fiche Technique : {style} {', '.join(aromes_clean)}")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("### 🌾 Bill of Materials (Grains)")
            st.write(f"**Total Grains : {total_malt} kg**")
            # Affichage précis des poids
            st.write(f"- **{poids_base:.2f} kg** : {malt_base_nom}")
            st.write(f"- **{poids_spe:.2f} kg** : {malt_spe_nom}")
            
            st.markdown("---")
            st.markdown("### 🦠 Levure")
            st.write(f"**{poids_levure}g** ({nb_sachets} sachet{'s' if nb_sachets > 1 else ''})")
            st.write(f"Souche : **{levure}**")

    with c2:
        with st.container(border=True):
            st.markdown("### 🌿 Plan de Houblonnage")
            st.write(f"1️⃣ **Amérisant (60min)** : {int(grammes_amer)}g de {houblon_amer}")
            st.write(f"2️⃣ **Aromatique (5min)** : {int(grammes_arome)}g de **{houblon_arome}**")
            if "Tropical" in aromes_clean or "Agrumes" in aromes_clean:
                 st.write(f"3️⃣ **Dry Hop (J+4)** : {int(grammes_arome)}g de {houblon_arome}")

    # --- PROCESSUS ---
    st.subheader("⏳ Profil de Brassage")
    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.metric("1. Empâtage", f"{temp_empatage}°C", "60 min")
    col_p2.metric("2. Ébullition", f"{temps_ebu} min", "100°C")
    col_p3.metric("3. Fermentation", f"{temp_ferm}°C", "15 jours")

    st.divider()

    # --- MATCHING ---
    st.header("(Pour comparer :)")
    
    if not df.empty and aromes_selectionnes:
        suggestions = []
        mots_cles_user = [a.split(" ")[1].lower() if " " in a else a.lower() for a in aromes_selectionnes]
        
        for index, row in df.iterrows():
            score = 0
            raisons = []
            if style.lower() in str(row['Type_lower']):
                score += 2
                raisons.append("Style identique")
            
            match_arome = False
            for mot in mots_cles_user:
                if mot in str(row['Aromes_lower']):
                    match_arome = True
                    raisons.append(f"Note de {mot}")
            if match_arome: score += 3 
            
            if abs(row['Degre'] - degre_vise) <= 1.5: score += 1

            if score >= 3: suggestions.append((row, score, raisons))
        
        if suggestions:
            suggestions.sort(key=lambda x: x[1], reverse=True)
            top_match = suggestions[0]
            beer, score, raisons = top_match

            col_vide1, col_center, col_vide2 = st.columns([1, 2, 1])
            with col_center:
                with st.container(border=True):
                    st.markdown(f"<h3 style='text-align: center; color: #e67e22;'>🏆 {beer['Nom']}</h3>", unsafe_allow_html=True)
                    st.caption(f"<div style='text-align: center;'>{beer['Type']} | {beer['Degre']}°</div>", unsafe_allow_html=True)
                    st.success(f"Pourquoi ? {', '.join(raisons)}")
                    st.write(f"*{beer['Description']}*")
                    
                    if pd.notna(beer['Lien_Achat']) and str(beer['Lien_Achat']).startswith('http'):
                        st.link_button("🛒 Commander pour goûter", beer['Lien_Achat'], type="primary", use_container_width=True)
                    else:
                        st.button("Indisponible en ligne", disabled=True, use_container_width=True)
        else:
            st.warning(f"Aucune bière commerciale correspondante dans la base.")
    else:
         st.info("Sélectionnez des arômes pour voir le comparatif.")

else:
    st.info("👆 Configurez vos préférences ci-dessus et cliquez sur le bouton.")
    for _ in range(5): st.write("")
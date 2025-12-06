import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import math

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Beer Factory", page_icon="🍺", layout="wide")

# --- DATA: BASE DE DONNÉES INGRÉDIENTS (POUR LES CALCULS) ---
MALTS_DB = {
    "Pilsner": {"yield": 78, "ebc": 3.5},
    "Pale Ale": {"yield": 79, "ebc": 6.5},
    "Maris Otter": {"yield": 78, "ebc": 5.0},
    "Munich": {"yield": 76, "ebc": 15},
    "Vienna": {"yield": 76, "ebc": 8},
    "Blé (Froment)": {"yield": 80, "ebc": 4},
    "Carapils": {"yield": 72, "ebc": 3},
    "Malt Acide": {"yield": 50, "ebc": 4},
    "Cara Ruby": {"yield": 74, "ebc": 50},
    "Crystal 150": {"yield": 70, "ebc": 150},
    "Chocolat": {"yield": 65, "ebc": 900},
    "Orge Grillé": {"yield": 65, "ebc": 1200},
    "Fumé": {"yield": 77, "ebc": 6},
    "Biscuit": {"yield": 75, "ebc": 50}
}

HOPS_DB = {
    "Magnum": {"aa": 12.0}, "Saaz": {"aa": 3.5}, "Citra": {"aa": 13.0},
    "Amarillo": {"aa": 9.0}, "Mosaic": {"aa": 12.0}, "Galaxy": {"aa": 14.0},
    "Simcoe": {"aa": 13.0}, "Chinook": {"aa": 13.0}, "Mistral": {"aa": 6.5},
    "Hallertau Mittelfrüh": {"aa": 4.0}, "Barbe Rouge": {"aa": 8.0},
    "Fuggles": {"aa": 4.5}, "Cascade": {"aa": 6.0}, "Tettnanger": {"aa": 4.0}
}

# --- STYLE CSS (RETOUR À L'ORIGINAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rye&family=Poppins:wght@300;600&display=swap');
    
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
        font-size: 2.5em;
        text-align: center;
        color: #555;
        font-weight: bold;
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

if 'recette_generee' not in st.session_state:
    st.session_state.recette_generee = False

# --- FONCTIONS MATHÉMATIQUES (NOUVEAU MOTEUR) ---
def round_grain(poids): return round(poids * 20) / 20
def calc_og_from_abv(abv): return (abv / 131.25) + 1.010

def calc_grain_weight(target_sg, volume, efficiency=0.75, malt_yield=78):
    points = (target_sg - 1) * 1000
    return (points * volume) / (malt_yield * efficiency * 3.83)

def calc_hops_weight(target_ibu, alpha_acid, time_min, volume_l, boil_gravity):
    bigness = 1.65 * (0.000125 ** (boil_gravity - 1))
    boil_fact = (1 - (math.e ** (-0.04 * time_min))) / 4.15
    utilization = bigness * boil_fact
    if utilization == 0: return 0
    return (target_ibu * volume_l) / (utilization * (alpha_acid/100) * 1000)

def estimate_color(malt_list, volume):
    mcu = sum([(w * props['ebc']) / volume for w, props in malt_list])
    return 2.93 * (mcu * 4.23) ** 0.6859

# --- PDF COMPACT (1 PAGE) ---
class PDF(FPDF):
    def header(self):
        # On remet le logo dans le PDF aussi s'il existe
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 25)
        self.set_font('Arial', 'B', 24)
        self.cell(0, 15, 'Beer Factory', 0, 1, 'C') # Titre demandé
        self.ln(5)

def create_pdf_compact(data):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    # Infos Styles
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, f"Fiche de Brassage : {data['style']}", ln=True, align='C')
    pdf.set_font("Arial", 'I', 11)
    aromes_txt = ", ".join(data['aromes']).encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 6, f"Profil : {aromes_txt}", ln=True, align='C')
    pdf.ln(5)

    # BANDEAU TECHNIQUE (Compact)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 10)
    info_str = f"Volume: {data['volume']}L  |  ABV: {data['abv']}%  |  OG: {data['og']:.3f}  |  IBU: {int(data['ibu'])}  |  EBC: {int(data['ebc'])}"
    pdf.cell(0, 10, info_str, 1, 1, 'C', fill=True)
    pdf.ln(5)

    # 1. GRAINS
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "1. Grains & Fermentescibles", ln=True)
    pdf.set_font("Arial", '', 10)
    
    h_line = 6
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(25, h_line, "Poids", 1, 0, 'C', True)
    pdf.cell(140, h_line, "Malt", 1, 0, 'L', True)
    pdf.cell(25, h_line, "%", 1, 1, 'C', True)
    
    total_grain = 0
    for grain in data['grains']:
        pdf.cell(25, h_line, f"{grain['poids']} kg", 1, 0, 'C')
        nom_grain = grain['nom'].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(140, h_line, f" {nom_grain}", 1, 0, 'L')
        pdf.cell(25, h_line, f"{grain['ratio']*100:.0f} %", 1, 1, 'C')
        total_grain += grain['poids']
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(165, h_line, f"Total : {total_grain:.2f} kg", 0, 1, 'R')
    pdf.ln(5)

    # 2. HOUBLONS
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "2. Houblonnage", ln=True)
    pdf.set_font("Arial", '', 10)
    
    pdf.cell(25, h_line, "Poids", 1, 0, 'C', True)
    pdf.cell(60, h_line, "Variete", 1, 0, 'L', True)
    pdf.cell(60, h_line, "Usage", 1, 0, 'L', True)
    pdf.cell(45, h_line, "AA%", 1, 1, 'C', True)
    
    for hop in data['houblons']:
        pdf.cell(25, h_line, f"{hop['poids']} g", 1, 0, 'C')
        pdf.cell(60, h_line, f" {hop['nom']}", 1, 0, 'L')
        pdf.cell(60, h_line, f" {hop['usage']}", 1, 0, 'L')
        pdf.cell(45, h_line, f"{hop['aa']} %", 1, 1, 'C')
    pdf.ln(5)

    # 3. PROCESS COMPACT
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "3. Processus", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 8, f"Empatage: {data['eau_emp']:.1f} L (67 C - 60min)", 1)
    pdf.cell(95, 8, f"Rincage: {data['eau_rinc']:.1f} L (75 C)", 1, 1)
    pdf.cell(95, 8, f"Ebullition: 60 min", 1)
    pdf.cell(95, 8, f"Fermentation: ~15 jours", 1, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, f"Levure : {data['levure']}", 0, 1, 'L')

    # Footer
    pdf.set_y(-15)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Genere par Beer Factory - L'application des brasseurs amateurs", 0, 0, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- CHARGEMENT DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("bieres.csv", sep=";", dtype=str)
        df['Degre'] = df['Degre'].str.replace(',', '.').astype(float)
        df['Type_lower'] = df['Type'].str.lower()
        df['Aromes_lower'] = df['Aromes'].str.lower().fillna("")
        return df
    except Exception: return pd.DataFrame()
df = load_data()

# --- HEADER AVEC LOGO (RETOUR LAYOUT ORIGINAL) ---
c_logo1, c_logo2, c_logo3 = st.columns([1, 1, 1])
with c_logo2:
    try:
        st.image("logo.png", use_container_width=True)
    except: pass

st.markdown('<h1 class="main-title">Beer Factory</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Le générateur de recettes</p>', unsafe_allow_html=True)

# ==========================================
# PARTIE 1 : RÉGLAGES (RETOUR TEXTES ORIGINAUX)
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
        style = st.selectbox("Quel style de bière ?", list(definitions_styles.keys()))
        st.info(definitions_styles[style])
        
        c1, c2 = st.columns(2)
        volume = c1.number_input("Volume (Litres)", 5, 100, 20)
        degre_vise = c2.slider("Degré alcool (%)", 3.0, 12.0, 6.0, 0.1)

    with col_droite:
        st.subheader("La Palette Aromatique")
        
        # RETOUR À LA LISTE COMPLÈTE
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
        # Mapping pour le moteur de calcul
        ibu_map = {"Nulle": 5, "Légère": 15, "Moyenne": 30, "Forte": 50, "Extrême": 80}
        ibu_target = ibu_map[amertume]

st.write("") 

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    if st.button("🍺 GÉNÉRER MA RECETTE 🍺", type="primary", use_container_width=True, disabled=trop_d_aromes):
        st.session_state.recette_generee = True

st.divider()

# ==========================================
# PARTIE 2 : LE RÉSULTAT (MOTEUR AMÉLIORÉ)
# ==========================================

if st.session_state.recette_generee:
    
    # 1. LOGIQUE STYLE & INGRÉDIENTS (Adaptée au nouveau moteur)
    malt_base_nom = "Pilsner"; malt_spe_nom = "Blé (Froment)"
    levure = "US-05 (Neutre)"
    houblon_amer = "Magnum"; houblon_arome = "Saaz"
    ratio_base = 0.90; ratio_spe = 0.10
    
    if style == "IPA":
        malt_base_nom = "Pale Ale"; malt_spe_nom = "Carapils"; levure = "Verdant IPA"; ratio_base = 0.93; ratio_spe = 0.07 
    elif style == "Stout":
        malt_base_nom = "Maris Otter"; malt_spe_nom = "Chocolat"; levure = "S-04"; ratio_base = 0.85; ratio_spe = 0.15 
    elif style == "Ambrée":
        malt_base_nom = "Pale Ale"; malt_spe_nom = "Cara Ruby"; levure = "T-58"; ratio_base = 0.85; ratio_spe = 0.15
    elif style == "Blanche":
        malt_base_nom = "Pilsner"; malt_spe_nom = "Blé (Froment)"; levure = "WB-06"; ratio_base = 0.60; ratio_spe = 0.40 
    elif style == "Saison":
        malt_base_nom = "Pilsner"; malt_spe_nom = "Munich"; levure = "Belle Saison"
    elif style == "Sour":
        malt_base_nom = "Pilsner"; malt_spe_nom = "Malt Acide"; levure = "Philly Sour"
    elif style == "Lager":
        malt_base_nom = "Pilsner"; malt_spe_nom = "Vienna"; levure = "W-34/70"

    # Nuances Aromatiques (Override)
    aromes_clean = [a.split(" ")[1] if " " in a else a for a in aromes_selectionnes]
    
    # Malt overrides
    if "Biscuit" in aromes_clean: malt_spe_nom = "Biscuit"
    if "Fumé" in aromes_clean: malt_base_nom = "Fumé"
    if "Caramel" in aromes_clean and style != "Ambrée": malt_spe_nom = "Crystal 150"
    
    # Houblon overrides
    if "Agrumes" in aromes_clean: houblon_arome = "Citra"
    elif "Tropical" in aromes_clean: houblon_arome = "Galaxy"
    elif "Pin" in aromes_clean: houblon_arome = "Simcoe"
    elif "Floral" in aromes_clean: houblon_arome = "Mistral"
    elif "Herbacé" in aromes_clean: houblon_arome = "Hallertau Mittelfrüh"
    elif "Fruits Rouges" in aromes_clean: houblon_arome = "Barbe Rouge"
    elif "Café" in aromes_clean: houblon_arome = "Fuggles"

    # 2. CALCULS SCIENTIFIQUES (CACHE SOUS LE CAPOT)
    target_og = calc_og_from_abv(degre_vise)
    # On récupère les yields dans la DB, si absent défaut à 75
    yield_base = MALTS_DB.get(malt_base_nom, {"yield": 78})['yield']
    yield_spe = MALTS_DB.get(malt_spe_nom, {"yield": 75})['yield']
    
    avg_yield = (yield_base * ratio_base) + (yield_spe * ratio_spe)
    total_grain_mass = calc_grain_weight(target_og, volume, 0.75, avg_yield)
    
    poids_base = round_grain(total_grain_mass * ratio_base)
    poids_spe = round_grain(total_grain_mass * ratio_spe)
    total_grain_affiche = poids_base + poids_spe

    # Calcul Couleur
    ebc_estime = estimate_color([(poids_base, MALTS_DB.get(malt_base_nom, {'ebc':4})), 
                                 (poids_spe, MALTS_DB.get(malt_spe_nom, {'ebc':4}))], volume)

    # Calcul Houblons (Tinseth)
    boil_gravity = target_og * 0.85
    aa_amer = HOPS_DB.get(houblon_amer, {'aa': 10})['aa']
    aa_arome = HOPS_DB.get(houblon_arome, {'aa': 5})['aa']
    
    grammes_amer = calc_hops_weight(ibu_target * 0.8, aa_amer, 60, volume, boil_gravity)
    grammes_arome = calc_hops_weight(ibu_target * 0.2, aa_arome, 5, volume, boil_gravity)

    # Calcul Eau
    eau_empatage = total_grain_affiche * 3.0
    eau_rincage = (volume * 1.15 + total_grain_affiche) - eau_empatage
    if eau_rincage < 0: eau_rincage = 0

    # 3. AFFICHAGE RÉSULTAT (DESIGN ORIGINAL MAIS DONNÉES PRÉCISES)
    st.header(f"📜 Fiche Technique : {style} {', '.join(aromes_clean)}")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("### 🌾 Bill of Materials")
            st.write(f"**Total Grains : {total_grain_affiche:.2f} kg** (EBC: {int(ebc_estime)})")
            st.write(f"- **{poids_base:.2f} kg** : {malt_base_nom}")
            st.write(f"- **{poids_spe:.2f} kg** : {malt_spe_nom}")
            st.markdown("---")
            st.markdown("### 🦠 Levure")
            st.write(f"**1 sachet** : **{levure}**")

    with c2:
        with st.container(border=True):
            st.markdown("### 🌿 Houblonnage")
            st.write(f"- **{int(grammes_amer)}g** {houblon_amer} (Amérisant - 60min)")
            st.write(f"- **{int(grammes_arome)}g** {houblon_arome} (Aromatique - 5min)")
            st.markdown(f"**IBU Cible : {int(ibu_target)}**")

    # PROCESS
    st.subheader("⏳ Profil de Brassage & Volumes d'Eau")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    col_p1.metric("1. Empâtage (60 min)", f"67°C", f"Eau: {eau_empatage:.1f} L")
    col_p2.metric("2. Rinçage", "75°C", f"Eau: {eau_rincage:.1f} L")
    col_p3.metric("3. Ébullition", f"60 min", "100°C")
    col_p4.metric("4. Fermentation", f"20°C", "~15 jours")

    # 4. EXPORT PDF (COMPACT 1 PAGE)
    st.write("")
    
    # Prep data pour le PDF compact
    recette_data = {
        "style": style, "aromes": aromes_clean, "volume": volume, "abv": degre_vise,
        "og": target_og, "ibu": ibu_target, "ebc": ebc_estime,
        "grains": [
            {"nom": malt_base_nom, "poids": poids_base, "ratio": ratio_base},
            {"nom": malt_spe_nom, "poids": poids_spe, "ratio": ratio_spe}
        ],
        "houblons": [
            {"nom": houblon_amer, "poids": int(grammes_amer), "usage": "Ebu 60min", "aa": aa_amer},
            {"nom": houblon_arome, "poids": int(grammes_arome), "usage": "Arome 5min", "aa": aa_arome}
        ],
        "eau_emp": eau_empatage, "eau_rinc": eau_rincage, "levure": levure
    }
    
    pdf_bytes = create_pdf_compact(recette_data)
    
    st.download_button(label="📥 TÉLÉCHARGER MA RECETTE EN PDF", 
                       data=pdf_bytes, 
                       file_name=f"BeerFactory_{style}.pdf", 
                       mime='application/pdf', 
                       use_container_width=True)

    st.divider()

    # 5. MATCHING (Code Original)
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
import streamlit as st
from fpdf import FPDF
import os
import math

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Beer Factory", page_icon="🍺", layout="wide")

# --- DATA (MOTEUR INCHANGÉ) ---
MALTS_DB = {
    "Pilsner": {"yield": 78, "ebc": 3.5}, "Pale Ale": {"yield": 79, "ebc": 6.5},
    "Maris Otter": {"yield": 78, "ebc": 5.0}, "Munich": {"yield": 76, "ebc": 15},
    "Vienna": {"yield": 76, "ebc": 8}, "Blé (Froment)": {"yield": 80, "ebc": 4},
    "Carapils": {"yield": 72, "ebc": 3}, "Malt Acide": {"yield": 50, "ebc": 4},
    "Cara Ruby": {"yield": 74, "ebc": 50}, "Crystal 150": {"yield": 70, "ebc": 150},
    "Chocolat": {"yield": 65, "ebc": 900}, "Orge Grillé": {"yield": 65, "ebc": 1200},
    "Fumé": {"yield": 77, "ebc": 6}, "Biscuit": {"yield": 75, "ebc": 50}
}
HOPS_DB = {
    "Magnum": {"aa": 12.0}, "Saaz": {"aa": 3.5}, "Citra": {"aa": 13.0},
    "Amarillo": {"aa": 9.0}, "Mosaic": {"aa": 12.0}, "Galaxy": {"aa": 14.0},
    "Simcoe": {"aa": 13.0}, "Chinook": {"aa": 13.0}, "Mistral": {"aa": 6.5},
    "Hallertau Mittelfrüh": {"aa": 4.0}, "Barbe Rouge": {"aa": 8.0},
    "Fuggles": {"aa": 4.5}, "Cascade": {"aa": 6.0}, "Tettnanger": {"aa": 4.0}
}

# --- TEMPLATE CSS "MODERN CRAFT" ---
st.markdown("""
    <style>
    /* Import Google Fonts : Raleway (Titres) et Lato (Texte) */
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Raleway:wght@400;600;800&display=swap');
    
    /* BACKGROUND GENERAL */
    .stApp {
        background-color: #f8f9fa; /* Gris très clair moderne */
    }
    
    /* TITRES */
    h1, h2, h3 {
        font-family: 'Raleway', sans-serif !important;
        color: #2c3e50;
        font-weight: 800;
    }
    
    h1 { letter-spacing: -1px; font-size: 3.5rem !important; }
    
    /* CUSTOM CARDS (Pour remplacer les bordures par défaut) */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        /* On ne peut pas cibler parfaitement les containers, mais on style le global */
    }
    
    /* BOUTON PRINCIPAL */
    div.stButton > button {
        background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
        color: white !important;
        border: none;
        border-radius: 50px; /* Bouton arrondi moderne */
        padding: 0.8rem 2rem;
        font-family: 'Raleway', sans-serif;
        font-weight: 600;
        font-size: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(230, 126, 34, 0.4);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(230, 126, 34, 0.6);
    }
    
    /* INPUTS & SLIDERS */
    .stSelectbox label, .stNumberInput label, .stSlider label {
        font-family: 'Raleway', sans-serif;
        font-weight: 600;
        color: #34495e;
        font-size: 1rem;
    }
    
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
    }

    /* CUSTOM METRICS */
    div[data-testid="stMetricValue"] {
        font-family: 'Lato', sans-serif;
        font-weight: 300;
        color: #e67e22;
    }
    
    /* PILLS (Tags arômes) */
    span[data-baseweb="tag"] {
        background-color: #e67e2220 !important;
        border: 1px solid #e67e22 !important;
    }
    
    /* SÉPARATEURS */
    hr { margin: 3rem 0; border-color: #e0e0e0; }

    </style>
""", unsafe_allow_html=True)

if 'recette_generee' not in st.session_state:
    st.session_state.recette_generee = False

# --- FONCTIONS MATHÉMATIQUES ---
def round_grain(poids): return round(poids * 20) / 20
def calc_og_from_abv(abv): return (abv / 131.25) + 1.010
def calc_grain_weight(target_sg, volume, efficiency, malt_yield=78):
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

# --- PDF GENERATOR (Compact) ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"): self.image("logo.png", 10, 8, 25)
        self.set_font('Arial', 'B', 24)
        self.cell(0, 15, 'BEER FACTORY', 0, 1, 'C')
        self.ln(5)

def create_pdf_compact(data):
    pdf = PDF(); pdf.add_page(); pdf.set_auto_page_break(auto=True, margin=10)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, f"Fiche de Brassage : {data['style']}", ln=True, align='C')
    pdf.set_font("Arial", 'I', 11)
    aromes_txt = ", ".join(data['aromes']).encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 6, f"Profil : {aromes_txt}", ln=True, align='C')
    pdf.ln(5)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    info_str = f"Vol: {data['volume']}L | ABV: {data['abv']}% | OG: {data['og']:.3f} | IBU: {int(data['ibu'])} | EBC: {int(data['ebc'])} | Eff: {int(data['eff']*100)}%"
    pdf.cell(0, 10, info_str, 1, 1, 'C', fill=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "1. Grains & Fermentescibles", ln=True)
    pdf.set_font("Arial", '', 10)
    h_line = 6
    pdf.set_fill_color(250, 250, 250)
    pdf.cell(25, h_line, "Poids", 1, 0, 'C', True); pdf.cell(140, h_line, "Malt", 1, 0, 'L', True); pdf.cell(25, h_line, "%", 1, 1, 'C', True)
    total_grain = 0
    for grain in data['grains']:
        pdf.cell(25, h_line, f"{grain['poids']} kg", 1, 0, 'C')
        nom_grain = grain['nom'].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(140, h_line, f" {nom_grain}", 1, 0, 'L')
        pdf.cell(25, h_line, f"{grain['ratio']*100:.0f} %", 1, 1, 'C')
        total_grain += grain['poids']
    pdf.set_font("Arial", 'B', 10); pdf.cell(165, h_line, f"Total : {total_grain:.2f} kg", 0, 1, 'R'); pdf.ln(5)

    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "2. Houblonnage", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(25, h_line, "Poids", 1, 0, 'C', True); pdf.cell(60, h_line, "Variete", 1, 0, 'L', True); pdf.cell(60, h_line, "Usage", 1, 0, 'L', True); pdf.cell(45, h_line, "AA%", 1, 1, 'C', True)
    for hop in data['houblons']:
        pdf.cell(25, h_line, f"{hop['poids']} g", 1, 0, 'C')
        pdf.cell(60, h_line, f" {hop['nom']}", 1, 0, 'L')
        pdf.cell(60, h_line, f" {hop['usage']}", 1, 0, 'L')
        pdf.cell(45, h_line, f"{hop['aa']} %", 1, 1, 'C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "3. Processus", ln=True); pdf.set_font("Arial", '', 10)
    pdf.cell(95, 8, f"Empatage: {data['eau_emp']:.1f} L (67 C - 60min)", 1)
    pdf.cell(95, 8, f"Rincage: {data['eau_rinc']:.1f} L (75 C)", 1, 1)
    pdf.cell(95, 8, f"Ebullition: 60 min (100 C)", 1)
    pdf.cell(95, 8, f"Fermentation: ~15 jours", 1, 1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, f"Levure : {data['levure']}", 0, 1, 'L')
    pdf.set_y(-15); pdf.set_font("Arial", 'I', 8); pdf.cell(0, 10, "Genere par Beer Factory", 0, 0, 'C')
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# UI HEADER
# ==========================================
c_logo1, c_logo2, c_logo3 = st.columns([1, 1, 1])
with c_logo2:
    try: st.image("logo.png", use_container_width=True)
    except: pass

st.markdown('<h1 style="text-align: center;">BEER FACTORY</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-family: Raleway; color: #7f8c8d; margin-top: -20px; font-size: 1.2rem;">L\'atelier de création de recettes</p>', unsafe_allow_html=True)
st.write("")
st.write("")

# ==========================================
# PARTIE 1 : CONFIGURATION (Look Modern Cards)
# ==========================================

with st.container():
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("### 1. La Base")
        with st.container(border=True): # Cadre blanc propre
            definitions_styles = {
                "Blonde": "☀️ La Blonde : Dorée, maltée, accessible.",
                "IPA": "🌲 L'IPA : Houblonnée, amère et aromatique.",
                "Stout": "☕ Le Stout : Noire, torréfiée, notes de café.",
                "Ambrée": "🍂 L'Ambrée : Couleur cuivre, notes de caramel.",
                "Blanche": "☁️ La Blanche : Blé, trouble, agrumes.",
                "Saison": "🚜 La Saison : Rustique, sèche et poivrée.",
                "Sour": "🍋 La Sour : Acidulée et rafraîchissante.",
                "Lager": "❄️ La Lager : Fermentation basse, nette."
            }
            style = st.selectbox("Style de bière", list(definitions_styles.keys()))
            st.caption(definitions_styles[style])
            
            c_v, c_a = st.columns(2)
            volume = c_v.number_input("Volume (Litres)", 5, 100, 20)
            degre_vise = c_a.slider("Degré alcool (%)", 3.0, 12.0, 6.0, 0.1)

    with col2:
        st.markdown("### 2. Le Caractère")
        with st.container(border=True): # Cadre blanc propre
            options_aromes = ["🍊 Agrumes", "🥭 Tropical", "🌲 Pin", "🍌 Banane", "☕ Café", "🍫 Chocolat", "🍮 Caramel", "🍪 Biscuit", "🥓 Fumé", "🌶️ Épices", "🌸 Floral"]
            aromes_selectionnes = st.pills("Profil Aromatique (Max 2)", options_aromes, selection_mode="multi")
            
            trop_d_aromes = len(aromes_selectionnes) > 2
            if trop_d_aromes: st.error("Choisissez 2 arômes maximum.")
            
            st.write("")
            amertume = st.select_slider("Niveau d'Amertume", options=["Nulle", "Légère", "Moyenne", "Forte", "Extrême"])
            ibu_map = {"Nulle": 5, "Légère": 15, "Moyenne": 30, "Forte": 50, "Extrême": 80}
            ibu_target = ibu_map[amertume]

st.write("")
st.write("")
c_b1, c_b2, c_b3 = st.columns([1, 2, 1])
with c_b2:
    if st.button("✨ Concevoir la Recette", type="primary", use_container_width=True, disabled=trop_d_aromes):
        st.session_state.recette_generee = True

# ==========================================
# PARTIE 2 : RÉSULTATS
# ==========================================

if st.session_state.recette_generee:
    st.markdown("---")
    
    # 0. CONSTANTES
    efficacite = 0.75 

    # 1. LOGIQUE METIER (Identique)
    malt_base_nom = "Pilsner"; malt_spe_nom = "Blé (Froment)"; levure = "US-05 (Neutre)"
    houblon_amer = "Magnum"; houblon_arome = "Saaz"
    ratio_base = 0.90; ratio_spe = 0.10
    
    if style == "IPA": malt_base_nom="Pale Ale"; malt_spe_nom="Carapils"; levure="Verdant IPA"; ratio_base=0.93; ratio_spe=0.07 
    elif style == "Stout": malt_base_nom="Maris Otter"; malt_spe_nom="Chocolat"; levure="S-04"; ratio_base=0.85; ratio_spe=0.15 
    elif style == "Ambrée": malt_base_nom="Pale Ale"; malt_spe_nom="Cara Ruby"; levure="T-58"; ratio_base=0.85; ratio_spe=0.15
    elif style == "Blanche": malt_base_nom="Pilsner"; malt_spe_nom="Blé (Froment)"; levure="WB-06"; ratio_base=0.60; ratio_spe=0.40 
    elif style == "Saison": malt_base_nom="Pilsner"; malt_spe_nom="Munich"; levure="Belle Saison"
    elif style == "Sour": malt_base_nom="Pilsner"; malt_spe_nom="Malt Acide"; levure="Philly Sour"
    elif style == "Lager": malt_base_nom="Pilsner"; malt_spe_nom="Vienna"; levure="W-34/70"

    aromes_clean = [a.split(" ")[1] if " " in a else a for a in aromes_selectionnes]
    if "Biscuit" in aromes_clean: malt_spe_nom = "Biscuit"
    if "Fumé" in aromes_clean: malt_base_nom = "Fumé"
    if "Caramel" in aromes_clean and style != "Ambrée": malt_spe_nom = "Crystal 150"
    if "Agrumes" in aromes_clean: houblon_arome = "Citra"
    elif "Tropical" in aromes_clean: houblon_arome = "Galaxy"
    elif "Pin" in aromes_clean: houblon_arome = "Simcoe"
    elif "Floral" in aromes_clean: houblon_arome = "Mistral"
    elif "Herbacé" in aromes_clean: houblon_arome = "Hallertau Mittelfrüh"
    elif "Fruits Rouges" in aromes_clean: houblon_arome = "Barbe Rouge"
    elif "Café" in aromes_clean: houblon_arome = "Fuggles"

    # 2. CALCULS
    target_og = calc_og_from_abv(degre_vise)
    avg_yield = (MALTS_DB.get(malt_base_nom, {"yield":78})['yield'] * ratio_base) + (MALTS_DB.get(malt_spe_nom, {"yield":75})['yield'] * ratio_spe)
    total_grain_mass = calc_grain_weight(target_og, volume, efficacite, avg_yield)
    poids_base = round_grain(total_grain_mass * ratio_base); poids_spe = round_grain(total_grain_mass * ratio_spe)
    total_grain_affiche = poids_base + poids_spe
    ebc_estime = estimate_color([(poids_base, MALTS_DB.get(malt_base_nom, {'ebc':4})), (poids_spe, MALTS_DB.get(malt_spe_nom, {'ebc':4}))], volume)
    boil_gravity = target_og * 0.85
    aa_amer = HOPS_DB.get(houblon_amer, {'aa':10})['aa']; aa_arome = HOPS_DB.get(houblon_arome, {'aa':5})['aa']
    grammes_amer = calc_hops_weight(ibu_target * 0.8, aa_amer, 60, volume, boil_gravity)
    grammes_arome = calc_hops_weight(ibu_target * 0.2, aa_arome, 5, volume, boil_gravity)
    eau_empatage = total_grain_affiche * 3.0; eau_rincage = (volume * 1.15 + total_grain_affiche) - eau_empatage
    if eau_rincage < 0: eau_rincage = 0

    # 3. AFFICHAGE MODERNE
    st.markdown(f"<h2 style='text-align: center; color: #d35400;'>{style.upper()} {', '.join(aromes_clean).upper()}</h2>", unsafe_allow_html=True)
    st.write("")

    col_res1, col_res2 = st.columns([2, 1.2], gap="large")
    
    with col_res1:
        with st.container(border=True):
            st.markdown("#### 🌾 Grains & Fermentescibles")
            st.markdown(f"**Total : {total_grain_affiche:.2f} kg** <span style='color:gray; font-size:0.8em'>(Eff. {int(efficacite*100)}% | EBC {int(ebc_estime)})</span>", unsafe_allow_html=True)
            st.write(f"• **{poids_base:.2f} kg** : {malt_base_nom}")
            st.write(f"• **{poids_spe:.2f} kg** : {malt_spe_nom}")
            
            st.markdown("#### 🦠 Levure")
            st.write(f"• Souche : **{levure}** (1 sachet)")

        with st.container(border=True):
            st.markdown("#### 🌿 Houblons")
            st.write(f"• **{int(grammes_amer)}g** {houblon_amer} (Amérisant - 60min)")
            st.write(f"• **{int(grammes_arome)}g** {houblon_arome} (Aromatique - 5min)")
    
    with col_res2:
        st.markdown("#### ⏳ Processus")
        with st.container(border=True):
            st.metric("1. Empâtage (60 min)", "67°C", f"{eau_empatage:.1f} L d'eau")
            st.divider()
            st.metric("2. Rinçage", "75°C", f"{eau_rincage:.1f} L d'eau")
            st.divider()
            # Inversion demandée : 100°C en gros
            st.metric("3. Ébullition", "100°C", "60 min")
            st.divider()
            st.metric("4. Fermentation", "20°C", "~15 jours")

    st.write("")
    
    recette_data = {
        "style": style, "aromes": aromes_clean, "volume": volume, "abv": degre_vise,
        "og": target_og, "ibu": ibu_target, "ebc": ebc_estime, "eff": efficacite,
        "grains": [{"nom": malt_base_nom, "poids": poids_base, "ratio": ratio_base}, {"nom": malt_spe_nom, "poids": poids_spe, "ratio": ratio_spe}],
        "houblons": [{"nom": houblon_amer, "poids": int(grammes_amer), "usage": "Ebu 60min", "aa": aa_amer}, {"nom": houblon_arome, "poids": int(grammes_arome), "usage": "Arome 5min", "aa": aa_arome}],
        "eau_emp": eau_empatage, "eau_rinc": eau_rincage, "levure": levure
    }
    
    pdf_bytes = create_pdf_compact(recette_data)
    st.download_button(label="📥 Télécharger la Fiche (PDF)", data=pdf_bytes, file_name=f"BeerFactory_{style}.pdf", mime='application/pdf', use_container_width=True)
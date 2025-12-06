import streamlit as st
from fpdf import FPDF
import os
import math

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Beer Factory", page_icon="🍺", layout="wide")

# --- MOTEUR DE CALCULS ---
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

# --- STYLE CSS CORRECTIF & ARCHITECTURAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rye&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    :root {
        --couleur-fond-logo: #FCF6ED; 
        --primary-amber: #C27818;
        --dark-brown: #2b2118;
        --text-dark: #1a120b;
    }

    /* 1. CADRE EXTERIEUR MASSIF (FIXÉ) */
    .stApp {
        background-color: var(--couleur-fond-logo);
        color: var(--text-dark);
        font-family: 'Roboto', sans-serif;
        
        /* Force le cadre, padding pour éviter que le contenu touche le cadre */
        border: 50px solid var(--dark-brown);
        box-shadow: inset 0 0 0 5px var(--primary-amber);
        padding: 20px; 
    }
    
    /* Adaptation mobile : on réduit le cadre sinon c'est illisible */
    @media (max-width: 640px) {
        .stApp {
            border: 15px solid var(--dark-brown);
            padding: 5px;
        }
    }

    /* 2. MODULES INTERNES (CADRES) */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border: 6px solid var(--dark-brown) !important;
        box-shadow: inset 0 0 0 2px var(--primary-amber) !important;
        border-radius: 4px;
        background-color: rgba(255,255,255, 0.85) !important;
        padding: 20px !important;
        margin-bottom: 20px;
    }

    /* TITRES */
    h1 {
        font-family: 'Rye', serif !important;
        color: var(--dark-brown) !important; 
        text-transform: uppercase; 
        font-weight: 400;
        letter-spacing: 1px;
        text-align: center !important;
        font-size: 3rem !important; 
        line-height: 1.1;
        margin-bottom: -10px !important;
    }
    
    h2, h3 { 
        font-family: 'Rye', serif !important;
        color: var(--dark-brown) !important; 
        text-transform: uppercase; 
        letter-spacing: 1px;
    }
    
    /* SOUS-TITRES */
    .subheader-text {
        color: var(--primary-amber); font-weight: bold; font-size: 1.2em;
        margin-bottom: 15px; border-bottom: 3px solid var(--primary-amber);
        padding-bottom: 5px; display: inline-block; text-transform: uppercase;
        font-family: 'Rye', serif;
    }

    /* BOUTONS GENERAUX */
    div.stButton > button {
        background-color: var(--primary-amber); color: white !important;
        border: 3px solid var(--dark-brown);
        border-radius: 4px; padding: 0.8rem 1.5rem;
        font-family: 'Rye', serif; text-transform: uppercase; letter-spacing: 1.5px;
        box-shadow: 4px 4px 0px var(--dark-brown);
        font-size: 1.3rem;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        transform: translate(2px, 2px);
        box-shadow: 2px 2px 0px var(--dark-brown);
        background-color: #d35400;
    }

    /* INPUTS */
    .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] {
        background-color: #ffffff !important;
        color: var(--dark-brown) !important;
        border: 2px solid #bcaaa4;
        border-radius: 4px;
    }
    input[type="number"] { color: var(--dark-brown) !important; font-weight: bold; }
    
    .stSelectbox label, .stNumberInput label, .stSlider label {
        color: var(--dark-brown) !important; 
        font-weight: bold;
        font-family: 'Roboto', sans-serif;
        text-transform: uppercase;
    }

    div[data-baseweb="slider"] div[role="slider"] { background-color: var(--primary-amber) !important; }
    div[data-baseweb="slider"] > div > div > div { background-color: var(--primary-amber) !important; }

    /* --- CORRECTION CRITIQUE ST.PILLS (AROMES) --- */
    
    /* 1. État par défaut (Non sélectionné) */
    [data-testid="stPills"] button {
        background-color: #ffffff !important; /* Blanc */
        border: 2px solid var(--dark-brown) !important;
        transition: all 0.2s;
    }
    
    /* Texte par défaut */
    [data-testid="stPills"] button p {
        color: var(--dark-brown) !important; /* Marron foncé */
        font-weight: 700 !important;
        font-family: 'Roboto', sans-serif;
    }
    
    /* 2. État SÉLECTIONNÉ */
    [data-testid="stPills"] button[aria-selected="true"] {
        background-color: var(--primary-amber) !important; /* Ambre */
        border-color: var(--dark-brown) !important;
    }
    
    /* Texte quand sélectionné */
    [data-testid="stPills"] button[aria-selected="true"] p {
        color: #ffffff !important; /* Blanc */
    }
    
    /* 3. Survol */
    [data-testid="stPills"] button:hover {
        border-color: var(--primary-amber) !important;
        transform: scale(1.02);
    }

    /* METRICS */
    div[data-testid="stMetricLabel"] { color: var(--dark-brown); font-weight: 700; text-transform: uppercase;}
    div[data-testid="stMetricValue"] { color: var(--primary-amber); font-weight: 800; font-size: 1.8rem; font-family: 'Rye', serif; }
    
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
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

# --- PDF GENERATOR ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"): self.image("logo.png", 10, 8, 25)
        self.set_font('Arial', 'B', 20)
        self.cell(0, 15, 'BEER FACTORY', 0, 1, 'C')
        self.ln(5)

def create_pdf_compact(data):
    pdf = PDF(); pdf.add_page(); pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", 'B', 14); pdf.cell(0, 8, f"Fiche de Production : {data['style'].upper()}", ln=True, align='C')
    pdf.set_font("Arial", 'I', 11)
    aromes_txt = ", ".join(data['aromes']).encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 6, f"Profil : {aromes_txt}", ln=True, align='C'); pdf.ln(5)
    pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 10)
    info_str = f"Vol: {data['volume']}L | ABV: {data['abv']}% | OG: {data['og']:.3f} | IBU: {int(data['ibu'])} | EBC: {int(data['ebc'])} | Eff: {int(data['eff']*100)}%"
    pdf.cell(0, 10, info_str, 1, 1, 'C', fill=True); pdf.ln(8)
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "1. Grains & Fermentescibles", ln=True); pdf.set_font("Arial", '', 10)
    h_line = 7; pdf.set_fill_color(245, 245, 245)
    pdf.cell(25, h_line, "Poids", 1, 0, 'C', True); pdf.cell(140, h_line, "Malt", 1, 0, 'L', True); pdf.cell(25, h_line, "%", 1, 1, 'C', True)
    total_grain = 0
    for grain in data['grains']:
        pdf.cell(25, h_line, f"{grain['poids']} kg", 1, 0, 'C'); nom_grain = grain['nom'].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(140, h_line, f" {nom_grain}", 1, 0, 'L'); pdf.cell(25, h_line, f"{grain['ratio']*100:.0f} %", 1, 1, 'C'); total_grain += grain['poids']
    pdf.set_font("Arial", 'B', 10); pdf.cell(165, h_line, f"Total : {total_grain:.2f} kg", 0, 1, 'R'); pdf.ln(8)
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "2. Houblonnage", ln=True); pdf.set_font("Arial", '', 10)
    pdf.cell(25, h_line, "Poids", 1, 0, 'C', True); pdf.cell(60, h_line, "Variete", 1, 0, 'L', True); pdf.cell(60, h_line, "Usage", 1, 0, 'L', True); pdf.cell(45, h_line, "AA%", 1, 1, 'C', True)
    for hop in data['houblons']:
        pdf.cell(25, h_line, f"{hop['poids']} g", 1, 0, 'C'); pdf.cell(60, h_line, f" {hop['nom']}", 1, 0, 'L'); pdf.cell(60, h_line, f" {hop['usage']}", 1, 0, 'L'); pdf.cell(45, h_line, f"{hop['aa']} %", 1, 1, 'C')
    pdf.ln(8)
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "3. Processus", ln=True); pdf.set_font("Arial", '', 10)
    pdf.cell(95, 8, f"Empatage: {data['eau_emp']:.1f} L (67 C - 60min)", 1); pdf.cell(95, 8, f"Rincage: {data['eau_rinc']:.1f} L (75 C)", 1, 1)
    pdf.cell(95, 8, f"Ebullition: 60 min (100 C)", 1); pdf.cell(95, 8, f"Fermentation: ~15 jours (20 C)", 1, 1); pdf.ln(8)
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, f"Levure : {data['levure']}", 0, 1, 'L')
    pdf.set_y(-15); pdf.set_font("Arial", 'I', 8); pdf.cell(0, 10, "Systeme Beer Factory", 0, 0, 'C')
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# HEADER
# ==========================================

st.markdown('<h1 style="text-align: center;">BEER FACTORY</h1>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([2, 0.8, 2]) 
with c2:
    try: st.image("logo.png", use_container_width=True)
    except: pass

st.markdown('<p style="text-align: center; color: #C27818; margin-top: -15px; font-family: Rye; letter-spacing: 2px; text-transform: uppercase;">LE GÉNÉRATEUR DE RECETTES DE BIÈRES</p>', unsafe_allow_html=True)
st.write("")

# ==========================================
# MODULE 1 : CONFIGURATION
# ==========================================

with st.container(border=True): 
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown('<p class="subheader-text">1. TYPE DE BIÈRE</p>', unsafe_allow_html=True)
        definitions_styles = {
            "Blonde": "☀️ Dorée, maltée, accessible.",
            "IPA": "🌲 Houblonnée, amère et aromatique.",
            "Stout": "☕ Noire, torréfiée, notes de café.",
            "Ambrée": "🍂 Couleur cuivre, notes de caramel.",
            "Blanche": "☁️ Blé, trouble, agrumes.",
            "Saison": "🚜 Rustique, sèche et poivrée.",
            "Lager": "❄️ Fermentation basse, nette."
        }
        style = st.selectbox("Style", list(definitions_styles.keys()))
        st.caption(definitions_styles[style])
        
        c_v, c_a = st.columns(2)
        volume = c_v.number_input("Volume (L)", 5, 100, 20)
        degre_vise = c_a.slider("Alcool (%)", 3.0, 12.0, 6.0, 0.1)
        
        st.write("")
        st.write("")
        amertume = st.select_slider("Amertume Ciblée", options=["Nulle", "Légère", "Moyenne", "Forte", "Extrême"])
        ibu_map = {"Nulle": 5, "Légère": 15, "Moyenne": 30, "Forte": 50, "Extrême": 80}
        ibu_target = ibu_map[amertume]

    with col2:
        st.markdown('<p class="subheader-text">2. CHOIX DES ARÔMES</p>', unsafe_allow_html=True)
        
        options_aromes = ["🍊 Agrumes", "🥭 Tropical", "🌲 Pin", "🍌 Banane", "☕ Café", "🍫 Chocolat", "🍮 Caramel", "🍪 Biscuit", "🥓 Fumé", "🌶️ Épices", "🌸 Floral"]
        
        # UTILISATION DE ST.PILLS (BOUTONS CLIQUABLES)
        # selection_mode="multi" permet de sélectionner plusieurs
        aromes_selectionnes = st.pills(
            "Sélectionnez 2 arômes maximum :",
            options_aromes,
            selection_mode="multi"
        )
        
        trop_d_aromes = len(aromes_selectionnes) > 2
        if trop_d_aromes:
            st.error("⚠️ Trop d'arômes ! Veuillez en désélectionner pour n'en garder que 2.")

# ==========================================
# TRANSITION
# ==========================================
st.write("")
try:
    st.image("frise.png", use_container_width=True)
except:
    st.markdown("---") 

st.write("")

c_b1, c_b2, c_b3 = st.columns([1, 2, 1])
with c_b2:
    if st.button("🍺 GÉNÉRER MA RECETTE 🍺", type="primary", use_container_width=True, disabled=trop_d_aromes):
        st.session_state.recette_generee = True

st.write("")

# ==========================================
# MODULE 2 : RÉSULTATS
# ==========================================

if st.session_state.recette_generee:
    
    efficacite = 0.75 
    malt_base_nom = "Pilsner"; malt_spe_nom = "Blé (Froment)"; levure = "US-05 (Neutre)"; houblon_amer = "Magnum"; houblon_arome = "Saaz"; ratio_base = 0.90; ratio_spe = 0.10
    if style == "IPA": malt_base_nom="Pale Ale"; malt_spe_nom="Carapils"; levure="Verdant IPA"; ratio_base=0.93; ratio_spe=0.07 
    elif style == "Stout": malt_base_nom="Maris Otter"; malt_spe_nom="Chocolat"; levure="S-04"; ratio_base=0.85; ratio_spe=0.15 
    elif style == "Ambrée": malt_base_nom="Pale Ale"; malt_spe_nom="Cara Ruby"; levure="T-58"; ratio_base=0.85; ratio_spe=0.15
    elif style == "Blanche": malt_base_nom="Pilsner"; malt_spe_nom="Blé (Froment)"; levure="WB-06"; ratio_base=0.60; ratio_spe=0.40 
    elif style == "Saison": malt_base_nom="Pilsner"; malt_spe_nom="Munich"; levure="Belle Saison"
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
    
    recette_data = {
        "style": style, "aromes": aromes_clean, "volume": volume, "abv": degre_vise,
        "og": target_og, "ibu": ibu_target, "ebc": ebc_estime, "eff": efficacite,
        "grains": [{"nom": malt_base_nom, "poids": poids_base, "ratio": ratio_base}, {"nom": malt_spe_nom, "poids": poids_spe, "ratio": ratio_spe}],
        "houblons": [{"nom": houblon_amer, "poids": int(grammes_amer), "usage": "Ebu 60min", "aa": aa_amer}, {"nom": houblon_arome, "poids": int(grammes_arome), "usage": "Arome 5min", "aa": aa_arome}],
        "eau_emp": eau_empatage, "eau_rinc": eau_rincage, "levure": levure
    }
    
    with st.container(border=True): 
        st.markdown(f"<h2 style='text-align: center; border-bottom: none;'>FICHE DE PRODUCTION : {style.upper()}</h2>", unsafe_allow_html=True)
        if aromes_clean: st.caption(f"<p style='text-align: center; font-style:italic;'>Notes : {', '.join(aromes_clean)}</p>", unsafe_allow_html=True)
        st.write("")

        col_res1, col_res2 = st.columns([2, 1.5], gap="medium")
        
        with col_res1:
            st.markdown('<p class="subheader-text">🌾 GRAINS & FERMENTESCIBLES</p>', unsafe_allow_html=True)
            st.markdown(f"**Total : {total_grain_affiche:.2f} kg** <span style='color:#555; font-size:0.9em'>(Eff. {int(efficacite*100)}% | EBC {int(ebc_estime)})</span>", unsafe_allow_html=True)
            st.write(f"• **{poids_base:.2f} kg** : {malt_base_nom}")
            st.write(f"• **{poids_spe:.2f} kg** : {malt_spe_nom}")
            
            st.write("")
            st.markdown('<p class="subheader-text">🦠 LEVURE</p>', unsafe_allow_html=True)
            st.write(f"• Souche : **{levure}** (1 sachet)")

            st.write("")
            st.markdown('<p class="subheader-text">🌿 HOUBLONS</p>', unsafe_allow_html=True)
            st.write(f"• **{int(grammes_amer)}g** {houblon_amer} (Amérisant - 60min)")
            st.write(f"• **{int(grammes_arome)}g** {houblon_arome} (Aromatique - 5min)")
            st.caption(f"IBU Cible : {int(ibu_target)}")
        
        with col_res2:
            st.markdown('<p class="subheader-text">⏳ PROCESSUS</p>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.metric("1. Empâtage", "60 min", "67°C")
            c2.metric("Eau", f"{eau_empatage:.1f} L")
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("2. Rinçage", "Batch", "75°C")
            c2.metric("Eau", f"{eau_rincage:.1f} L")
            st.divider()
            st.metric("3. Ébullition (100°C)", "60 min")
            st.divider()
            st.metric("4. Fermentation (20°C)", "~15 jours")

        st.write("")
        st.divider()
        pdf_bytes = create_pdf_compact(recette_data)
        st.download_button(label="📥 TÉLÉCHARGER LA FICHE (PDF)", data=pdf_bytes, file_name=f"BeerFactory_{style}.pdf", mime='application/pdf', use_container_width=True)
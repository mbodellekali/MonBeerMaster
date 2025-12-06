import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import math

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="Beer Factory", page_icon="🏭", layout="wide")

# --- DATA: BASE DE DONNÉES INGRÉDIENTS ---
MALTS_DB = {
    "Pilsner": {"yield": 78, "ebc": 3.5},
    "Pale Ale": {"yield": 79, "ebc": 6.5},
    "Maris Otter": {"yield": 78, "ebc": 5.0},
    "Munich": {"yield": 76, "ebc": 15},
    "Vienna": {"yield": 76, "ebc": 8},
    "Blé (Froment)": {"yield": 80, "ebc": 4},
    "Carapils": {"yield": 72, "ebc": 3},
    "Crystal 150": {"yield": 70, "ebc": 150},
    "Chocolat": {"yield": 65, "ebc": 900},
    "Orge Grillé": {"yield": 65, "ebc": 1200},
    "Acide": {"yield": 50, "ebc": 4},
    "Fumé": {"yield": 77, "ebc": 6},
    "Biscuit": {"yield": 75, "ebc": 50}
}

HOPS_DB = {
    "Magnum": {"aa": 12.0},
    "Saaz": {"aa": 3.5},
    "Citra": {"aa": 13.0},
    "Amarillo": {"aa": 9.0},
    "Mosaic": {"aa": 12.0},
    "Galaxy": {"aa": 14.0},
    "Simcoe": {"aa": 13.0},
    "Chinook": {"aa": 13.0},
    "Mistral": {"aa": 6.5},
    "Hallertau": {"aa": 4.0},
    "Barbe Rouge": {"aa": 8.0},
    "Fuggles": {"aa": 4.5},
    "Cascade": {"aa": 6.0}
}

# --- STYLE CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;700&family=Roboto:wght@300;400&display=swap');
    
    .main-title { font-family: 'Oswald', sans-serif; font-size: 4em; text-align: center; color: #2c3e50; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 0px; }
    .sub-title { font-family: 'Roboto', sans-serif; font-size: 1.2em; text-align: center; color: #7f8c8d; letter-spacing: 1px; margin-bottom: 30px; }
    
    h1, h2, h3 { font-family: 'Oswald', sans-serif !important; color: #34495e; }
    
    div.stButton > button { 
        background-color: #2c3e50; 
        color: white !important; 
        font-family: 'Oswald', sans-serif; 
        font-size: 1.2rem; 
        border-radius: 4px; 
        text-transform: uppercase;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #34495e;
    }
    </style>
""", unsafe_allow_html=True)

if 'recette_generee' not in st.session_state:
    st.session_state.recette_generee = False

# --- FONCTIONS PHYSIQUE ---
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

# --- GÉNÉRATION PDF COMPACTE (1 PAGE) ---
class PDF(FPDF):
    def header(self):
        # Logo plus discret
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 20)
        self.set_font('Arial', 'B', 24)
        self.cell(0, 10, 'BEER FACTORY', 0, 1, 'C')
        self.ln(2) # Espace réduit

def create_pdf_compact(data):
    pdf = PDF()
    pdf.add_page()
    # Marge basse réduite pour éviter le saut de page
    pdf.set_auto_page_break(auto=True, margin=10) 
    
    # Sous-titre
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, f"Fiche : {data['style']}", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    
    aromes_txt = ", ".join(data['aromes']).encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 5, f"Profil : {aromes_txt}", ln=True, align='C')
    pdf.ln(5)

    # BANDEAU TECHNIQUE (Compact)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 9)
    info_str = f"VOL: {data['volume']}L  |  ABV: {data['abv']}%  |  OG: {data['og']:.3f}  |  IBU: {int(data['ibu'])}  |  EBC: {int(data['ebc'])}"
    pdf.cell(0, 8, info_str, 1, 1, 'C', fill=True)
    pdf.ln(5)

    # 1. GRAINS
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "1. Grains", ln=True)
    pdf.set_font("Arial", '', 10)
    
    # Hauteur de ligne réduite à 6mm
    h_line = 6
    pdf.set_fill_color(250, 250, 250)
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
    pdf.ln(3)

    # 2. HOUBLONS
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "2. Houblons", ln=True)
    pdf.set_font("Arial", '', 10)
    
    pdf.cell(25, h_line, "Poids", 1, 0, 'C', True)
    pdf.cell(60, h_line, "Variete", 1, 0, 'L', True)
    pdf.cell(60, h_line, "Usage", 1, 0, 'L', True)
    pdf.cell(45, h_line, "Acide Alpha", 1, 1, 'C', True)
    
    for hop in data['houblons']:
        pdf.cell(25, h_line, f"{hop['poids']} g", 1, 0, 'C')
        pdf.cell(60, h_line, f" {hop['nom']}", 1, 0, 'L')
        pdf.cell(60, h_line, f" {hop['usage']}", 1, 0, 'L')
        pdf.cell(45, h_line, f"{hop['aa']} %", 1, 1, 'C')
    pdf.ln(5)

    # 3. PROCESS (Sur une ligne ou deux compactes)
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "3. Processus", ln=True)
    pdf.set_font("Arial", '', 10)
    
    # Utilisation de multicell ou cell cote a cote
    pdf.cell(95, 8, f"Empatage: {data['eau_emp']:.1f} L (67 C - 60min)", 1)
    pdf.cell(95, 8, f"Rincage: {data['eau_rinc']:.1f} L (75 C)", 1, 1)
    pdf.cell(95, 8, f"Ebullition: 60 min", 1)
    pdf.cell(95, 8, f"Fermentation: 20 C (~15 jours)", 1, 1)
    pdf.ln(5)

    # Info Levure
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, f"Levure Recommandee : {data['levure']}", 0, 1, 'L')

    # Footer manuel
    pdf.set_y(-15)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Genere par Beer Factory - L'algorithme des brasseurs", 0, 0, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- CHARGEMENT DUMMY DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("bieres.csv", sep=";", dtype=str)
        df['Degre'] = df['Degre'].str.replace(',', '.').astype(float)
        return df
    except: return pd.DataFrame()
df = load_data()

# ==========================================
# INTERFACE UTILISATEUR
# ==========================================

st.markdown('<h1 class="main-title">Beer Factory</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Scientific Brewing Algorithm</p>', unsafe_allow_html=True)

# RÉGLAGES
with st.container(border=True):
    c1, c2 = st.columns(2)
    with c1:
        style = st.selectbox("Style", ["Blonde", "IPA", "Stout", "Ambrée", "Blanche", "Saison"])
        volume = st.number_input("Volume (L)", 5, 100, 20)
        degre_vise = st.slider("Alcool (%)", 3.0, 12.0, 6.0, 0.1)
    with c2:
        aromes_selectionnes = st.pills("Profil Aromatique", ["🍊 Agrumes", "🥭 Tropical", "🌲 Pin", "🍌 Banane", "☕ Café", "🍪 Biscuit"], selection_mode="multi")
        amertume = st.select_slider("Amertume", options=["Douce", "Standard", "Prononcée", "Amère"])
        ibu_target = {"Douce": 15, "Standard": 25, "Prononcée": 40, "Amère": 60}[amertume]

    if st.button("LANCER LA PRODUCTION", type="primary", use_container_width=True):
        st.session_state.recette_generee = True

# RÉSULTATS & CALCULS
if st.session_state.recette_generee:
    
    # 1. INIT VARIABLES
    base_malt, spe_malt, yeast = "Pilsner", "Blé (Froment)", "US-05"
    hop_amer, hop_aroma = "Magnum", "Saaz"
    ratio_base, ratio_spe = 0.90, 0.10
    
    # LOGIQUE STYLE
    if style == "IPA": base_malt="Pale Ale"; spe_malt="Carapils"; ratio_base=0.94; ratio_spe=0.06; yeast="Verdant IPA"; hop_aroma="Citra"
    elif style == "Stout": base_malt="Maris Otter"; spe_malt="Chocolat"; ratio_base=0.85; ratio_spe
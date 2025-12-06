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
    pdf.cell(0, 10, "
import streamlit as st
import numpy as np
from scipy.integrate import quad
from scipy.interpolate import interp1d
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Barémage Expert & Volumétrique", layout="wide")

# --- MOTEUR DE CALCUL THÉORIQUE ---

def aire_segment_ellipse(h, a, b):
    if h <= 0: return 0
    if h >= 2*b: return np.pi * a * b
    # Segment d'ellipse basé sur un segment de cercle de rayon b, étiré par a/b
    r = b
    area_cercle = r**2 * np.arccos((r - h) / r) - (r - h) * np.sqrt(2 * r * h - h**2)
    return (a / b) * area_cercle

def vol_fond_bombé(h, D_nom, type_fond, oval_ratio=1.0):
    if h <= 0: return 0
    h_corr = min(h, D_nom)
    coeffs = {"Plat": 0, "Elliptique (D/4)": 0.2618, "Hémisphérique (D/2)": 0.5236, "Torisphérique (GRC)": 0.19}
    coeff = coeffs.get(type_fond, 0)
    return coeff * h_corr**2 * (1.5 * D_nom - h_corr) * oval_ratio

def calculer_vol_theorique(h_mes_m, L, D_nom, pente_deg, oval_rate, type_fond):
    alpha = np.radians(pente_deg)
    b = (D_nom * (1 - oval_rate/100)) / 2  # Demi-axe vertical
    a = (D_nom * (1 + oval_rate/100)) / 2  # Demi-axe horizontal
    
    def integrand(x):
        h_loc = h_mes_m - x * np.sin(alpha)
        h_clamped = max(0, min(2*b, h_loc))
        return aire_segment_ellipse(h_clamped, a, b)
    
    v_cyl, _ = quad(integrand, 0, L)
    h_bas = h_mes_m
    h_haut = h_mes_m - L * np.sin(alpha)
    v_fonds = vol_fond_bombé(h_bas, D_nom, type_fond, a/b) + vol_fond_bombé(h_haut, D_nom, type_fond, a/b)
    return v_cyl + v_fonds

# --- INTERFACE ---

st.title("🛢️ Logiciel de Barémage : Méthode Théorique & Volumétrique")

tab1, tab2 = st.tabs(["📐 Calcul Théorique (Expert)", "🧪 Méthode Volumétrique (Terrain)"])

# --- ONGLET 1 : CALCUL THÉORIQUE ---
with tab1:
    col_param, col_graph = st.columns([1, 2])
    
    with col_param:
        st.subheader("Paramètres")
        L = st.number_input("Longueur (m)", value=5.0)
        D = st.number_input("Diamètre (m)", value=2.0)
        pente = st.slider("Inclinaison (°)", -5.0, 5.0, 0.0)
        oval = st.slider("Ovalisation (%)", 0.0, 10.0, 0.0)
        fonds = st.selectbox("Type de fonds", ["Plat", "Elliptique (D/4)", "Hémisphérique (D/2)", "Torisphérique (GRC)"])
        pas_cm = st.number_input("Pas de la table (cm)", value=1.0, step=0.5)
        h_mort_cm = st.number_input("Hauteur Volume Mort (cm)", value=5.0)

    with col_graph:
        if st.button("Générer Table Théorique"):
            # Calculs
            D_reel = D * (1 - oval/100)
            hauteurs_m = np.arange(0, D_reel + (pas_cm/100), pas_cm/100)
            vols_m3 = [calculer_vol_theorique(h, L, D, pente, oval, fonds) for h in hauteurs_m]
            
            # DataFrame en Centimètres
            df = pd.DataFrame({
                "Hauteur (cm)": np.round(hauteurs_m * 100, 2),
                "Volume (m³)": np.round(vols_m3, 4),
                "Volume (Litres)": np.round(np.array(vols_m3) * 1000, 2)
            })
            
            st.success(f"Table générée de 0 à {max(df['Hauteur (cm)'])} cm")
            st.line_chart(df.set_index("Hauteur (cm)")["Volume (Litres)"])
            st.dataframe(df, height=300)
            st.download_button("📥 Télécharger Table Théorique", df.to_csv(index=False), "bareme_theorique.csv")

# --- ONGLET 2 : MÉTHODE VOLUMÉTRIQUE ---
with tab2:
    st.subheader("Importation des relevés compteur")
    st.markdown("""
    *Procédure :* Videz le réservoir, injectez le liquide par paliers, et notez la hauteur à la pige.
    Importez un fichier CSV avec deux colonnes : **Hauteur_cm** et **Volume_L**.
    """)
    
    uploaded_file = st.file_uploader("Choisir un fichier CSV de relevés terrain", type="csv")
    
    if uploaded_file:
        data_terrain = pd.read_csv(uploaded_file)
        st.write("Données terrain reçues :", data_terrain)
        
        if st.button("Calculer Barème Réel par Interpolation"):
            # Interpolation cubique pour lissage
            h_obs = data_terrain.iloc[:, 0].values # Hauteur cm
            v_obs = data_terrain.iloc[:, 1].values # Volume L
            
            f_interp = interp1d(h_obs, v_obs, kind='cubic', fill_value="extrapolate")
            
            # Génération millimétrique convertie en pas choisi
            h_new = np.arange(min(h_obs), max(h_obs) + 0.1, 1.0) # Table par cm
            v_new = f_interp(h_new)
            
            df_reel = pd.DataFrame({
                "Hauteur (cm)": h_new,
                "Volume (Litres)": np.round(v_new, 2)
            })
            
            st.info("La courbe ci-dessous représente votre réservoir réel (déformations incluses).")
            st.line_chart(df_reel.set_index("Hauteur (cm)"))
            st.dataframe(df_reel)
            st.download_button("📥 Télécharger Barème Réel", df_reel.to_csv(index=False), "bareme_reel_terrain.csv")

st.markdown("---")
st.caption("Unité de mesure de sortie : Centimètres (cm) | Volume : Litres & m³")

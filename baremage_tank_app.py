import streamlit as st
import numpy as np
from scipy.integrate import quad
import pandas as pd

# --- CONFIGURATION INTERFACE ---
st.set_page_config(page_title="Barémage Expert v3.0", layout="wide")

# --- MOTEUR DE CALCUL (LOGIQUE MÉTIER) ---

def aire_segment_cercle(h, R):
    """Calcule l'aire d'un segment de cercle."""
    if h <= 0: return 0
    if h >= 2*R: return np.pi * R**2
    return R**2 * np.arccos((R - h) / R) - (R - h) * np.sqrt(2 * R * h - h**2)

def aire_segment_ellipse(h, a, b):
    """Calcule l'aire d'un segment d'ellipse (Ovalisation).
    a: demi-axe horizontal, b: demi-axe vertical (hauteur/2)"""
    if h <= 0: return 0
    if h >= 2*b: return np.pi * a * b
    # Un segment d'ellipse est un segment de cercle de rayon b, étiré par a/b
    return (a / b) * aire_segment_cercle(h, b)

def vol_fond_bombé(h, D_nom, type_fond, oval_factor=1.0):
    """Volume partiel des fonds bombés avec correction d'ovalisation."""
    if h <= 0: return 0
    h_corr = min(h, D_nom)
    
    # Coeffs de base pour fonds bombés (théoriques)
    if type_fond == "Plat": return 0
    elif type_fond == "Elliptique (D/4)": coeff = 0.2618
    elif type_fond == "Hémisphérique (D/2)": coeff = 0.5236
    elif type_fond == "Torisphérique (GRC)": coeff = 0.19
    else: coeff = 0
    
    vol = coeff * h_corr**2 * (1.5 * D_nom - h_corr)
    return vol * oval_factor # Correction simplifiée pour l'ovalisation des fonds

def calculer_baremage(h_mes, L, D_nom, pente_deg, oval_rate, type_fond):
    """Moteur principal avec intégration 3D."""
    alpha = np.radians(pente_deg)
    
    # Calcul des axes de l'ellipse (Ovalisation)
    # Si oval_rate = 5%, le réservoir est écrasé verticalement de 5%
    b = (D_nom * (1 - oval_rate/100)) / 2  # Demi-axe vertical
    a = (D_nom * (1 + oval_rate/100)) / 2  # Demi-axe horizontal (élargissement)
    
    # Intégration sur la longueur L
    def integrand(x):
        h_loc = h_mes - x * np.sin(alpha)
        h_clamped = max(0, min(2*b, h_loc))
        return aire_segment_ellipse(h_clamped, a, b)
    
    v_cyl, _ = quad(integrand, 0, L)
    
    # Fonds bombés
    h_bas = h_mes
    h_haut = h_mes - L * np.sin(alpha)
    v_fonds = vol_fond_bombé(h_bas, D_nom, type_fond, a/b) + \
              vol_fond_bombé(h_haut, D_nom, type_fond, a/b)
              
    return v_cyl + v_fonds

# --- INTERFACE UTILISATEUR ---

st.title("🛢️ Système Expert de Barémage Industriel")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Paramètres de Structure")
    contexte = st.radio("Type d'installation", ["Aérien (Standard)", "Enterré (Déformé)"])
    
    L = st.number_input("Longueur nominale (m)", value=5.0, help="Mesure laser recommandée")
    D_nom = st.number_input("Diamètre nominal (m)", value=2.0)
    
    st.header("📐 Déformations & Pose")
    pente = st.slider("Inclinaison / Pente (°)", -5.0, 5.0, 0.0)
    
    oval = 0.0
    if contexte == "Enterré (Déformé)":
        oval = st.slider("Taux d'ovalisation (%)", 0.0, 10.0, 2.0, 
                         help="Écrasement vertical dû au poids de la terre")
    
    st.header("🏺 Géométrie des Fonds")
    type_fond = st.selectbox("Forme des extrémités", 
                             ["Plat", "Elliptique (D/4)", "Hémisphérique (D/2)", "Torisphérique (GRC)"])

    st.header("🚰 Exploitation")
    h_mort = st.number_input("Hauteur Volume Mort (mm)", value=50) / 1000

# --- AFFICHAGE DES RÉSULTATS ---

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("📟 Lecture Instantanée")
    h_inst = st.number_input("Hauteur lue à la pige (m)", value=1.0, step=0.01)
    
    v_tot = calculer_baremage(h_inst, L, D_nom, pente, oval, type_fond)
    v_mort = calculer_baremage(h_mort, L, D_nom, pente, oval, type_fond)
    
    st.metric("Volume Total", f"{v_tot:.3f} m³", f"{v_tot*1000:.1f} Litres")
    
    if h_inst <= h_mort:
        st.error(f"Attention : Niveau sous le seuil d'aspiration ({h_mort*1000:.0f} mm)")
    else:
        v_util = max(0, v_tot - v_mort)
        st.info(f"Volume pompable estimé : {v_util*1000:.1f} Litres")

with col2:
    st.subheader("📈 Table de Barémage")
    pas = st.select_slider("Précision de la table", options=[0.01, 0.02, 0.05, 0.1], value=0.01)
    
    if st.button("Générer la table complète"):
        # Le diamètre vertical réel est D_nom * (1 - oval/100)
        D_vert = D_nom * (1 - oval/100)
        niveaux = np.arange(0, D_vert + pas, pas)
        vols = [calculer_baremage(n, L, D_nom, pente, oval, type_fond) for n in niveaux]
        
        df = pd.DataFrame({
            "Niveau (m)": niveaux,
            "Volume (m3)": vols,
            "Lutres": np.array(vols) * 1000
        })
        
        st.line_chart(df.set_index("Niveau (m)")["Volume (m3)"])
        st.dataframe(df.style.format("{:.3f}"), height=300)
        
        st.download_button("📥 Exporter la Table (CSV)", df.to_csv(index=False), "table_expert.csv")

st.markdown("---")
st.caption("Barémage Expert v3.0 | Moteur de calcul basé sur l'intégration de sections elliptiques variables.")

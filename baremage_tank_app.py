import streamlit as st
import numpy as np
from scipy.integrate import quad
import pandas as pd

st.set_page_config(page_title='Barémage Industriel', layout='wide')

def aire_segment_circulaire(h, R):
    if h <= 0: return 0
    if h >= 2*R: return np.pi * R**2
    return R**2 * np.arccos((R - h) / R) - (R - h) * np.sqrt(2 * R * h - h**2)

def volume_fond_unitaire(h, D, type_fond):
    if h <= 0: return 0
    R = D / 2
    h = min(h, D)
    if type_fond == 'Plat': return 0
    elif type_fond == 'Hémisphérique (D/2)': return (np.pi * h**2 * (3*R - h)) / 3
    elif type_fond == 'Elliptique (D/4)': return (np.pi * h**2 * (1.5*D - h)) / 12
    elif type_fond == 'Torisphérique (GRC)': return 0.19 * h**2 * (1.5*D - h)
    return 0

def calculer_volume_total(h_mesuree, L, D, pente_deg, type_fond):
    R = D / 2
    alpha = np.radians(pente_deg)
    def integrand(x):
        h_locale = h_mesuree - x * np.sin(alpha)
        h_clamped = max(0, min(D, h_locale))
        return aire_segment_circulaire(h_clamped, R)
    v_cylindre, _ = quad(integrand, 0, L)
    h_bas = h_mesuree
    h_haut = h_mesuree - L * np.sin(alpha)
    v_fonds = volume_fond_unitaire(h_bas, D, type_fond) + volume_fond_unitaire(h_haut, D, type_fond)
    return v_cylindre + v_fonds

st.title('🛢️ Application de Barémage de Réservoir')
with st.sidebar:
    st.header('📋 Configuration')
    L = st.number_input('Longueur (m)', value=5.0)
    D = st.number_input('Diamètre (m)', value=2.0)
    type_fond = st.selectbox('Type de fonds', ['Plat', 'Elliptique (D/4)', 'Hémisphérique (D/2)', 'Torisphérique (GRC)'])
    pente = st.slider('Inclinaison (°)', -5.0, 5.0, 0.0)
    pas_cm = st.number_input('Pas (cm)', value=1)

col1, col2 = st.columns([1, 2])
with col1:
    h_instant = st.number_input('Hauteur (m)', value=D/2, max_value=D)
    vol = calculer_volume_total(h_instant, L, D, pente, type_fond)
    st.metric('Volume Total', f'{vol:.3f} m³', f'{vol*1000:.1f} L')

with col2:
    if st.button('🚀 Générer la Table'):
        hauteurs = np.arange(0, D + (pas_cm/100), pas_cm/100)
        volumes = [calculer_volume_total(h, L, D, pente, type_fond) for h in hauteurs]
        df = pd.DataFrame({'Hauteur (m)': hauteurs, 'Volume (m3)': volumes})
        st.line_chart(df.set_index('Hauteur (m)'))
        st.download_button('📥 Télécharger CSV', df.to_csv(index=False), 'bareme.csv')
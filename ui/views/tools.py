# ui/views/tools.py
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import io
from utils.export_utils import create_excel_export, create_pdf_export

def render_tools():
    st.markdown("### 🛠️ Boîte à Outils Supply Chain")
    st.markdown("Passez de la théorie à l'application métier. Calculez, simulez et exportez vos résultats.")

    tabs = st.tabs([
        "🛡️ Stock de Sécurité", 
        "💰 Coût Complet (Landed Cost)", 
        "📉 Optimiseur Wilson (EOQ)",
        "🌍 Empreinte Carbone",
        "💸 Cash-to-Cash",
        "🏢 Centralisation",
        "📦 Poids Volumétrique",
        "🚢 Sélecteur Incoterms"
    ])

    with tabs[0]: render_safety_stock_calculator()
    with tabs[1]: render_landed_cost_calculator()
    with tabs[2]: render_wilson_calculator()
    with tabs[3]: render_carbon_calculator()
    with tabs[4]: render_cash_to_cash_calculator()
    with tabs[5]: render_centralization_calculator()
    with tabs[6]: render_volumetric_calculator()
    with tabs[7]: render_incoterm_selector()

def render_export_buttons(title, data, summary):
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    excel_data = create_excel_export(title, data, summary)
    c1.download_button(
        label=f"📥 Télécharger Excel (.xlsx)",
        data=excel_data,
        file_name=f"MentorSC_{title.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
    pdf_data = create_pdf_export(title, data, summary)
    c2.download_button(
        label=f"📄 Télécharger Rapport PDF (.pdf)",
        data=pdf_data,
        file_name=f"MentorSC_{title.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# --- 1. STOCK DE SÉCURITÉ ---
def render_safety_stock_calculator():
    st.subheader("🛡️ Calculateur de Stock de Sécurité")
    col1, col2 = st.columns(2)
    with col1:
        avg_d = st.number_input("Conso moyenne / jour", value=100.0, key="ss_avg")
        std_d = st.number_input("Écart-type conso", value=20.0, key="ss_std")
    with col2:
        lt = st.number_input("Délai moyen (jours)", value=10.0, key="ss_lt")
        std_lt = st.number_input("Écart-type délai (jours)", value=2.0, key="ss_std_lt")
    
    sl = st.slider("Taux de Service cible (%)", 80.0, 99.9, 95.0, 0.1)
    z = norm.ppf(sl / 100)
    ss = z * np.sqrt(lt * (std_d ** 2) + (avg_d ** 2) * (std_lt ** 2))
    
    st.metric("Stock de Sécurité", f"{int(np.ceil(ss))} unités")
    
    data = {"Conso Moyenne": avg_d, "Ecart-type Conso": std_d, "Délai Moyen": lt, "Ecart-type Délai": std_lt, "Taux de Service": sl, "Coeff Z": f"{z:.2f}"}
    summary = {"Stock de Sécurité": f"{int(np.ceil(ss))} unités", "Point de Commande": f"{int(np.ceil(avg_d*lt + ss))} unités"}
    render_export_buttons("Stock de Sécurité", data, summary)

# --- 2. LANDED COST ---
def render_landed_cost_calculator():
    st.subheader("💰 Comparateur de Coût Complet")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Source A (Lointain)**")
        p_a = st.number_input("Prix Achat A", value=10.0)
        f_a = st.number_input("Fret A", value=2.0)
        d_a = st.number_input("Douane A (%)", value=6.0)
        lt_a = st.number_input("Délai A (jours)", value=40)
    with c2:
        st.markdown("**Source B (Proche)**")
        p_b = st.number_input("Prix Achat B", value=13.0)
        f_b = st.number_input("Fret B", value=0.5)
        d_b = st.number_input("Douane B (%)", value=0.0)
        lt_b = st.number_input("Délai B (jours)", value=5)
    
    rate = st.slider("Taux de possession annuel (%)", 5, 30, 15) / 100
    
    def calc(p, f, d, lt):
        duty = (p+f) * (d/100)
        fin = (p+f+duty) * rate * (lt/365)
        return p + f + duty + fin, duty, fin

    t_a, dt_a, fn_a = calc(p_a, f_a, d_a, lt_a)
    t_b, dt_b, fn_b = calc(p_b, f_b, d_b, lt_b)
    
    st.write(f"**Landed A:** {t_a:.2f}€ | **Landed B:** {t_b:.2f}€")
    data = {"Prix A": p_a, "Fret A": f_a, "Douane A": f"{d_a}%", "Délai A": lt_a, "Prix B": p_b, "Fret B": f_b, "Douane B": f"{d_b}%", "Délai B": lt_b, "Taux Possession": f"{rate*100}%"}
    summary = {"Coût Total A": f"{t_a:.2f}€", "Coût Total B": f"{t_b:.2f}€", "Ecart Unitaire": f"{abs(t_a-t_b):.2f}€"}
    render_export_buttons("Coût Complet", data, summary)

# --- 3. WILSON (EOQ) ---
def render_wilson_calculator():
    st.subheader("📉 Optimiseur de Commande (Wilson)")
    d = st.number_input("Demande Annuelle (unités)", value=12000)
    s = st.number_input("Coût fixe d'une commande (S)", value=50.0)
    h = st.number_input("Coût de possession annuel par unité (H)", value=2.0)
    
    eoq = np.sqrt((2 * d * s) / h)
    n = d / eoq
    
    st.metric("Quantité Économique (EOQ)", f"{int(np.ceil(eoq))} unités")
    st.write(f"Fréquence idéale : {n:.1f} commandes / an (soit tous les {365/n:.0f} jours)")
    
    data = {"Demande Annuelle": d, "Coût Commande (S)": s, "Coût Stockage (H)": h}
    summary = {"EOQ": f"{int(np.ceil(eoq))} unités", "Commandes/An": f"{n:.1f}"}
    render_export_buttons("Optimiseur Wilson", data, summary)

# --- 4. CARBONE ---
def render_carbon_calculator():
    st.subheader("🌍 Calculateur d'Empreinte Carbone")
    weight = st.number_input("Poids total (tonnes)", value=1.0)
    dist = st.number_input("Distance (km)", value=1000)
    
    factors = {"Avion": 0.500, "Camion": 0.080, "Train": 0.020, "Maritime": 0.010}
    res = {m: weight * dist * f for m, f in factors.items()}
    
    st.write(pd.DataFrame(list(res.items()), columns=["Mode", "CO2 (kg)"]))
    render_export_buttons("Empreinte Carbone", {"Poids (T)": weight, "Distance (km)": dist}, {m: f"{v:.1f} kg CO2" for m, v in res.items()})

# --- 5. CASH TO CASH ---
def render_cash_to_cash_calculator():
    st.subheader("💸 Simulateur Cash-to-Cash")
    dso = st.number_input("Délai paiement Client (DSO - jours)", value=45)
    dio = st.number_input("Délai de Stockage (DIO - jours)", value=60)
    dpo = st.number_input("Délai paiement Fournisseur (DPO - jours)", value=30)
    
    c2c = dso + dio - dpo
    st.metric("Cycle Cash-to-Cash", f"{c2c} jours")
    
    data = {"DSO (Clients)": dso, "DIO (Stocks)": dio, "DPO (Fournisseurs)": dpo}
    summary = {"Cycle C2C": f"{c2c} jours"}
    render_export_buttons("Cash-to-Cash", data, summary)

# --- 6. CENTRALISATION ---
def render_centralization_calculator():
    st.subheader("🏢 Simulateur de Centralisation (Square Root Law)")
    stock = st.number_input("Stock de sécurité actuel global", value=10000)
    n_old = st.number_input("Nombre d'entrepôts actuels", value=5)
    n_new = st.number_input("Nombre d'entrepôts futurs", value=1)
    
    new_stock = stock * np.sqrt(n_new / n_old)
    saving = stock - new_stock
    
    st.metric("Nouveau Stock estimé", f"{int(new_stock)}", f"-{int(saving)} unités")
    st.write(f"Économie de stock de sécurité estimée : **{int((saving/stock)*100)}%**")
    
    data = {"Stock Initial": stock, "Nb Entrepôts Avant": n_old, "Nb Entrepôts Après": n_new}
    summary = {"Stock Futur": int(new_stock), "Economie": f"{int(saving)} unités"}
    render_export_buttons("Centralisation", data, summary)

# --- 7. VOLUMÉTRIQUE ---
def render_volumetric_calculator():
    st.subheader("📦 Poids Volumétrique")
    l = st.number_input("L (cm)", value=60); w = st.number_input("W (cm)", value=40); h = st.number_input("H (cm)", value=40)
    real = st.number_input("Poids réel (kg)", value=10.0)
    ratio = st.selectbox("Ratio", [6000, 5000, 3000], format_func=lambda x: f"1:{x//1000} ({x})")
    
    vol = (l*w*h)/ratio
    taxable = max(real, vol)
    st.metric("Poids Taxable", f"{taxable:.2f} kg", f"Vol: {vol:.2f} kg")
    render_export_buttons("Poids Volumetrique", {"L":l, "W":w, "H":h, "Réel":real, "Ratio":ratio}, {"Poids Taxable": f"{taxable:.2f} kg"})

# --- 8. INCOTERMS ---
def render_incoterm_selector():
    st.subheader("🚢 Sélecteur Incoterms")
    q1 = st.toggle("Maîtrise du transport international")
    q2 = st.toggle("Douane import gérée par le vendeur")
    res = "DDP" if q2 else ("FOB/FCA" if q1 else "EXW")
    st.success(f"Incoterm recommandé : **{res}**")
    render_export_buttons("Incoterms", {"Maitrise Transport": q1, "Douane Import Vendeur": q2}, {"Recommandation": res})

def render_templates_section():
    st.write("Section ABC-XYZ déplacée vers les fiches outils.")

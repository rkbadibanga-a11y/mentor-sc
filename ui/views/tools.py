# ui/views/tools.py
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def render_tools():
    st.markdown("### 🛠️ Boîte à Outils Supply Chain")
    st.markdown("Passez de la théorie à l'application. Calculez vos paramètres et exportez vos outils vers Excel.")

    tab1, tab2 = st.tabs(["📊 Calculateur Stock de Sécurité", "📋 Templates & Formules"])

    with tab1:
        render_safety_stock_calculator()

    with tab2:
        render_templates_section()

def render_safety_stock_calculator():
    st.subheader("🛡️ Calculateur de Stock de Sécurité")
    st.info("Ce calculateur prend en compte l'incertitude de la demande ET la variabilité du délai fournisseur.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📁 Données de Demande**")
        avg_demand = st.number_input("Consommation moyenne (par jour)", value=100.0, step=1.0)
        std_demand = st.number_input("Écart-type de la conso (variabilité)", value=20.0, step=1.0)
        
        st.markdown("**🚚 Données Fournisseur**")
        lead_time = st.number_input("Délai de livraison moyen (jours)", value=10.0, step=1.0)
        std_lead_time = st.number_input("Écart-type du délai (jours)", value=2.0, step=0.5)

    with col2:
        st.markdown("**🎯 Cible de Service**")
        service_level = st.slider("Taux de Service cible (%)", min_value=80.0, max_value=99.9, value=95.0, step=0.1)
        
        # Calcul du coefficient Z
        z_score = norm.ppf(service_level / 100)
        st.metric("Coefficient de sécurité (Z)", f"{z_score:.2f}")

    # Calcul de la formule complexe
    # SS = Z * sqrt( (LeadTime * StdDemand^2) + (AvgDemand^2 * StdLeadTime^2) )
    term_demand = lead_time * (std_demand ** 2)
    term_lead_time = (avg_demand ** 2) * (std_lead_time ** 2)
    combined_std = np.sqrt(term_demand + term_lead_time)
    safety_stock = z_score * combined_std

    st.markdown("---")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Stock de Sécurité", f"{int(np.ceil(safety_stock))} unités")
    c2.metric("Point de Commande", f"{int(np.ceil(avg_demand * lead_time + safety_stock))} unités")
    c3.metric("Stock Moyen", f"{int(np.ceil(safety_stock))} unités (hors stock cycle)")

    with st.expander("🔍 Voir la formule appliquée"):
        st.latex(r"SS = Z \times \sqrt{L \times \sigma_c^2 + C^2 \times \sigma_L^2}")
        st.markdown(f"""
        - **Z** (Coeff. Sécurité) : {z_score:.2f}
        - **L** (Délai) : {lead_time} jours
        - **σc** (Écart-type conso) : {std_demand}
        - **C** (Conso moyenne) : {avg_demand}
        - **σL** (Écart-type délai) : {std_lead_time}
        """)

    # Export Excel
    st.markdown("#### 📥 Exporter vers Excel")
    if st.button("Générer mon outil Excel personnalisé", use_container_width=True):
        output = create_excel_template(avg_demand, std_demand, lead_time, std_lead_time, service_level, safety_stock, z_score)
        st.download_button(
            label="💾 Télécharger le fichier .xlsx",
            data=output,
            file_name="Calculateur_Stock_Securite_MentorSC.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def create_excel_template(avg_c, std_c, lt, std_lt, sl, ss, z):
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Calculateur SS"

    # Styles
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    input_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    result_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    # Titre
    ws['B2'] = "OUTIL DE CALCUL STOCK DE SÉCURITÉ - MENTOR SC"
    ws['B2'].font = Font(size=14, bold=True)
    
    # Entrées
    ws['B4'] = "PARAMÈTRES D'ENTRÉE"
    ws['B4'].font = Font(bold=True)
    
    data = [
        ("Consommation moyenne (jour)", avg_c, "Unités"),
        ("Écart-type consommation", std_c, "Unités"),
        ("Délai de livraison moyen", lt, "Jours"),
        ("Écart-type délai", std_lt, "Jours"),
        ("Taux de Service cible", sl/100, "Pourcentage"),
    ]
    
    for i, (label, val, unit) in enumerate(data):
        row = 5 + i
        ws.cell(row=row, column=2, value=label).border = border
        cell_val = ws.cell(row=row, column=3, value=val)
        cell_val.border = border
        cell_val.fill = input_fill
        if label == "Taux de Service cible":
            cell_val.number_format = '0.0%'
        ws.cell(row=row, column=4, value=unit).border = border

    # Résultats
    ws['B12'] = "RÉSULTATS CALCULÉS"
    ws['B12'].font = Font(bold=True)
    
    ws['B13'] = "Coefficient Z"
    ws['C13'] = z
    ws['B14'] = "Stock de Sécurité"
    ws['C14'] = "=C13*SQRT(C7*C6^2 + C5^2*C8^2)"
    ws['D14'] = "Unités"
    
    for r in range(13, 15):
        ws.cell(row=r, column=2).border = border
        c = ws.cell(row=r, column=3)
        c.border = border
        c.fill = result_fill
        ws.cell(row=r, column=4).border = border

    ws['B16'] = "💡 Note : Ce fichier utilise la formule de King qui combine les deux incertitudes."
    ws['B16'].font = Font(italic=True, size=9)

    # Ajustement colonnes
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 15

    wb.save(output)
    return output.getvalue()

def render_templates_section():
    st.subheader("📋 Liste des Formules Magiques")
    st.write("Copiez ces formules directement dans votre ERP ou Excel.")

    formulas = [
        {
            "name": "Quantité Économique (Wilson)",
            "formula": "SQRT((2 * Demande Annuelle * Coût Commande) / Coût Stockage)",
            "use": "Optimiser la taille des lots d'achat."
        },
        {
            "name": "Taux de Rotation des Stocks",
            "formula": "Consommation Annuelle / Stock Moyen",
            "use": "Mesurer la performance financière du stock."
        },
        {
            "name": "Taux de Service (Type 1)",
            "formula": "(Commandes livrées à temps) / (Total commandes reçues)",
            "use": "Mesurer la fiabilité logistique."
        }
    ]

    for f in formulas:
        with st.expander(f"🔹 {f['name']}"):
            st.code(f["formula"], language="excel")
            st.write(f"**Usage :** {f['use']}")
            if st.button(f"Générer Template Excel - {f['name']}"):
                st.info("Template en cours de préparation...")

    st.markdown("---")
    st.markdown("##### 📥 Téléchargements utiles")
    st.button("📦 Template Inventaire Tournant (.xlsx)")
    st.button("📊 Dashboard KPI Supply Chain (.xlsx)")

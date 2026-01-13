# utils/export_utils.py
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors

def create_excel_export(title, data_dict, summary_metrics=None):
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Rapport Mentor SC"

    # Styles
    title_font = Font(name='Arial', size=16, bold=True, color="1E293B")
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    # Header Branding
    ws['A1'] = "MENTOR SC - L'EXPERT SUPPLY CHAIN"
    ws['A1'].font = Font(bold=True, size=12)
    ws['A2'] = "Contact: r.k.badibanga@gmail.com"
    ws['A3'] = "Développé avec ❤️ par Mentor SC"
    
    ws['B5'] = title.upper()
    ws['B5'].font = title_font

    # Summary Metrics
    if summary_metrics:
        row = 7
        for label, val in summary_metrics.items():
            ws.cell(row=row, column=2, value=label).font = Font(bold=True)
            ws.cell(row=row, column=3, value=val).font = Font(bold=True, color="00DFD8")
            row += 1
        start_data = row + 2
    else:
        start_data = 7

    # Data Table
    ws.cell(row=start_data, column=2, value="Paramètre").fill = header_fill
    ws.cell(row=start_data, column=2).font = header_font
    ws.cell(row=start_data, column=3, value="Valeur").fill = header_fill
    ws.cell(row=start_data, column=3).font = header_font

    current_row = start_data + 1
    for key, value in data_dict.items():
        ws.cell(row=current_row, column=2, value=key).border = border
        ws.cell(row=current_row, column=3, value=value).border = border
        current_row += 1

    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 20

    wb.save(output)
    return output.getvalue()

def create_pdf_export(title, data_dict, summary_metrics=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- Header Branding ---
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 2*cm, "MENTOR SC")
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, height - 2.5*cm, "L'Expert Supply Chain")
    c.drawString(2*cm, height - 2.9*cm, "Contact: r.k.badibanga@gmail.com")
    
    # Blue Line
    c.setStrokeColor(colors.hexColor("#00DFD8"))
    c.setLineWidth(2)
    c.line(2*cm, height - 3.5*cm, width - 2*cm, height - 3.5*cm)

    # --- Title ---
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.hexColor("#1E293B"))
    c.drawCentredString(width/2, height - 5*cm, title)

    # --- Summary ---
    y = height - 7*cm
    if summary_metrics:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, "RÉSULTATS CLÉS :")
        y -= 0.8*cm
        for label, val in summary_metrics.items():
            c.setFont("Helvetica", 11)
            c.drawString(2.5*cm, y, f"• {label} :")
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(colors.hexColor("#007BFF"))
            c.drawString(8*cm, y, str(val))
            c.setFillColor(colors.black)
            y -= 0.6*cm
        y -= 1*cm

    # --- Table Header ---
    c.setFillColor(colors.hexColor("#1E293B"))
    c.rect(2*cm, y, width - 4*cm, 0.8*cm, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.5*cm, y + 0.25*cm, "PARAMÈTRE")
    c.drawString(10*cm, y + 0.25*cm, "VALEUR")
    
    # --- Table Body ---
    y -= 0.8*cm
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    
    for key, value in data_dict.items():
        if y < 3*cm: # New page if needed
            c.showPage()
            y = height - 3*cm
        
        # Zebra striping
        # c.setFillColor(colors.whitesmoke)
        # c.rect(2*cm, y, width - 4*cm, 0.7*cm, fill=1)
        
        c.setFillColor(colors.black)
        c.drawString(2.5*cm, y + 0.2*cm, str(key))
        c.drawString(10*cm, y + 0.2*cm, str(value))
        
        # Border
        c.setLineWidth(0.5)
        c.setStrokeColor(colors.lightgrey)
        c.line(2*cm, y, width - 2*cm, y)
        y -= 0.7*cm

    # --- Footer ---
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    c.drawCentredString(width/2, 1.5*cm, "Développé avec ❤️ par Mentor SC - r.k.badibanga@gmail.com")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

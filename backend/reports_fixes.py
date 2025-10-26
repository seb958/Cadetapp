# Corrections pour le système de rapports

from io import BytesIO
from typing import List, Optional
from datetime import datetime, date
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as ReportLabImage, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.axes import XCategoryAxis, YValueAxis
from pathlib import Path

LOGO_PATH = Path(__file__).parent / "logo.png"

def add_header_footer(canvas, doc, title: str):
    """Ajoute en-tête et pied de page à chaque page"""
    canvas.saveState()
    
    # En-tête
    if LOGO_PATH.exists():
        canvas.drawImage(str(LOGO_PATH), 0.75*inch, doc.height + 1.5*inch, width=0.75*inch, height=0.75*inch, preserveAspectRatio=True)
    
    canvas.setFont('Helvetica-Bold', 14)
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.height + 1.75*inch, title)
    
    canvas.setFont('Helvetica', 9)
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.height + 1.5*inch, f"Généré le {date_str}")
    
    # Pied de page
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, 0.5*inch, f"Page {doc.page}")
    
    canvas.restoreState()

async def generate_cadets_list_pdf_fixed(cadets: List[dict], sections: List[dict], filter_info: str) -> BytesIO:
    """Génère un PDF avec la liste des cadets - VERSION CORRIGÉE"""
    buffer = BytesIO()
    
    # FIX #2: Augmenter les marges pour éviter que les noms soient coupés
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            topMargin=2.5*inch, bottomMargin=0.75*inch,
                            leftMargin=1*inch, rightMargin=1*inch)  # Marges augmentées
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("Liste des Cadets", title_style))
    elements.append(Paragraph(f"<i>{filter_info}</i>", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # FIX #1: Vérifier qu'il y a des cadets
    if not cadets or len(cadets) == 0:
        no_data_style = ParagraphStyle(
            'NoData',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph("Aucun cadet trouvé avec ces critères", no_data_style))
        
        # Build PDF
        doc.build(elements, onFirstPage=lambda c, d: add_header_footer(c, d, "LISTE DES CADETS"),
                  onLaterPages=lambda c, d: add_header_footer(c, d, "LISTE DES CADETS"))
        buffer.seek(0)
        return buffer
    
    # Créer un dictionnaire des sections pour lookup rapide
    section_map = {s['id']: s['nom'] for s in sections}
    section_map['etat-major-virtual'] = '⭐ État-Major'
    
    # Grouper par section
    cadets_by_section = {}
    for cadet in cadets:
        section_id = cadet.get('section_id', 'no_section')
        if section_id not in cadets_by_section:
            cadets_by_section[section_id] = []
        cadets_by_section[section_id].append(cadet)
    
    # Générer le tableau pour chaque section
    for section_id, section_cadets in sorted(cadets_by_section.items()):
        section_name = section_map.get(section_id, 'Sans section')
        
        # Titre de section
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=12
        )
        elements.append(Paragraph(section_name, section_style))
        
        # Tableau des cadets - Largeurs ajustées pour A4 avec marges de 1 inch
        data = [['Nom', 'Prénom', 'Grade', 'Rôle']]
        
        for cadet in sorted(section_cadets, key=lambda x: (x.get('nom', ''), x.get('prenom', ''))):
            data.append([
                cadet.get('nom', '-'),
                cadet.get('prenom', '-'),
                cadet.get('grade', '-').replace('_', ' ').title(),
                cadet.get('role', '-')
            ])
        
        # Largeurs adaptées pour A4 (210mm = 8.27 inch - 2 inch marges = 6.27 inch disponible)
        table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.6*inch, 1.6*inch])
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Corps
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 1), (-1, -1), 6),
            ('RIGHTPADDING', (0, 1), (-1, -1), 6),
            
            # Grille
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Lignes alternées
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Résumé
    summary_text = f"<b>Total: {len(cadets)} cadet(s)</b>"
    elements.append(Paragraph(summary_text, styles['Normal']))
    
    # Build PDF avec en-tête/pied de page
    doc.build(elements, onFirstPage=lambda c, d: add_header_footer(c, d, "LISTE DES CADETS"),
              onLaterPages=lambda c, d: add_header_footer(c, d, "LISTE DES CADETS"))
    
    buffer.seek(0)
    return buffer


async def generate_inspection_sheet_pdf_fixed(cadets: List[dict], uniform_type: str, 
                                       criteria: List[str], sections: List[dict]) -> BytesIO:
    """Génère une feuille d'inspection vierge - VERSION CORRIGÉE EN PAYSAGE"""
    buffer = BytesIO()
    
    # FIX #3: Format PAYSAGE pour plus d'espace horizontal
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            topMargin=2.5*inch, bottomMargin=0.75*inch,
                            leftMargin=0.75*inch, rightMargin=0.75*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Créer un dictionnaire des sections
    section_map = {s['id']: s['nom'] for s in sections}
    section_map['etat-major-virtual'] = '⭐ État-Major'
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph(f"Feuille d'Inspection - {uniform_type}", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Informations
    info_style = styles['Normal']
    elements.append(Paragraph(f"<b>Date:</b> _________________________  <b>Inspecteur:</b> _________________________", info_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Légende du barème
    legend_style = ParagraphStyle(
        'Legend',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=10
    )
    elements.append(Paragraph("<b>Barème:</b> 0 = Très mauvais | 1 = Mauvais | 2 = Passable | 3 = Bon | 4 = Excellent", legend_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Grouper par section
    cadets_by_section = {}
    for cadet in cadets:
        section_id = cadet.get('section_id', 'no_section')
        if section_id not in cadets_by_section:
            cadets_by_section[section_id] = []
        cadets_by_section[section_id].append(cadet)
    
    # FIX #3: Critères en abréviations pour éviter le chevauchement
    # Créer des abréviations pour les critères longs
    criteria_abbrev = []
    criteria_legend = []
    for i, crit in enumerate(criteria, 1):
        if len(crit) > 15:
            abbrev = f"C{i}"
            criteria_abbrev.append(abbrev)
            criteria_legend.append(f"{abbrev}: {crit}")
        else:
            criteria_abbrev.append(crit[:12])  # Tronquer à 12 caractères
            if len(crit) > 12:
                criteria_legend.append(f"{crit[:12]}: {crit}")
    
    # Afficher la légende des critères si nécessaire
    if criteria_legend:
        legend_text = "<b>Critères:</b> " + " | ".join(criteria_legend)
        elements.append(Paragraph(legend_text, legend_style))
        elements.append(Spacer(1, 0.1*inch))
    
    # Tableau pour chaque section
    for section_id, section_cadets in sorted(cadets_by_section.items()):
        section_name = section_map.get(section_id, 'Sans section')
        
        # Titre de section
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=6
        )
        elements.append(Paragraph(section_name, section_style))
        
        # En-tête du tableau avec abréviations
        header = ['Cadet'] + criteria_abbrev + ['Score', 'Commentaire']
        
        # Calculer les largeurs en fonction du nombre de critères
        # Paysage A4 = 11.69 inch - 1.5 inch marges = 10.19 inch disponible
        available_width = 9.5*inch
        cadet_col_width = 1.8*inch
        score_col_width = 0.5*inch
        comment_col_width = 1.5*inch
        
        remaining_width = available_width - cadet_col_width - score_col_width - comment_col_width
        criteria_col_width = remaining_width / len(criteria) if criteria else 0.5*inch
        criteria_col_width = max(criteria_col_width, 0.4*inch)  # Minimum 0.4 inch
        
        col_widths = [cadet_col_width] + [criteria_col_width] * len(criteria) + [score_col_width, comment_col_width]
        
        data = [header]
        
        # Lignes pour chaque cadet
        for cadet in sorted(section_cadets, key=lambda x: (x.get('nom', ''), x.get('prenom', ''))):
            cadet_name = f"{cadet.get('nom', '')} {cadet.get('prenom', '')}"
            row = [cadet_name] + [''] * len(criteria) + ['', '']
            data.append(row)
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            
            # Corps
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Grille
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Lignes alternées
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Page break entre sections si beaucoup de cadets
        if len(section_cadets) > 20:
            elements.append(PageBreak())
    
    # Build PDF
    doc.build(elements, onFirstPage=lambda c, d: add_header_footer(c, d, f"FEUILLE D'INSPECTION - {uniform_type.upper()}"),
              onLaterPages=lambda c, d: add_header_footer(c, d, f"FEUILLE D'INSPECTION - {uniform_type.upper()}"))
    
    buffer.seek(0)
    return buffer


async def generate_inspection_stats_pdf_with_chart(inspections: List[dict], stats: dict, 
                                       period_info: str, sections: List[dict]) -> BytesIO:
    """Génère un rapport détaillé avec GRAPHIQUE d'évolution"""
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=2.5*inch, bottomMargin=0.75*inch,
                            leftMargin=0.75*inch, rightMargin=0.75*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("Rapport d'Inspections d'Uniformes", title_style))
    elements.append(Paragraph(f"<i>{period_info}</i>", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Statistiques globales
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#3b82f6'),
        spaceAfter=12
    )
    
    elements.append(Paragraph("📊 Statistiques Globales", summary_style))
    
    summary_data = [
        ['Métrique', 'Valeur'],
        ['Total d\'inspections', str(stats.get('total_inspections', 0))],
        ['Moyenne escadron', f"{stats.get('squadron_average', 0):.1f}%"],
        ['Meilleur score', f"{stats.get('best_score', 0):.1f}%"],
        ['Score le plus bas', f"{stats.get('worst_score', 0):.1f}%"],
        ['Nombre de cadets inspectés', str(stats.get('cadets_inspected', 0))]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # FIX #4: GRAPHIQUE D'ÉVOLUTION
    if inspections and len(inspections) > 0:
        elements.append(Paragraph("📈 Évolution des Scores dans le Temps", summary_style))
        
        # Préparer les données pour le graphique
        # Grouper par date et calculer la moyenne
        inspections_by_date = {}
        for insp in inspections:
            date_str = insp['date']
            if date_str not in inspections_by_date:
                inspections_by_date[date_str] = []
            inspections_by_date[date_str].append(insp['total_score'])
        
        # Calculer les moyennes par date
        dates = sorted(inspections_by_date.keys())
        averages = [sum(inspections_by_date[d]) / len(inspections_by_date[d]) for d in dates]
        
        # Limiter à 15 points max pour lisibilité
        if len(dates) > 15:
            step = len(dates) // 15
            dates = dates[::step]
            averages = averages[::step]
        
        # Créer le graphique
        drawing = Drawing(400, 200)
        chart = HorizontalLineChart()
        chart.x = 50
        chart.y = 50
        chart.height = 125
        chart.width = 300
        chart.data = [averages]
        chart.lines[0].strokeColor = colors.HexColor('#3b82f6')
        chart.lines[0].strokeWidth = 2
        
        # Configurer les axes
        chart.categoryAxis.categoryNames = [d[5:] for d in dates]  # Format MM-DD
        chart.categoryAxis.labels.boxAnchor = 'n'
        chart.categoryAxis.labels.angle = 45
        chart.categoryAxis.labels.fontSize = 7
        
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = 100
        chart.valueAxis.valueStep = 20
        chart.valueAxis.labels.fontSize = 8
        
        drawing.add(chart)
        elements.append(drawing)
        elements.append(Spacer(1, 0.3*inch))
    
    # Statistiques par section
    if stats.get('by_section'):
        elements.append(Paragraph("📍 Statistiques par Section", summary_style))
        
        section_data = [['Section', 'Inspections', 'Moyenne', 'Cadets']]
        
        for section_stat in stats['by_section']:
            section_data.append([
                section_stat['section_name'],
                str(section_stat['total_inspections']),
                f"{section_stat['average_score']:.1f}%",
                str(section_stat['cadets_count'])
            ])
        
        section_table = Table(section_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        section_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
        ]))
        
        elements.append(section_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Cadets nécessitant un suivi
    if stats.get('cadets_needing_attention'):
        attention_style = ParagraphStyle(
            'Attention',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#ef4444'),
            spaceAfter=12
        )
        
        elements.append(Paragraph("⚠️ Cadets nécessitant un suivi (score < 60%)", attention_style))
        
        attention_data = [['Cadet', 'Section', 'Moyenne', 'Inspections']]
        
        for cadet in stats['cadets_needing_attention']:
            attention_data.append([
                f"{cadet['nom']} {cadet['prenom']}",
                cadet['section_name'],
                f"{cadet['average_score']:.1f}%",
                str(cadet['inspection_count'])
            ])
        
        attention_table = Table(attention_data, colWidths=[2.5*inch, 2*inch, 1.5*inch, 1.5*inch])
        attention_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fee2e2')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elements.append(attention_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Top 10 cadets
    if stats.get('top_cadets'):
        top_style = ParagraphStyle(
            'Top',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#10b981'),
            spaceAfter=12
        )
        
        elements.append(Paragraph("🏆 Top 10 Cadets", top_style))
        
        top_data = [['Rang', 'Cadet', 'Section', 'Moyenne']]
        
        for idx, cadet in enumerate(stats['top_cadets'][:10], 1):
            top_data.append([
                str(idx),
                f"{cadet['nom']} {cadet['prenom']}",
                cadet['section_name'],
                f"{cadet['average_score']:.1f}%"
            ])
        
        top_table = Table(top_data, colWidths=[0.75*inch, 2.5*inch, 2*inch, 1.5*inch])
        top_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#d1fae5'), colors.white])
        ]))
        
        elements.append(top_table)
    
    # Build PDF
    doc.build(elements, onFirstPage=lambda c, d: add_header_footer(c, d, "RAPPORT D'INSPECTIONS"),
              onLaterPages=lambda c, d: add_header_footer(c, d, "RAPPORT D'INSPECTIONS"))
    
    buffer.seek(0)
    return buffer

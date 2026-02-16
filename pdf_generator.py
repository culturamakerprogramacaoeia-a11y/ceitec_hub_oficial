"""
Gerador de Cartões-Resposta em PDF
Gera layouts personalizados com QR Code para correção automatizada
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
import os

class PDFGenerator:
    def __init__(self, output_dir='static/uploads/provas'):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()

    def gerar_cartao(self, prova_id, nome_prova, turma, num_questoes=30, professor=""):
        filename = f"cartao_prova_{prova_id}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=20*mm)
        elements = []

        # Título
        elements.append(Paragraph(f"<b>CEITEC HUB - CARTÃO RESPOSTA</b>", self.styles['Title']))
        elements.append(Spacer(1, 5*mm))
        
        # Cabeçalho
        header_data = [
            [f"Prova: {nome_prova}", f"Turma: {turma}"],
            [f"Professor(a): {professor}", f"Data: ____/____/____"]
        ]
        t = Table(header_data, colWidths=[100*mm, 60*mm])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t)
        elements.append(Spacer(1, 10*mm))

        # QR Code (Contendo ID da Prova)
        qr_code = qr.QrCodeWidget(f'CEITEC|{prova_id}|0|{turma}')
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        d = Drawing(40*mm, 40*mm, transform=[40*mm/width, 0, 0, 40*mm/height, 0, 0])
        d.add(qr_code)
        
        # Nome do Aluno (Campo Manuscrito)
        name_field = [
            [d, Paragraph("NOME DO ALUNO(A): ________________________________________________", self.styles['Normal'])]
        ]
        t_name = Table(name_field, colWidths=[45*mm, 125*mm])
        t_name.setStyle(TableStyle([('ALIGN', (0,0), (0,0), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(t_name)
        elements.append(Spacer(1, 10*mm))

        # Questões OMR
        questoes_data = []
        for i in range(1, num_questoes + 1, 2):
            row = [
                f"{i:02d}", "[A] [B] [C] [D] [E]", "  ",
                f"{i+1:02d}" if i+1 <= num_questoes else "", 
                "[A] [B] [C] [D] [E]" if i+1 <= num_questoes else ""
            ]
            questoes_data.append(row)

        t_qst = Table(questoes_data, colWidths=[10*mm, 60*mm, 20*mm, 10*mm, 60*mm])
        t_qst.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Courier-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (1,-1), 0.5, colors.black),
            ('GRID', (3,0), (4,-1), 0.5, colors.black),
        ]))
        elements.append(t_qst)

        # Instruções
        elements.append(Spacer(1, 20*mm))
        elements.append(Paragraph("<b>INSTRUÇÕES:</b> Use caneta preta ou azul. Preencha totalmente a bolha.", self.styles['Normal']))

        doc.build(elements)
        return filename

    def gerar_caderno_questoes(self, prova_id, nome_prova, turma, questoes, professor=""):
        filename = f"prova_caderno_{prova_id}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=15*mm, leftMargin=20*mm, rightMargin=20*mm)
        elements = []

        # Cabeçalho Escolar Adicionado
        header_table_data = [
            [Paragraph("<b>CEITEC HUB - Plataforma Educacional</b>", self.styles['Heading2']), ""],
            [f"Avaliação: {nome_prova.upper()}", f"Data: ____/____/2026"],
            [f"Professor(a): {professor}", f"Turma: {turma}"],
            [Paragraph("<b>ALUNO(A): __________________________________________________________________</b>", self.styles['Normal']), ""]
        ]
        
        t_header = Table(header_table_data, colWidths=[120*mm, 50*mm])
        t_header.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-3), 0.5, colors.grey),
            ('SPAN', (0,0), (1,0)),
            ('SPAN', (0,3), (1,3)),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,3), (1,3), 10),
            ('TOPPADDING', (0,0), (1,0), 5),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 15*mm))
        
        # Estilo personalizado para questões
        qst_style = ParagraphStyle(
            'QStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            alignment=0, # Justified
            spaceAfter=10
        )
        
        for q in questoes:
            # Enunciado formatado
            texto = q.get('texto') or "Questão sem enunciado."
            p_text = f"<b>{q['numero']}.</b> {texto}"
            elements.append(Paragraph(p_text, qst_style))
            
            # Alternativas com recuo
            alts = q.get('alternativas', [])
            if isinstance(alts, str):
                import json
                try: alts = json.loads(alts)
                except: alts = []
            
            labels = ["A", "B", "C", "D", "E"]
            for i, alt_text in enumerate(alts):
                if i < len(labels):
                    elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;({labels[i]}) {alt_text}", self.styles['Normal']))
            
            elements.append(Spacer(1, 8*mm))

        doc.build(elements)
        return filename

    def gerar_gabarito_professor(self, prova_id, nome_prova, turma, questoes, gabarito, professor=""):
        filename = f"prova_gabarito_{prova_id}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=15*mm, leftMargin=20*mm, rightMargin=20*mm)
        elements = []

        # Cabeçalho do Gabarito
        header_table_data = [
            [Paragraph(f"<b>GABARITO OFICIAL: {nome_prova.upper()}</b>", self.styles['Heading2']), ""],
            [f"Professor(a): {professor}", f"Turma: {turma}"]
        ]
        
        t_header = Table(header_table_data, colWidths=[120*mm, 50*mm])
        t_header.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('SPAN', (0,0), (1,0)),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 10*mm))
        
        qst_style = ParagraphStyle('QStyle', parent=self.styles['Normal'], fontSize=11, leading=14)
        
        for q in questoes:
            num = str(q['numero'])
            resp_correta = gabarito.get(num, "")
            
            p_text = f"<b>{num}.</b> {q.get('texto', '...')}"
            elements.append(Paragraph(p_text, qst_style))
            
            alts = q.get('alternativas', [])
            if isinstance(alts, str):
                import json
                try: alts = json.loads(alts)
                except: alts = []
            
            labels = ["A", "B", "C", "D", "E"]
            for i, alt_text in enumerate(alts):
                if i < len(labels):
                    marca = ""
                    if labels[i] == resp_correta:
                        marca = " <b><font color='green'>[RESPOSTA CORRETA]</font></b>"
                    
                    elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;({labels[i]}) {alt_text}{marca}", self.styles['Normal']))
            
            elements.append(Spacer(1, 5*mm))

        doc.build(elements)
        return filename

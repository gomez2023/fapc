try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False
from datetime import datetime
from typing import Optional

def gerar_pdf_documento(
    nome_reu: str,
    numero_processo: str,
    fundamentacao: str,
    fundamento_legal: str,
    tipo: str = "ILEGAL",
    justica_federal: bool = False
) -> Optional[str]:
    if not REPORTLAB_OK:
        print("reportlab não instalado. Execute: pip install reportlab")
        return None

    nome_base = nome_reu.replace(" ", "_")[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefixo = "Requerimento_Relaxamento" if tipo == "ILEGAL" else "Alerta_Cautelar"
    nome_arquivo = f"{prefixo}_{nome_base}_{timestamp}.pdf"

    try:
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        styles = getSampleStyleSheet()
        titulo_s = ParagraphStyle("Titulo", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=13, spaceAfter=16)
        corpo_s = ParagraphStyle("Corpo", parent=styles["Normal"], alignment=TA_JUSTIFY, fontSize=11, leading=16, spaceAfter=12)
        aviso_s = ParagraphStyle("Aviso", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9, leading=13, textColor=(0.4,0.4,0.4), spaceBefore=20)
        assinatura_s = ParagraphStyle("Assinatura", parent=styles["Normal"], alignment=TA_CENTER, fontSize=11, spaceBefore=40)

        juiz = "JUSTIÇA FEDERAL" if justica_federal else "PODER JUDICIÁRIO DO ESTADO"
        story = [Paragraph(f"<b>{juiz}</b>", titulo_s)]

        if tipo == "ILEGAL":
            story.append(Paragraph("<b>REQUERIMENTO DE RELAXAMENTO DE PRISÃO PREVENTIVA</b><br/><i>(Gerado por sistema automatizado de auditoria – requer assinatura de advogado habilitado)</i>", titulo_s))
            story.append(Paragraph("<b>ATENÇÃO:</b> Este documento é instrumento de apoio à petição defensiva. <b>Não possui validade judicial autônoma.</b> Deve ser apresentado por advogado ou Defensor Público habilitado.", aviso_s))
        else:
            story.append(Paragraph("<b>NOTIFICAÇÃO DE ALERTA CAUTELAR</b><br/><i>(Gerado por sistema automatizado — uso interno da Defesa)</i>", titulo_s))

        story += [
            Paragraph(f"<b>PROCESSO Nº:</b> {numero_processo}", corpo_s),
            Paragraph(f"<b>BENEFICIÁRIO:</b> {nome_reu.upper()}", corpo_s),
            Paragraph(f"<b>DATA DA ANÁLISE:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}", corpo_s),
            Paragraph(f"<b>FUNDAMENTO LEGAL:</b> {fundamento_legal}", corpo_s),
            Paragraph(f"<b>FUNDAMENTAÇÃO:</b> {fundamentacao}", corpo_s),
        ]

        if tipo == "ILEGAL":
            story.append(Paragraph("Com base na análise acima, nos termos do art. 648, I e II, do CPP e na jurisprudência do Supremo Tribunal Federal, requer-se o RELAXAMENTO IMEDIATO da prisão preventiva, por configurar constrangimento ilegal.", corpo_s))

        story.append(Paragraph("____________________________________________<br/><b>Assinatura do Advogado / Defensor Público</b><br/>OAB nº ___________", assinatura_s))
        doc.build(story)
        print(f"\n[PDF GERADO] {nome_arquivo}")
        return nome_arquivo
    except PermissionError:
        print(f"\nSem permissão para escrever {nome_arquivo}")
        return None
    except Exception as e:
        print(f"\nErro ao gerar PDF: {e}")
        return None

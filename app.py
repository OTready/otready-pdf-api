from flask import Flask, request, send_file, jsonify
import io
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak, HRFlowable, KeepTogether)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
import math

app = Flask(__name__)

NAVY        = colors.HexColor("#1F3A5F")
BLUE        = colors.HexColor("#2E75B6")
LIGHT_BLUE  = colors.HexColor("#D6E4F0")
RED         = colors.HexColor("#C00000")
RED_LIGHT   = colors.HexColor("#FDECEA")
AMBER       = colors.HexColor("#ED7D31")
AMBER_LIGHT = colors.HexColor("#FEF3E2")
GREEN       = colors.HexColor("#375623")
GREEN_LIGHT = colors.HexColor("#E2EFDA")
GRAY        = colors.HexColor("#F5F5F5")
GRAY_MID    = colors.HexColor("#D9D9D9")
WHITE       = colors.white
TEXT_DARK   = colors.HexColor("#1A1A1A")
TEXT_MID    = colors.HexColor("#444444")
TEXT_LIGHT  = colors.HexColor("#777777")
PW, PH      = A4

def make_styles():
    return {
        'cover_title': ParagraphStyle('cover_title', fontName='Helvetica-Bold',
            fontSize=26, textColor=NAVY, leading=32, spaceAfter=6),
        'h1': ParagraphStyle('h1', fontName='Helvetica-Bold',
            fontSize=12, textColor=WHITE, leading=16,
            backColor=NAVY, spaceBefore=14, spaceAfter=8,
            borderPadding=(6,12,6,12)),
        'h2': ParagraphStyle('h2', fontName='Helvetica-Bold',
            fontSize=10.5, textColor=WHITE, leading=14,
            backColor=BLUE, spaceBefore=10, spaceAfter=6,
            borderPadding=(5,8,5,8)),
        'h3': ParagraphStyle('h3', fontName='Helvetica-Bold',
            fontSize=10, textColor=NAVY, leading=13,
            spaceBefore=8, spaceAfter=3),
        'body': ParagraphStyle('body', fontName='Helvetica',
            fontSize=9, textColor=TEXT_DARK, leading=13,
            spaceBefore=2, spaceAfter=3),
        'body_small': ParagraphStyle('body_small', fontName='Helvetica',
            fontSize=8, textColor=TEXT_MID, leading=11,
            spaceBefore=1, spaceAfter=1),
        'bullet': ParagraphStyle('bullet', fontName='Helvetica',
            fontSize=9, textColor=TEXT_DARK, leading=12,
            leftIndent=12, firstLineIndent=-10,
            spaceBefore=2, spaceAfter=2),
        'bullet_bold': ParagraphStyle('bullet_bold', fontName='Helvetica-Bold',
            fontSize=9, textColor=NAVY, leading=12,
            leftIndent=12, firstLineIndent=-10,
            spaceBefore=4, spaceAfter=1),
        'caption': ParagraphStyle('caption', fontName='Helvetica-Oblique',
            fontSize=7.5, textColor=TEXT_LIGHT, leading=10, spaceAfter=4),
        'disclaimer': ParagraphStyle('disclaimer', fontName='Helvetica-Oblique',
            fontSize=8, textColor=TEXT_LIGHT, leading=11,
            spaceBefore=4, spaceAfter=4),
        'horizon': ParagraphStyle('horizon', fontName='Helvetica-Bold',
            fontSize=8.5, textColor=BLUE, leading=11,
            spaceBefore=5, spaceAfter=1),
    }

def status_color(score):
    if score <= 1.2: return RED, RED_LIGHT, "FRAGILE"
    if score <= 2.2: return AMBER, AMBER_LIGHT, "INTERMEDIO"
    return GREEN, GREEN_LIGHT, "STRUTTURATO"

def on_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PH-3*cm, PW, 3*cm, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, PH-3.25*cm, PW, 0.25*cm, fill=1, stroke=0)
    canvas.setFillColor(GRAY)
    canvas.rect(0, 0, PW, 1.1*cm, fill=1, stroke=0)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(1.5*cm, 0.4*cm, "Prodotto da: Riccardo Talarico  |  otready.tech")
    canvas.drawRightString(PW-1.5*cm, 0.4*cm, "RISERVATO - USO INTERNO / CONSULENZIALE")
    canvas.restoreState()

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PH-1.3*cm, PW, 1.3*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawString(1.5*cm, PH-0.8*cm, "OTReady")
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(PW-1.5*cm, PH-0.8*cm, "OT Cyber Risk & Maturity Assessment Report")
    canvas.setFillColor(GRAY)
    canvas.rect(0, 0, PW, 0.9*cm, fill=1, stroke=0)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(1.5*cm, 0.3*cm, "Prodotto da: Riccardo Talarico  |  otready.tech")
    canvas.drawRightString(PW-1.5*cm, 0.3*cm, f"Pagina {doc.page}")
    canvas.restoreState()

def score_bar_chart(scores):
    labels = ["S1 Contesto OT","S2 Architettura IT/OT",
              "S3 Accessi e Fornitori","S4 Continuita Operativa",
              "S5 Change Management","S6 Governance"]
    d = Drawing(420, 195)
    bh,gap,lw,bmax,ys = 19,7,142,210,155
    for i,(lbl,val) in enumerate(zip(labels,scores)):
        y = ys - i*(bh+gap)
        col,bg,txt = status_color(val)
        d.add(String(lw-4,y+5,lbl,fontName='Helvetica',fontSize=7.5,
                     fillColor=TEXT_DARK,textAnchor='end'))
        d.add(Rect(lw,y,bmax,bh,fillColor=GRAY,strokeColor=None,strokeWidth=0))
        bw = int((val/3.0)*bmax)
        if bw>0:
            d.add(Rect(lw,y,bw,bh,fillColor=col,strokeColor=None,strokeWidth=0))
        d.add(String(lw+bmax+5,y+5,f"{val:.2f}",
                     fontName='Helvetica-Bold',fontSize=8,fillColor=TEXT_DARK))
        d.add(String(lw+bmax+36,y+5,txt,
                     fontName='Helvetica-Bold',fontSize=7,fillColor=col))
    for v in [0,1,1.5,2,3]:
        x = lw+int((v/3.0)*bmax)
        d.add(String(x,ys-6*(bh+gap)-12,str(v),
                     fontName='Helvetica',fontSize=6.5,fillColor=TEXT_LIGHT,textAnchor='middle'))
        d.add(Line(x,ys-6*(bh+gap),x,ys+bh,strokeColor=GRAY_MID,strokeWidth=0.4))
    return d

def radar_chart(scores):
    labels=["S1","S2","S3","S4","S5","S6"]
    n,cx,cy,rm = 6,120,120,85
    d = Drawing(240,240)
    for lv in [1,2,3]:
        r=int((lv/3.0)*rm)
        for i in range(n):
            a1=math.pi/2-i*2*math.pi/n
            a2=math.pi/2-(i+1)*2*math.pi/n
            d.add(Line(cx+r*math.cos(a1),cy+r*math.sin(a1),
                       cx+r*math.cos(a2),cy+r*math.sin(a2),
                       strokeColor=GRAY_MID,strokeWidth=0.4))
    for i in range(n):
        a=math.pi/2-i*2*math.pi/n
        d.add(Line(cx,cy,cx+rm*math.cos(a),cy+rm*math.sin(a),
                   strokeColor=GRAY_MID,strokeWidth=0.4))
    pts=[]
    for i,v in enumerate(scores):
        a=math.pi/2-i*2*math.pi/n
        r=(v/3.0)*rm
        pts.extend([cx+r*math.cos(a),cy+r*math.sin(a)])
    d.add(Polygon(pts,fillColor=colors.HexColor("#2E75B6"),
                  strokeColor=BLUE,strokeWidth=1.5,fillOpacity=0.3))
    for i,v in enumerate(scores):
        a=math.pi/2-i*2*math.pi/n
        r=(v/3.0)*rm
        col,_,_ = status_color(v)
        d.add(Rect(cx+r*math.cos(a)-3.5,cy+r*math.sin(a)-3.5,7,7,
                   fillColor=col,strokeColor=WHITE,strokeWidth=0.8))
    for i,lbl in enumerate(labels):
        a=math.pi/2-i*2*math.pi/n
        lx=cx+(rm+16)*math.cos(a)
        ly=cy+(rm+16)*math.sin(a)
        d.add(String(lx,ly,lbl,fontName='Helvetica-Bold',fontSize=7,
                     fillColor=NAVY,textAnchor='middle'))
    return d

def h1(t,S): return Paragraph(t,S['h1'])
def h2(t,S): return Paragraph(t,S['h2'])
def h3(t,S): return Paragraph(t,S['h3'])
def body(t,S): return Paragraph(t,S['body'])
def sp(h=5): return Spacer(1,h)
def hr(): return HRFlowable(width="100%",thickness=0.4,color=LIGHT_BLUE,spaceAfter=4,spaceBefore=3)

def bul(text,S,bold=False):
    st = S['bullet_bold'] if bold else S['bullet']
    return Paragraph(f"• {text}",st)

def callout(text,S):
    t=Table([[Paragraph(text,S['body'])]],colWidths=[430])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),LIGHT_BLUE),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ]))
    return t

def clean(text, maxlen=None):
    text = re.sub(r'<br\s*/?>',' ',text)
    text = re.sub(r'<[^>]+>','',text)
    text = re.sub(r'\*\*([^*]+)\*\*',r'\1',text)
    text = re.sub(r'\*([^*]+)\*',r'\1',text)
    text = re.sub(r'#{1,4}\s*','',text)
    text = re.sub(r'\s+',' ',text).strip()
    if maxlen and len(text)>maxlen:
        text = text[:maxlen]+'...'
    return text

def norm_tbl(rows,S):
    bs=ParagraphStyle('bsn',fontName='Helvetica',fontSize=7.5,textColor=TEXT_DARK,leading=10)
    conv=[]
    for row in rows:
        conv.append([Paragraph(clean(str(c)),bs) if isinstance(c,str) else c for c in row])
    t=Table(conv,colWidths=[6.8*cm,2*cm,10.2*cm])
    style=[
        ('BACKGROUND',(0,0),(-1,0),NAVY),
        ('FONTSIZE',(0,0),(-1,-1),7.5),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('GRID',(0,0),(-1,-1),0.3,GRAY_MID),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,GRAY]),
    ]
    sm={"FRAGILE":(RED,RED_LIGHT),"LIMITATO":(RED,RED_LIGHT),
        "PARZIALE":(AMBER,AMBER_LIGHT),"INTERMEDIO":(AMBER,AMBER_LIGHT),
        "STRUTTURATO":(GREEN,GREEN_LIGHT),"CONFORME":(GREEN,GREEN_LIGHT)}
    for i in range(1,len(rows)):
        cell=rows[i][1] if isinstance(rows[i][1],str) else ""
        for key,(col,bg) in sm.items():
            if key in cell.upper():
                style.extend([('BACKGROUND',(1,i),(1,i),bg),
                               ('TEXTCOLOR',(1,i),(1,i),col),
                               ('FONTNAME',(1,i),(1,i),'Helvetica-Bold')])
                break
    t.setStyle(TableStyle(style))
    return t

def extract_field(text,patterns,default='Non specificato',maxlen=60):
    for p in patterns:
        m=re.search(p,text,re.IGNORECASE)
        if m:
            val=m.group(1).strip()
            val=re.split(r'\n|nel settore|questa configurazione|L\'assenza|La gestione|espone',val)[0]
            val=clean(val).strip('|').strip()
            if val and len(val)<maxlen:
                return val
    return default

def parse_report(text):
    data={
        'azienda':     extract_field(text,[r'Azienda[:\s*]+([^\n|]{2,50})']),
        'settore':     extract_field(text,[r'Settore[:\s*]+([^\n|]{2,50})']),
        'dimensione':  extract_field(text,[r'Dimensione[:\s*]+([^\n|]{2,50})']),
        'nis2':        extract_field(text,[r'Esposizione NIS2[:\s*]+([^\n|]{2,40})',
                                           r'Esposizione normativa[:\s*]+([^\n|]{2,40})']),
        'fornitori':   extract_field(text,[r'Fornitori[^\n:]*[:\s*]+([^\n|]{2,40})']),
        'compilato_da':extract_field(text,[r'Compilato da[:\s*]+([^\n|]{2,50})']),
        'data':        extract_field(text,[r'Data[^\n:]*[:\s*]+(\d{1,2}[^\n|]{3,20}\d{4})']),
        'score_global':0.0,'icn':0.0,'cap_rule':False,
        'livello':'Non determinato',
        'scores':{'S1':0.0,'S2':0.0,'S3':0.0,'S4':0.0,'S5':0.0,'S6':0.0},
        'full_text':text,
    }
    m=re.search(r'Score[^:\n]*[:\s]+([\d]+\.[\d]+)',text)
    if m: data['score_global']=float(m.group(1))
    m=re.search(r'ICN[:\s]+([\d]+\.[\d]+)',text)
    if m: data['icn']=float(m.group(1))
    m=re.search(r'Livello\s+(\d+\s*[-–]\s*\w+)',text)
    if m: data['livello']=m.group(1).strip()
    if 'CAP RULE' in text.upper() and 'NON ATTIVA' not in text.upper() and 'ATTIVA' in text.upper():
        data['cap_rule']=True
    for i in range(1,7):
        m=re.search(rf'S{i}[^:.\n]{{0,30}}[:\s]+([\d]+\.[\d]+)',text)
        if m: data['scores'][f'S{i}']=float(m.group(1))
    return data

def split_sections(text):
    sections={}
    markers={
        'exec':r'(?:1\.|#+\s*1\.)\s*EXECUTIVE SUMMARY',
        'profilo':r'(?:2\.|#+\s*2\.)\s*PROFILO',
        'risultati':r'(?:3\.|#+\s*3\.)\s*RISULTATI',
        'analisi':r'(?:4\.|#+\s*4\.)\s*ANALISI',
        'rischi':r'(?:5\.|#+\s*5\.)\s*TOP\s*5',
        'roadmap':r'(?:6\.|#+\s*6\.)\s*ROADMAP',
        'normativa':r'(?:7\.|#+\s*7\.)\s*ALLINEAMENTO',
        'metodologia':r'(?:8\.|#+\s*8\.)\s*METODOLOGIA',
        'disclaimer':r'(?:9\.|#+\s*9\.)\s*DISCLAIMER',
    }
    positions={}
    for key,pattern in markers.items():
        m=re.search(pattern,text,re.IGNORECASE)
        if m: positions[key]=m.start()
    sorted_keys=sorted(positions.keys(),key=lambda k:positions[k])
    for i,key in enumerate(sorted_keys):
        start=positions[key]
        end=positions[sorted_keys[i+1]] if i+1<len(sorted_keys) else len(text)
        sections[key]=text[start:end]
    return sections

def parse_domains(text):
    domains=[]
    pattern=r'(S[1-6]\s*[-–]\s*[A-Z][^\n]+)\s*[—-]+\s*Score\s*([\d.]+)\s*[—-]+\s*([A-Z]+)'
    matches=list(re.finditer(pattern,text,re.IGNORECASE))
    for i,m in enumerate(matches):
        title=clean(m.group(1).strip(),80)
        score=float(m.group(2))
        status=m.group(3).strip()
        start=m.end()
        end=matches[i+1].start() if i+1<len(matches) else len(text)
        content=text[start:end]

        why=''
        m2=re.search(r'[Pp]erche[^\n]*conta[^\n]*\n(.*?)(?=Cosa emerge|$)',content,re.DOTALL)
        if m2: why=clean(m2.group(1),400)

        ev_end=content.find('Rischi') if 'Rischi' in content else len(content)//2
        evidenze=[clean(e,200) for e in re.findall(r'[•\-\*]\s*(.+)',content[:ev_end]) if len(clean(e))>10][:5]

        rs=content.find('Rischi'); rc=content.find('Raccomandaz')
        rischi_text=content[rs:rc] if rs>0 and rc>rs else ''
        rischi=[clean(r,200) for r in re.findall(r'[•\-\*]\s*(.+)',rischi_text) if len(clean(r))>10][:3]

        recs={'0-90 giorni':[],'3-9 mesi':[],'9-18 mesi':[]}
        if rc>0:
            rec_text=content[rc:]
            cur='0-90 giorni'
            for line in rec_text.split('\n'):
                line=line.strip()
                if re.search(r'0.90|0–90',line): cur='0-90 giorni'
                elif re.search(r'3.9|3–9',line): cur='3-9 mesi'
                elif re.search(r'9.18|9–18',line): cur='9-18 mesi'
                elif line.startswith(('•','-','*')) and len(line)>5:
                    recs[cur].append(clean(line,200))

        domains.append({'title':title,'score':score,'status':status,
                        'why':why,'evidenze':evidenze,'rischi':rischi,'recs':recs})
    return domains

def parse_risks(text):
    risks=[]
    for line in text.split('\n'):
        if '|' in line and not re.match(r'^[\s|:-]+$',line):
            parts=[p.strip() for p in line.split('|')]
            if len(parts)>=2 and len(parts[0])>5:
                risks.append(parts[:4])
    return risks[:5]

def parse_roadmap(text):
    items=[]
    for line in text.split('\n'):
        if '|' in line and not re.match(r'^[\s|:-]+$',line):
            parts=[p.strip() for p in line.split('|')]
            if len(parts)>=3 and len(parts[0])>5:
                items.append(parts[:4])
    return items

def build_pdf(report_text):
    S=make_styles()
    data=parse_report(report_text)
    sections=split_sections(report_text)
    scores_list=[data['scores'][f'S{i}'] for i in range(1,7)]

    buffer=io.BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=A4,
        leftMargin=1.7*cm,rightMargin=1.7*cm,
        topMargin=2.0*cm,bottomMargin=1.7*cm)
    story=[]

    # COVER
    story.append(Spacer(1,3.2*cm))
    story.append(Paragraph("OT Cyber Risk &amp; Maturity",S['cover_title']))
    story.append(Paragraph("Assessment Report",
        ParagraphStyle('ct2',fontName='Helvetica-Bold',fontSize=20,
                       textColor=BLUE,leading=26,spaceAfter=4)))
    story.append(Paragraph("Valutazione di maturita e governance del rischio cyber OT",
        ParagraphStyle('cs',fontName='Helvetica-Oblique',fontSize=10,
                       textColor=TEXT_MID,leading=14,spaceAfter=16)))
    story.append(HRFlowable(width="100%",thickness=1.5,color=BLUE,spaceAfter=14))
    meta=[["Azienda",data['azienda']],["Settore",data['settore']],
          ["Dimensione",data['dimensione']],["Esposizione NIS2",data['nis2']],
          ["Compilato da",data['compilato_da']],["Data assessment",data['data']]]
    mt=Table(meta,colWidths=[4.5*cm,11*cm])
    mt.setStyle(TableStyle([
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),('FONTNAME',(1,0),(1,-1),'Helvetica'),
        ('FONTSIZE',(0,0),(-1,-1),9),('TEXTCOLOR',(0,0),(0,-1),NAVY),
        ('BACKGROUND',(0,0),(0,-1),LIGHT_BLUE),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),8),('GRID',(0,0),(-1,-1),0.3,GRAY_MID),
    ]))
    story.append(mt)
    story.append(sp(14))
    story.append(Paragraph("<i>RISERVATO - USO INTERNO / CONSULENZIALE</i>",
        ParagraphStyle('conf',fontName='Helvetica-Oblique',fontSize=8,textColor=RED)))
    story.append(PageBreak())

    # 1. EXECUTIVE SUMMARY
    story.append(h1("1. Executive Summary",S))
    story.append(sp(4))
    g_col,g_bg,g_txt=status_color(data['score_global'])
    i_col,i_bg,i_txt=status_color(data['icn'])
    kpi=[[
        Paragraph(f"<b>Livello di Maturita OT</b><br/><br/>"
                  f"<font size=12><b>Livello {data['livello']}</b></font><br/>"
                  f"<font size=9.5><b>Score: {data['score_global']:.2f}/3 — {g_txt}</b></font>",S['body']),
        Paragraph(f"<b>Indice di Coerenza Normativa (ICN)</b><br/><br/>"
                  f"<font size=12><b>ICN: {data['icn']:.2f}/3</b></font><br/>"
                  f"<font size=9.5><b>{i_txt}</b></font>",S['body']),
    ]]
    kt=Table(kpi,colWidths=[9.5*cm,9.5*cm])
    kt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,0),g_bg),('BACKGROUND',(1,0),(1,0),i_bg),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
        ('BOX',(0,0),(0,0),1,g_col),('BOX',(1,0),(1,0),1,i_col),
    ]))
    story.append(kt)
    story.append(sp(8))
    if data['cap_rule']:
        story.append(callout(
            "CAP RULE ATTIVA: Le sezioni Accessi (S3) e/o Continuita Operativa (S4) "
            "presentano criticita strutturali che limitano il livello complessivo raggiungibile.",S))
        story.append(sp(6))
    exec_text=sections.get('exec','')
    story.append(h3("Messaggi chiave per il management",S))
    bullets_exec=re.findall(r'[•\-\*]\s*\*?\*?([^•\-\*\n]{20,})',exec_text)
    if not bullets_exec:
        paras=[p.strip() for p in exec_text.split('\n') if len(p.strip())>50]
        bullets_exec=paras[1:5]
    for b in bullets_exec[:5]:
        story.append(bul(clean(b,250),S,bold=True))
        story.append(sp(2))
    story.append(PageBreak())

    # 2. PROFILO
    story.append(h1("2. Profilo della valutazione",S))
    story.append(sp(4))
    prof=[["Azienda",data['azienda'],"Settore",data['settore']],
          ["Dimensione",data['dimensione'],"Fornitori OT",data['fornitori']],
          ["Esposizione NIS2",data['nis2'],"Compilato da",data['compilato_da']],
          ["Data assessment",data['data'],"Strumento","OTReady v3.0"]]
    pt=Table(prof,colWidths=[3.8*cm,5.8*cm,3.8*cm,5.6*cm])
    pt.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),('FONTNAME',(2,0),(2,-1),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),8),('TEXTCOLOR',(0,0),(0,-1),NAVY),('TEXTCOLOR',(2,0),(2,-1),NAVY),
        ('BACKGROUND',(0,0),(0,-1),LIGHT_BLUE),('BACKGROUND',(2,0),(2,-1),LIGHT_BLUE),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),6),('GRID',(0,0),(-1,-1),0.3,GRAY_MID),
    ]))
    story.append(pt)
    story.append(sp(8))
    story.append(body("Valutazione basata su questionario strutturato di 31 domande (scala 0-3) "
                      "organizzate in 6 domini operativi. Non e' un audit tecnico, non certifica "
                      "conformita normativa. L'obiettivo e' fornire al management una fotografia "
                      "pratica dello stato attuale e una roadmap concreta di miglioramento.",S))
    story.append(PageBreak())

    # 3. RISULTATI
    story.append(h1("3. Risultati per sezione",S))
    story.append(sp(5))
    sec_labels=[
        ("S1 - Contesto OT e Criticita", data['scores']['S1'],"10%"),
        ("S2 - Architettura IT/OT",      data['scores']['S2'],"20%"),
        ("S3 - Accessi e Fornitori",      data['scores']['S3'],"25%"),
        ("S4 - Continuita Operativa",     data['scores']['S4'],"20%"),
        ("S5 - Change Management",        data['scores']['S5'],"15%"),
        ("S6 - Governance e Normativa",   data['scores']['S6'],"10%"),
    ]
    hdr=[Paragraph(f"<font color='white'><b>{t}</b></font>",S['body_small'])
         for t in ["Sezione","Score","Stato","Peso"]]
    rows=[hdr]
    for name,score,weight in sec_labels:
        col,bg,txt=status_color(score)
        rows.append([
            Paragraph(name,S['body_small']),
            Paragraph(f"<b>{score:.2f}</b>",ParagraphStyle('sv',fontName='Helvetica-Bold',
                fontSize=9,textColor=col,leading=11)),
            Paragraph(f"<b>{txt}</b>",ParagraphStyle('st',fontName='Helvetica-Bold',
                fontSize=8,textColor=col,leading=10)),
            Paragraph(weight,S['body_small']),
        ])
    g_col2,_,g_txt2=status_color(data['score_global'])
    rows.append([
        Paragraph("<font color='white'><b>SCORE GLOBALE PONDERATO</b></font>",
            ParagraphStyle('sg',fontName='Helvetica-Bold',fontSize=8.5,textColor=WHITE,leading=11)),
        Paragraph(f"<b>{data['score_global']:.2f}</b>",
            ParagraphStyle('sgv',fontName='Helvetica-Bold',fontSize=11,textColor=WHITE,leading=13)),
        Paragraph(f"<b>{g_txt2}</b>",
            ParagraphStyle('sgl',fontName='Helvetica-Bold',fontSize=8,textColor=WHITE,leading=10)),
        Paragraph(f"ICN: {data['icn']:.2f}",
            ParagraphStyle('icnl',fontName='Helvetica',fontSize=8,textColor=WHITE,leading=10)),
    ])
    st_style=[
        ('BACKGROUND',(0,0),(-1,0),NAVY),('BACKGROUND',(0,-1),(-1,-1),NAVY),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),5),('GRID',(0,0),(-1,-1),0.3,GRAY_MID),
        ('ROWBACKGROUNDS',(0,1),(-1,-2),[WHITE,GRAY]),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]
    for i,(_,score,_) in enumerate(sec_labels):
        col,bg,_=status_color(score)
        st_style.append(('BACKGROUND',(2,i+1),(2,i+1),bg))
    sec_tbl=Table(rows,colWidths=[7*cm,1.8*cm,2.5*cm,7.7*cm])
    sec_tbl.setStyle(TableStyle(st_style))
    story.append(sec_tbl)
    story.append(sp(14))
    story.append(h3("3.1 Score per sezione",S))
    story.append(sp(3))
    story.append(score_bar_chart(scores_list))
    story.append(Paragraph("Fig. 1 – Score per sezione. Rosso=Fragile, Arancio=Intermedio, Verde=Strutturato.",S['caption']))
    story.append(KeepTogether([
        sp(10),h3("3.2 Profilo di maturita",S),sp(3),
        Table([[radar_chart(scores_list)]],colWidths=[19*cm],
              style=[('ALIGN',(0,0),(-1,-1),'CENTER')]),
        Paragraph("Fig. 2 – Radar chart del profilo di maturita OT.",S['caption']),
    ]))
    story.append(PageBreak())

    # 4. ANALISI
    story.append(h1("4. Analisi dettagliata per dominio",S))
    analisi_text=sections.get('analisi',report_text)
    domains=parse_domains(analisi_text)
    if domains:
        for dom in domains:
            col,bg,txt=status_color(dom['score'])
            story.append(sp(8))
            sec_hdr=Table([[
                Paragraph(f"<b>{dom['title']}</b>",
                    ParagraphStyle('dh',fontName='Helvetica-Bold',fontSize=10,textColor=WHITE,leading=13)),
                Paragraph(f"Score: <b>{dom['score']:.2f}</b> — <b>{dom['status']}</b>",
                    ParagraphStyle('ds',fontName='Helvetica-Bold',fontSize=9,textColor=WHITE,leading=12)),
            ]],colWidths=[12*cm,7*cm])
            sec_hdr.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,-1),col),
                ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
                ('LEFTPADDING',(0,0),(0,0),10),('RIGHTPADDING',(1,0),(1,0),10),
                ('ALIGN',(1,0),(1,0),'RIGHT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ]))
            story.append(sec_hdr)
            story.append(sp(5))
            if dom['why']:
                story.append(Paragraph("<b>Perche conta in OT</b>",S['h3']))
                story.append(body(dom['why'],S))
                story.append(sp(3))
            if dom['evidenze']:
                story.append(Paragraph("<b>Cosa emerge</b>",S['h3']))
                for e in dom['evidenze']:
                    story.append(bul(e,S))
                story.append(sp(3))
            if dom['rischi']:
                story.append(Paragraph("<b>Rischi operativi</b>",S['h3']))
                for r in dom['rischi']:
                    story.append(bul(r,S))
                story.append(sp(3))
            if any(dom['recs'][k] for k in dom['recs']):
                story.append(Paragraph("<b>Raccomandazioni</b>",S['h3']))
                for horizon,actions in dom['recs'].items():
                    if actions:
                        story.append(Paragraph(f"<b>{horizon}:</b>",S['horizon']))
                        for a in actions[:3]:
                            story.append(bul(a,S))
            story.append(hr())
    story.append(PageBreak())

    # 5. TOP 5 RISCHI
    story.append(h1("5. Top 5 Rischi Operativi",S))
    story.append(sp(5))
    rischi_text=sections.get('rischi','')
    risks_data=parse_risks(rischi_text)
    rhdr=[Paragraph(f"<font color='white'><b>{t}</b></font>",S['body_small'])
          for t in ["#","Rischio","Priorita","Impatto potenziale"]]
    rrows=[rhdr]
    pc={"CRITICA":RED,"ALTA":AMBER,"MEDIA":AMBER,"BASSA":GREEN}
    if risks_data:
        for i,parts in enumerate(risks_data):
            while len(parts)<4: parts.append("")
            prio=parts[1].strip().upper() if len(parts)>1 else ""
            pcol=pc.get(prio,AMBER)
            rrows.append([
                Paragraph(f"<b>{i+1}</b>",ParagraphStyle('rn',fontName='Helvetica-Bold',
                    fontSize=8,textColor=WHITE,leading=10)),
                Paragraph(clean(parts[0],150),S['body_small']),
                Paragraph(f"<b>{prio}</b>",ParagraphStyle('rp',fontName='Helvetica-Bold',
                    fontSize=7.5,textColor=pcol,leading=10)),
                Paragraph(clean(parts[2] if len(parts)>2 else "",150),S['body_small']),
            ])
    rt=Table(rrows,colWidths=[0.6*cm,7*cm,1.8*cm,9.6*cm])
    rs=[
        ('BACKGROUND',(0,0),(-1,0),NAVY),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),4),('GRID',(0,0),(-1,-1),0.3,GRAY_MID),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,GRAY]),
    ]
    for i,parts in enumerate(risks_data):
        prio=parts[1].strip().upper() if len(parts)>1 else ""
        pcol=pc.get(prio,AMBER)
        rs.append(('BACKGROUND',(0,i+1),(0,i+1),pcol))
    rt.setStyle(TableStyle(rs))
    story.append(rt)
    story.append(PageBreak())

    # 6. ROADMAP
    story.append(h1("6. Roadmap e Priorita",S))
    story.append(sp(4))
    story.append(body("La roadmap e' progettata per essere realistica in una PMI con risorse limitate.",S))
    story.append(sp(6))
    roadmap_text=sections.get('roadmap','')
    rm_items=parse_roadmap(roadmap_text)
    rmhdr=[Paragraph(f"<font color='white'><b>{t}</b></font>",S['body_small'])
           for t in ["Iniziativa","Orizzonte","Effort","Owner"]]
    rmrows=[rmhdr]
    hc={"0-90":RED,"0–90":RED,"3-9":AMBER,"3–9":AMBER,"9-18":GREEN,"9–18":GREEN}
    if rm_items:
        for parts in rm_items:
            while len(parts)<4: parts.append("")
            hor=parts[1].strip() if len(parts)>1 else ""
            hcol=RED
            for k,v in hc.items():
                if k in hor: hcol=v; break
            rmrows.append([
                Paragraph(clean(parts[0],150),S['body_small']),
                Paragraph(f"<b>{clean(hor)}</b>",ParagraphStyle('rh2',fontName='Helvetica-Bold',
                    fontSize=7.5,textColor=hcol,leading=10)),
                Paragraph(clean(parts[2] if len(parts)>2 else "",20),S['body_small']),
                Paragraph(clean(parts[3] if len(parts)>3 else "",80),S['body_small']),
            ])
    rmt=Table(rmrows,colWidths=[9*cm,2*cm,1.5*cm,6.5*cm])
    rmt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),4),('GRID',(0,0),(-1,-1),0.3,GRAY_MID),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,GRAY]),
    ]))
    story.append(rmt)
    story.append(PageBreak())

    # 7. NORMATIVA
    story.append(h1("7. Allineamento Normativo",S))
    story.append(sp(5))
    story.append(h2("7.1  IEC 62443",S))
    story.append(sp(3))
    bs=ParagraphStyle('bsn',fontName='Helvetica',fontSize=7.5,textColor=TEXT_DARK,leading=10)
    iec_rows=[
        [Paragraph("<font color='white'><b>Principio</b></font>",S['body_small']),
         Paragraph("<font color='white'><b>Stato</b></font>",S['body_small']),
         Paragraph("<font color='white'><b>Osservazione</b></font>",S['body_small'])],
        [Paragraph("Identificazione e autenticazione (IAC)",bs),"FRAGILE",
         Paragraph("Account individuali e MFA su accessi remoti",bs)],
        [Paragraph("Controllo accessi (AC)",bs),"PARZIALE",
         Paragraph("Processo di revoca e tracciabilita sessioni",bs)],
        [Paragraph("Integrita sistema (SI)",bs),"PARZIALE",
         Paragraph("Patch management e change management",bs)],
        [Paragraph("Continuita e disponibilita (RA)",bs),"PARZIALE",
         Paragraph("Backup testati e RTO validati operativamente",bs)],
        [Paragraph("Governance e policy",bs),"FRAGILE",
         Paragraph("Policy OT documentate e revisione management",bs)],
    ]
    story.append(norm_tbl(iec_rows,S))
    story.append(sp(10))
    story.append(h2("7.2  NIS2 – Direttiva UE 2022/2555",S))
    story.append(sp(3))
    nis2_rows=[
        [Paragraph("<font color='white'><b>Macro-requisito NIS2</b></font>",S['body_small']),
         Paragraph("<font color='white'><b>Stato</b></font>",S['body_small']),
         Paragraph("<font color='white'><b>Osservazione</b></font>",S['body_small'])],
        [Paragraph("Governance rischio cyber (art. 21)",bs),"FRAGILE",
         Paragraph("Policy OT e revisione periodica management",bs)],
        [Paragraph("Misure tecniche (backup, MFA, segmentazione)",bs),"PARZIALE",
         Paragraph("Completezza e test periodici da verificare",bs)],
        [Paragraph("Gestione incidenti e notifica 24h (art. 23)",bs),"PARZIALE",
         Paragraph("Procedure risposta ed escalation formale",bs)],
        [Paragraph("Sicurezza supply chain – fornitori (art. 21)",bs),"FRAGILE",
         Paragraph("Accessi fornitori con MFA e tracciabilita",bs)],
        [Paragraph("Formazione e awareness (art. 21)",bs),"PARZIALE",
         Paragraph("Formazione specifica OT periodica",bs)],
    ]
    story.append(norm_tbl(nis2_rows,S))
    story.append(PageBreak())

    # 8-9. METODOLOGIA E DISCLAIMER
    story.append(h1("8. Metodologia",S))
    story.append(sp(4))
    for title,text in [
        ("Natura dell'assessment",
         "Valutazione non invasiva basata su questionario strutturato di 31 domande in 6 sezioni operative. "
         "Non e' un audit tecnico, non include test di vulnerabilita."),
        ("Scala di valutazione",
         "0=Assente, 1=Informale, 2=Parziale, 3=Governato (formalizzato, documentato, revisionato)."),
        ("Score globale e pesi",
         "S1=10%, S2=20%, S3=25%, S4=20%, S5=15%, S6=10%. "
         "Accessi (S3) e Continuita (S4) hanno peso maggiore per impatto operativo diretto."),
        ("Cap Rule",
         "Se S3 o S4 sono <=1.2, il livello non puo superare Livello 2 - Consapevole."),
        ("ICN","S2x25% + S3x30% + S4x25% + S6x20%. Misura l'allineamento a IEC 62443 e NIS2."),
    ]:
        story.append(KeepTogether([
            Paragraph(f"<b>{title}</b>",S['h3']),body(text,S),sp(3)]))
    story.append(sp(6))
    story.append(h1("9. Disclaimer",S))
    story.append(sp(4))
    story.append(Paragraph(
        "Questo report e' un output di assessment di maturita OT basato su questionario strutturato. "
        "Non sostituisce audit tecnici, penetration test o certificazioni normative. Le raccomandazioni "
        "devono essere adattate al contesto specifico con il supporto di figure tecniche qualificate. "
        "<b>Prodotto da: Riccardo Talarico – otready.tech</b>",S['disclaimer']))

    doc.build(story,onFirstPage=on_cover,onLaterPages=on_page)
    buffer.seek(0)
    return buffer

@app.route('/health',methods=['GET'])
def health():
    return jsonify({'status':'ok','service':'OTReady PDF Generator v3'})

@app.route('/generate-pdf',methods=['POST'])
def generate_pdf():
    try:
        body_data=request.get_json(force=True)
        report_text=body_data.get('report_text','')
        if not report_text:
            return jsonify({'error':'report_text is required'}),400
        pdf_buffer=build_pdf(report_text)
        return send_file(pdf_buffer,mimetype='application/pdf',
                         as_attachment=True,download_name='OTReady_Report.pdf')
    except Exception as e:
        return jsonify({'error':str(e)}),500

if __name__=='__main__':
    import os
    port=int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0',port=port)

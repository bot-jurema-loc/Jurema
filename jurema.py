import streamlit as st
import pandas as pd
import os
import re
import unicodedata
import pdfplumber
import io
import zipfile
import base64
import fitz
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="Gestão de Faturas e Veículos", page_icon="logo_empresa.png" if os.path.exists("logo_empresa.png") else "📄", layout="wide")

def _aplicar_logo():
    logo_path = "logo_empresa.png"
    icone_path = "logo_icone.png" if os.path.exists("logo_icone.png") else logo_path
    if os.path.exists(logo_path):
        try:
            st.logo(logo_path, icon_image=icone_path, size="large")
            return
        except AttributeError:
            pass 
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.sidebar.markdown(f'<div style="text-align:center; padding:8px 0 12px 0;"><img src="data:image/png;base64,{b64}" width="180"></div>', unsafe_allow_html=True)
    else:
        st.sidebar.caption("⚠️ `logo.png` não encontrado na pasta do app.")

_aplicar_logo()

col_logo_titulo, col_texto_titulo = st.columns([0.04, 0.96], gap=None, vertical_alignment="center")
with col_logo_titulo:
    if os.path.exists("logo_empresa.png"):
        st.image("logo_empresa.png", width=58)
with col_texto_titulo:
    st.title("Jurema > Localiza")

responsaveis_obras = {
    "001J": "LUCIANO BACURAU", "003J": "LUCIANO BACURAU", "013J": "ROBERT", "015J": "LUCIANO BACURAU", "017J": "LUCIANO BACURAU", "02.005-MZJ": "LUCIANO BACURAU",
    "02.050-MZJ": "ROBERT", "02.065-MZJ": "GIOVANE SANTOS", "02.079-MZJ": "GIOVANE SANTOS", "02.090-MZJ": "GUILHERME PEDREIRA", "02.096-MZJ": "GIOVANE SANTOS", "02.103-MZJ": "GIOVANE SANTOS",
    "02.104-MZJ": "GIOVANE SANTOS", "02.105-MZJ": "ROBERT", "02.106-MZJ": "EDUARDO FERREIRA", "02.107-MZJ": "JOSE IVO", "02.110-MZJ": "GIOVANE SANTOS", "02.111-MZJ": "EDUARDO FERREIRA",
    "02.112-MZJ": "GIOVANE SANTOS", "03.001-MZJ": "LAURA GALVÃO", "3.001-MZJ": "LAURA GALVÃO", "03.002-MZJ": "LAURA GALVÃO", "3.002-MZJ": "LAURA GALVÃO", "03.003-MZJ": "LAURA GALVÃO",
    "3.003-MZJ": "LAURA GALVÃO", "02.102-MZJ": "NÃO INFORMADO", "02.113-MZJ": "NÃO INFORMADO",
}

responsaveis_placas = {
    "TYW4C52": "WELNER DE NASARETH PEREIRA BRITO", "TZH5A80": "VITORIA GABRIELLE DE MOURA MACEDO VELOSO", "TYD9F70": "TOPOGRAFIA", "TZP6G88": "THIAGO HENRIQUE DOS SANTOS", "TZL7I93": "THIAGO HENRIQUE DOS SANTOS",
    "TZH5I11": "TATIARA", "TZD3D04": "RONALDO CALAÇO DA SILVA", "TZO3F74": "ROMULO ALBERTO DE NEGREIROS SOUZA", "TZH6D13": "RENATO FERNANDES", "TZX7E04": "REGINALDO OLIVEIRA DA SILVA", "TYE4H30": "RASILSON",
    "TYW6D64": "RAFAEL", "TYT1C93": "RAEL LIRA", "TYT1C94": "RAEL LIRA", "TZP6G87": "PAULO HENRIQUE MAIA", "TZT1J32": "NAELSON FERNANDES DE SOUSA OLIVEIRA", "TYK5G44": "MINERVINO NETO", "UVM0D01": "MICHAEL MOREIRA DE BARROS",
    "TZM6J85": "MAURICIO PESSOA ROSA", "TZO3F72": "MARINA DE JESUS VIANA CARVALHO", "TXW7C65": "MARINA DE JESUS VIANA CARVALHO", "TYY0H65": "MARIA EDUARDA LOPES SILVA BARBOSA", "TZV7C01": "MARIA CLARA", "TXZ5J42": "LEONARDO CAMPELO",
    "TZD6E87": "LAURA GALVAO LOURENCO CESAR", "UVJ4I59": "JOSE IVO DA SILVA FILHO", "TXP5I56": "JOSE IVO", "TZB2J50": "JOSE HELDER SOUSA DE OLIVEIRA", "TYW2B88": "JOSE ALVES", "TYW2B83": "JOSE ALVES",
    "TYY7G53": "JOÃO ROSA", "TXS3C32": "JOÃO PEDRO ENGENHEIRO", "TZT8D69": "JOAO PAULO DE ARAUJO", "TZX7E44": "JOAO DE SOUSA MARINHO", "UVU2G17": "JEFFERSON SOUZA DUARTE ARAUJO", "TZD9H74": "ISMAEL COMPRADOR",
    "TYW7B93": "HIDELGARDES SOARES DE OLIVEIRA", "TZD9H72": "HALLYSSON RODRIGUES DE ALMEIDA", "TXO9I18": "GUSTAVO JOSE DE COSTA", "UAC6J61": "GUILHERME AUGUSTO PEDREIRA E CUNHA", "TYE5C85": "GIVALDO", "UAB8C95": "GIOVANNI DE MOURA SANTOS",
    "TYA9C08": "GIOVANNI DE MOURA SANTOS", "TXH6C24": "GILCIVAN JOSE PEREIRA SANTOS", "TYW2B86": "GABRIEL TOPOGRAFO", "TYQ2F20": "FREEDE", "UVS4G54": "FRANCISCO FABIO DE OLIVEIRA", "UAC0H25": "FRANCISCO DE ASSIS GONCALVES PEREIRA JUNIOR",
    "UVU2G08": "FRANCISCO ARAUJO DA SILVA", "TZL7J75": "EZILDO PEREIRA DA SILVA", "TYE5C81": "EULER LABORATORIO", "TXZ5J41": "EULER LABORATORIO", "TYQ2F21": "ENG. RODRIGO", "TYO2F36": "ENC. ADRIANO",
    "TZX7E72": "ELAINE DOS SANTOS CAMELO", "TZO3F78": "EDILEUDO", "TYZ5C85": "CLAUDEMIR", "TZU4A24": "CARLOS CESAR DA SILVA OLIVEIRA", "TZW1I09": "CARLO EDUARDO SANTOS FERREIRA", "TYV9F49": "BRITO - TOPOGRAFO",
    "TZL7I92": "ANTONIO KELSON DE CASTRO FREIRE", "TEQ2G86": "ANTONIO FEITOSA NUMES", "UVR6I93": "ALLAN FISCAL", "TZB2G92": "ALDEVANDO CARVALHO PAZ", "TZH4I50": "JOSE AURICELIO",
}

obras_por_codigo = {
    "001J": "ESCRITORIO", "003J": "APOIO CENTRAL", "013J": "SINALIZAÇÃO", "015J": "OFICINA - APOIO", "017J": "LOGISTICA", "02.005-MZJ": "MANUTENÇÃO", "02.050-MZJ": "BARRAGEM - ATALAIA",
    "02.065-MZJ": "USINA M. ASFALTICA", "02.079-MZJ": "IDEPI - ENTRE RIOS", "02.090-MZJ": "CONSERVA - ENTRE RIOS", "02.096-MZJ": "PAV. CANAUBAIS", "02.103-MZJ": "RODOVIA BR-330", "02.104-MZJ": "PAV. AEROPORTO",
    "02.105-MZJ": "RODOVIA BR-316", "02.106-MZJ": "PRATINHA - 3º ETAPA", "02.107-MZJ": "RODOVIA BR-235 - BOM JESUS", "02.111-MZJ": "CS GRÃOS", "02.112-MZJ": "AEROPORTO PALMAS - TO", "03.001-MZJ": "ANAJAS PIRIPIRI",
    "03.002-MZJ": "SÃO JOÃO E SÃO FELIX", "03.003-MZJ": "EMPREEMDIMENTO FAIXA 2 (TIMON)", "3.001-MZJ": "SPE - FLOR DO CAMPO",
}

def limpar_placa(placa):
    if pd.isna(placa): return ""
    p = str(placa).replace("-", "").replace(" ", "").strip().upper()
    return {"7ZD3D04": "TZD3D04"}.get(p, p)

def formatar_visual_placa(placa):
    p = limpar_placa(placa)
    return f"{p[:3]}-{p[3:]}" if len(p) == 7 else p

def normalizar_colunas_veiculos(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={"Ativos": "Apelido", "Ativo": "Apelido", "Nome do Ativo": "Apelido", "Código Obra": "Obra - Código", "Codigo Obra": "Obra - Código", "Nome da Obra": "Obra", "Placa do Veículo": "Placa"})
    for col in ["Apelido", "Obra", "Obra - Código", "Placa"]:
        if col not in df.columns: df[col] = ""
    return df[["Apelido", "Obra", "Obra - Código", "Placa"]]

pasta_app = os.path.dirname(os.path.abspath(__file__))

def localizar_base_veiculos():
    candidatos = []
    for nome in os.listdir(pasta_app):
        if not nome.lower().endswith((".xlsx", ".xls")) or nome.startswith("~$"): continue
        caminho = os.path.join(pasta_app, nome)
        try:
            colunas_originais = {str(c).strip().lower() for c in pd.read_excel(caminho, nrows=0).columns}
            if any("placa" in c for c in colunas_originais) and any(t in " ".join(colunas_originais) for t in ["ativo", "apelido", "obra", "codigo"]):
                score = sum(1 for t in ["placa", "ativo", "apelido", "obra", "código obra", "codigo obra"] if any(t in c for c in colunas_originais))
                candidatos.append((score, os.path.getmtime(caminho), caminho))
        except Exception:
            continue
    if candidatos: return sorted(candidatos, key=lambda item: (item[0], item[1]), reverse=True)[0][2]
    return os.path.join(pasta_app, "base_veiculos.xlsx")

BASE_VEICULOS = localizar_base_veiculos()

def placa_eh_valida(valor): return bool(re.fullmatch(r"[A-Z]{3}[0-9][A-Z0-9][0-9]{2}", limpar_placa(valor)))

@st.cache_data
def carregar_dados_excel():
    if not os.path.exists(BASE_VEICULOS): 
        return pd.DataFrame(columns=["Placa_Limpa", "Placa", "Ativo", "Código Obra", "Nome da Obra", "Responsável Obra"])
    try:
        bruto = normalizar_colunas_veiculos(pd.read_excel(BASE_VEICULOS))
        df = bruto.copy()
        df["Placa_Limpa"] = df["Placa"].apply(limpar_placa)
        df = df[df["Placa_Limpa"].apply(placa_eh_valida)]
        df = df.drop_duplicates(subset=["Placa_Limpa"], keep="first")
        for col in ["Apelido", "Obra - Código", "Obra"]: 
            df[col] = df[col].fillna("").astype(str).str.strip()
        df["Obra"] = df.apply(lambda r: obras_por_codigo.get(str(r["Obra - Código"]).strip(), r["Obra"]), axis=1)
        df["Responsável Obra"] = df["Obra - Código"].map(responsaveis_obras).fillna("NÃO INFORMADO")
        df["Responsável Obra"] = df["Placa_Limpa"].map(responsaveis_placas).fillna(df["Responsável Obra"])
        df["Placa"] = df["Placa_Limpa"].apply(formatar_visual_placa)
        return df.rename(columns={"Apelido": "Ativo", "Obra - Código": "Código Obra", "Obra": "Nome da Obra"})[["Placa_Limpa", "Placa", "Ativo", "Código Obra", "Nome da Obra", "Responsável Obra"]]
    except Exception as erro:
        st.session_state["erro_planilha"] = str(erro)
        return pd.DataFrame()

def importar_veiculos_excel(arquivo):
    existentes = normalizar_colunas_veiculos(pd.read_excel(BASE_VEICULOS)) if os.path.exists(BASE_VEICULOS) else pd.DataFrame(columns=["Apelido", "Obra", "Obra - Código", "Placa"])
    novos = normalizar_colunas_veiculos(pd.read_excel(arquivo))
    existentes_por_placa = {limpar_placa(l["Placa"]): l for _, l in existentes.iterrows() if limpar_placa(l["Placa"])}
    placas_lote, adicionar, relatorio = set(), [], []
    for _, linha in novos.iterrows():
        placa = limpar_placa(linha["Placa"])
        if not placa or placa in {"NAN", "NAOTEM"} or not placa_eh_valida(placa):
            relatorio.append({"Placa": str(linha["Placa"]), "Situação": "Ignorado", "Motivo": "Inválida", "Ativo no Excel enviado": str(linha["Apelido"]), "Obra no Excel enviado": str(linha["Obra"]), "Código no Excel enviado": str(linha["Obra - Código"]), "Ativo mantido na base": "", "Obra mantida na base": "", "Código mantido na base": ""})
        elif placa in existentes_por_placa:
            relatorio.append({"Placa": formatar_visual_placa(placa), "Situação": "Mantido", "Motivo": "Já existia", "Ativo no Excel enviado": str(linha["Apelido"]), "Obra no Excel enviado": str(linha["Obra"]), "Código no Excel enviado": str(linha["Obra - Código"]), "Ativo mantido na base": str(existentes_por_placa[placa]["Apelido"]), "Obra mantida na base": str(existentes_por_placa[placa]["Obra"]), "Código mantido na base": str(existentes_por_placa[placa]["Obra - Código"])})
        elif placa in placas_lote:
            relatorio.append({"Placa": formatar_visual_placa(placa), "Situação": "Ignorado", "Motivo": "Repetido no envio", "Ativo no Excel enviado": str(linha["Apelido"]), "Obra no Excel enviado": str(linha["Obra"]), "Código no Excel enviado": str(linha["Obra - Código"]), "Ativo mantido na base": "", "Obra mantida na base": "", "Código mantido na base": ""})
        else:
            reg = linha.copy(); reg["Placa"] = formatar_visual_placa(placa); adicionar.append(reg); placas_lote.add(placa)
            relatorio.append({"Placa": formatar_visual_placa(placa), "Situação": "Adicionado", "Motivo": "Nova", "Ativo no Excel enviado": str(linha["Apelido"]), "Obra no Excel enviado": str(linha["Obra"]), "Código no Excel enviado": str(linha["Obra - Código"]), "Ativo mantido na base": "—", "Obra mantida na base": "—", "Código mantido na base": "—"})
    if adicionar: pd.concat([existentes, pd.DataFrame(adicionar)], ignore_index=True).to_excel(BASE_VEICULOS, index=False, sheet_name="Lista Patrimônio")
    return sum(1 for i in relatorio if i["Situação"] == "Adicionado"), sum(1 for i in relatorio if i["Situação"] == "Mantido"), sum(1 for i in relatorio if i["Situação"].startswith("Ignorado")), pd.DataFrame(relatorio)

df_veiculos = carregar_dados_excel()

def sem_acento(s): return "".join(c for c in unicodedata.normalize("NFD", s.upper()) if unicodedata.category(c) != "Mn")

def localizar_area_descricao(page):
    words = page.get_text("words")
    desc = [w for w in words if sem_acento(w[4].strip().rstrip(':')) == "DESCRICAO"]
    if not desc: return None
    h = min(desc, key=lambda w: w[1])
    bottoms = [w[1] for w in words if sem_acento(w[4].strip().rstrip(':')) == "VENCIMENTO" and w[1] > h[1]]
    if not bottoms: return None
    bottom = min(bottoms) - 7; x0 = page.rect.x0 + page.rect.width * 0.055; cy_h = (h[1] + h[3]) / 2
    valor = [w for w in words if sem_acento(w[4].strip()) == "VALOR" and w[0] > h[2] and abs((w[1] + w[3]) / 2 - cy_h) <= 5]
    x1 = (min(valor, key=lambda w: w[0])[0] - 8) if valor else page.rect.x0 + page.rect.width * 0.70
    top = h[3] + 8; occupied = []
    for block in page.get_text("blocks"):
        bx0, by0, bx1, by1, btext = block[:5]; norm = sem_acento(btext)
        if by1 <= top or by0 >= bottom or bx0 >= x1 or bx1 <= x0 or "DESCRICAO" in norm or "VENCIMENTO" in norm: continue
        occupied.append(by1)
    y_start = max([top + 8] + [v + 7 for v in occupied])
    return fitz.Rect(x0, y_start, x1, bottom) if y_start + 28 <= bottom else None

def quebrar_texto(texto, fonte, tamanho, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = f"{atual} {palavra}".strip()
        if not atual or fitz.get_text_length(teste, fontname=fonte, fontsize=tamanho) <= largura: atual = teste
        else: linhas.append(atual); atual = palavra
    if atual: linhas.append(atual)
    return linhas

def inserir_identificacao_no_boleto(pdf_bytes, dados):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        alvo = None
        for page in doc:
            area = localizar_area_descricao(page)
            if area:
                alvo = (page, area)
                break
        if not alvo: return pdf_bytes
        page, area = alvo
        esq = [f"ATIVO: {dados.get('apelido', 'NÃO INFORMADO')}", f"OBRA: {dados.get('obra', 'NÃO INFORMADA')}", f"CÓDIGO DA OBRA: {dados.get('codigo', 'NÃO INFORMADO')}"]
        for tam in (8.5, 8, 7.5, 7, 6.5, 6):
            col_e = [l for t in esq for l in quebrar_texto(t, "hebo", tam, area.width - 8)]
            if len(col_e) * tam * 1.3 <= area.height: break
        else: tam = 6; col_e = [l for t in esq for l in quebrar_texto(t, "hebo", tam, area.width - 8)]
        y = area.y0 + tam
        for linha in col_e:
            page.insert_text(fitz.Point(area.x0, y), linha, fontname="hebo", fontsize=tam, color=(1, 0, 0), overlay=True); y += tam * 1.3
        return doc.tobytes(garbage=4, deflate=True)
    finally: doc.close()

def processar_pdf(arquivo_pdf, nome_arquivo):
    arquivo_pdf.seek(0); paginas_por_contrato = {}
    lista_placas_reais = df_veiculos["Placa_Limpa"].tolist() if not df_veiculos.empty else []
    with pdfplumber.open(arquivo_pdf) as pdf_leitura:
        for num_pagina, pagina in enumerate(pdf_leitura.pages):
            texto = pagina.extract_text()
            if not texto: continue
            texto_upper = texto.upper()
            match_fatura = re.search(r'(CGMTZ|CAMTZ|AGMTZ|MTMTZ)[\s\-]*(\d+)', texto_upper)
            if not match_fatura: continue
            contrato = f"{match_fatura.group(1)} {match_fatura.group(2)}"
            if contrato not in paginas_por_contrato: paginas_por_contrato[contrato] = {"paginas": [], "placas": set()}
            paginas_por_contrato[contrato]["paginas"].append(num_pagina)
            for p in re.findall(r'([A-Z0-9]{3}[0-9][A-Z0-9][0-9]{2})', texto_upper):
                if limpar_placa(p) in lista_placas_reais: paginas_por_contrato[contrato]["placas"].add(limpar_placa(p))
            for p1, p2 in re.findall(r'([A-Z0-9]{3})\s*([0-9][A-Z0-9][0-9]{2})', re.sub(r'[^A-Z0-9 \n]', ' ', texto_upper)):
                if limpar_placa(p1 + p2) in lista_placas_reais: paginas_por_contrato[contrato]["placas"].add(limpar_placa(p1 + p2))
    resultados = []
    if paginas_por_contrato:
        arquivo_pdf.seek(0); leitor = PdfReader(arquivo_pdf)
        for contrato, info in paginas_por_contrato.items():
            escritor = PdfWriter()
            for indice in info["paginas"]: escritor.add_page(leitor.pages[indice])
            buffer_saida = io.BytesIO(); escritor.write(buffer_saida)
            placas_ordenadas = sorted(info["placas"]); placa = placas_ordenadas[0] if placas_ordenadas else ""
            dados_escrita = None
            if placa and not df_veiculos.empty:
                info_veiculo = df_veiculos[df_veiculos["Placa_Limpa"] == placa]
                if not info_veiculo.empty: dados_escrita = {"apelido": info_veiculo.iloc[0]["Ativo"], "obra": info_veiculo.iloc[0]["Nome da Obra"], "codigo": info_veiculo.iloc[0]["Código Obra"]}
            pdf_final = buffer_saida.getvalue()
            if dados_escrita: pdf_final = inserir_identificacao_no_boleto(pdf_final, dados_escrita)
            resultados.append({"contrato": contrato, "pdf_bytes": pdf_final, "placas": placas_ordenadas, "paginas": len(info["paginas"]), "arquivo_origem": nome_arquivo})
    return resultados

@st.cache_data(show_spinner=False)
def processar_pdfs_cache(arquivos_bytes):
    lista_faturas, arquivos_limpos = [], {}
    for nome_arquivo, dados_bytes in arquivos_bytes:
        for r in processar_pdf(io.BytesIO(dados_bytes), nome_arquivo):
            nome_limpo = f"LIMPO_{r['contrato'].replace(' ', '_')}.pdf"; arquivos_limpos[nome_limpo] = r["pdf_bytes"]
            if r["placas"]:
                for placa in r["placas"]: lista_faturas.append({"Nº Fatura": r["contrato"], "Placa_Encontrada": placa, "Placa_Formatada": formatar_visual_placa(placa), "Arquivo PDF": nome_arquivo, "Arquivo Limpo": nome_limpo, "Páginas Mantidas": r["paginas"]})
            else: lista_faturas.append({"Nº Fatura": r["contrato"], "Placa_Encontrada": "", "Placa_Formatada": "SEM PLACA", "Arquivo PDF": nome_arquivo, "Arquivo Limpo": nome_limpo, "Páginas Mantidas": r["paginas"]})
    return lista_faturas, arquivos_limpos

@st.cache_data(show_spinner=False)
def montar_zip_cache(nomes_arquivos, arquivos_limpos_items):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, dados in arquivos_limpos_items:
            if nome in set(nomes_arquivos): zf.writestr(nome, dados)
    return buf.getvalue()

@st.cache_data(show_spinner=False)
def unificar_pdfs_cache(nomes_pdfs, arquivos_limpos_items):
    escritor_final = PdfWriter()
    for nome, dados in arquivos_limpos_items:
        if nome in set(nomes_pdfs):
            for pagina in PdfReader(io.BytesIO(dados)).pages: escritor_final.add_page(pagina)
    buffer_saida = io.BytesIO(); escritor_final.write(buffer_saida)
    return buffer_saida.getvalue()

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
with st.expander("🚗 Cadastro e banco de veículos", expanded=False):
    st.markdown("Consulte a base atual, importe novos veículos e baixe a planilha atualizada.")
    st.caption(f"O aplicativo está procurando planilhas na pasta: `{pasta_app}`")
    st.caption(f"Planilha identificada: `{os.path.basename(BASE_VEICULOS)}`")
    
    if "erro_planilha" in st.session_state:
        st.error(f"Erro ao ler a planilha: {st.session_state['erro_planilha']}")
        
    st.metric("Veículos com placa cadastrada", len(df_veiculos))
    
    if not df_veiculos.empty: 
        st.dataframe(df_veiculos[["Ativo", "Nome da Obra", "Código Obra", "Placa"]], use_container_width=True, hide_index=True)
    else: 
        st.warning("⚠️ A base não possui veículos válidos. Verifique se as colunas da planilha estão corretas (Placa, Obra, Código Obra, Ativo).")
        
    arquivo_novos_veiculos = st.file_uploader("Importar Excel com novos veículos", type=["xlsx", "xls"], key="importar_novos_veiculos")
    if arquivo_novos_veiculos is not None:
        st.caption("Colunas aceitas: Apelido/Ativo, Obra, Obra - Código e Placa.")
        if st.button("Adicionar veículos novos à base", type="primary"):
            try:
                st.session_state["relatorio_importacao_veiculos"] = dict(zip(["adicionados", "mantidos", "invalidos", "detalhes"], importar_veiculos_excel(arquivo_novos_veiculos)))
                carregar_dados_excel.clear(); st.rerun()
            except Exception as erro: st.error(f"Erro ao importar: {erro}")
            
    if "relatorio_importacao_veiculos" in st.session_state:
        rel = st.session_state["relatorio_importacao_veiculos"]
        st.markdown("### Resultado da última importação")
        c1, c2, c3 = st.columns(3)
        c1.metric("Novos veículos adicionados", rel["adicionados"]); c2.metric("Placas existentes preservadas", rel["mantidos"]); c3.metric("Linhas ignoradas", rel["invalidos"])
        st.caption("Atenção: esta rotina não substitui registros existentes. Quando a placa já está cadastrada, os dados da base são mantidos.")
        if not rel["detalhes"].empty: st.dataframe(rel["detalhes"], use_container_width=True, hide_index=True)
        if st.button("Fechar relatório da importação", key="fechar_relatorio_importacao"):
            del st.session_state["relatorio_importacao_veiculos"]; st.rerun()
            
    if os.path.exists(BASE_VEICULOS):
        with open(BASE_VEICULOS, "rb") as arquivo_base:
            st.download_button("📥 Baixar banco de veículos atualizado (Excel)", data=arquivo_base.read(), file_name=os.path.basename(BASE_VEICULOS), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="baixar_base_veiculos")

st.subheader("1. Envie os arquivos PDF")
pdfs_enviados = st.file_uploader("Selecione os PDFs", type=["pdf"], accept_multiple_files=True)
botao_processar = st.button("Processar PDFs", type="primary")

# --- CORREÇÃO PARA LIMPAR A MEMÓRIA AO REMOVER O PDF ---
if not pdfs_enviados:
    st.session_state.pop("lista_faturas", None)
    st.session_state.pop("arquivos_limpos", None)

if pdfs_enviados and botao_processar:
    if df_veiculos.empty:
        st.error("⚠️ O banco de veículos está vazio. Certifique-se de que a planilha está na pasta listada acima e que ela possui os dados corretos.")
    else:
        arquivos_bytes = tuple((getattr(p, "name", "arquivo.pdf"), p.getvalue()) for p in pdfs_enviados)
        with st.spinner("Processando PDFs, separando por contrato e escrevendo dados do veículo..."):
            st.session_state["lista_faturas"], st.session_state["arquivos_limpos"] = processar_pdfs_cache(arquivos_bytes)

# Se já processamos PDFs alguma vez nesta sessão, desenha os resultados
if "lista_faturas" in st.session_state and "arquivos_limpos" in st.session_state:
    lista_faturas = st.session_state["lista_faturas"]
    arquivos_limpos_para_zip = st.session_state["arquivos_limpos"]

    if lista_faturas:
        df_faturas = pd.DataFrame(lista_faturas)
        df_final = pd.merge(df_faturas, df_veiculos, left_on="Placa_Encontrada", right_on="Placa_Limpa", how="left")
        for col, val in [("Ativo", "-"), ("Código Obra", "-"), ("Nome da Obra", "NÃO ENCONTRADA"), ("Responsável Obra", "NÃO INFORMADO")]:
            df_final[col] = df_final[col].fillna(val)
        df_final["Nº Fatura"] = df_final["Nº Fatura"].astype(str)
        df_final = df_final.sort_values(by="Nº Fatura").drop_duplicates(subset=["Nº Fatura", "Placa_Encontrada"], keep='first')
        
        if not df_final.empty:
            df_exibicao = df_final[["Arquivo PDF", "Nº Fatura", "Placa_Formatada", "Ativo", "Código Obra", "Nome da Obra", "Responsável Obra"]].rename(columns={"Placa_Formatada": "Placa"})
            
            st.sidebar.header("🔍 Filtrar Faturas")
            filtro_obra = st.sidebar.multiselect("Filtrar por Nome da Obra:", sorted(df_exibicao["Nome da Obra"].dropna().astype(str).unique()))
            filtro_codigo = st.sidebar.multiselect("Filtrar por Código da Obra:", sorted(df_exibicao["Código Obra"].dropna().astype(str).unique()))
            filtro_fatura = st.sidebar.multiselect("Filtrar por Nº da Fatura:", sorted(df_exibicao["Nº Fatura"].dropna().astype(str).unique()))
            filtro_placa = st.sidebar.multiselect("Filtrar por Placa:", sorted(df_exibicao["Placa"].dropna().astype(str).unique()))
            
            df_filtrado = df_exibicao.copy()
            if filtro_obra: df_filtrado = df_filtrado[df_filtrado["Nome da Obra"].isin(filtro_obra)]
            if filtro_codigo: df_filtrado = df_filtrado[df_filtrado["Código Obra"].isin(filtro_codigo)]
            if filtro_fatura: df_filtrado = df_filtrado[df_filtrado["Nº Fatura"].isin(filtro_fatura)]
            if filtro_placa: df_filtrado = df_filtrado[df_filtrado["Placa"].isin(filtro_placa)]
            
            st.subheader("2. Resultado do Cruzamento")
            st.markdown(f"**Total de faturas processadas:** {len(df_filtrado)}")
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
            st.download_button("📥 Baixar Relatório (CSV)", data=df_filtrado.to_csv(index=False).encode('utf-8-sig'), file_name='faturas_por_obra.csv', mime='text/csv')
        
        st.markdown("---")
        st.subheader("3. Downloads dos PDFs Limpos")
        st.write("Cada contrato gera **um PDF limpo separado**, já com o Ativo e Obra escritos em vermelho na área de descrição.")
        
        if arquivos_limpos_para_zip:
            arquivos_limpos_items = tuple(arquivos_limpos_para_zip.items())
            if len(arquivos_limpos_para_zip) > 1:
                st.download_button(f"📦 Baixar TODOS os contratos (.ZIP) — {len(arquivos_limpos_para_zip)} arquivo(s)", data=montar_zip_cache(tuple(arquivos_limpos_para_zip.keys()), arquivos_limpos_items), file_name="contratos_limpos_TODOS.zip", mime="application/zip", type="primary", key="dl_todos")
            else:
                nome_arq = list(arquivos_limpos_para_zip.keys())[0]
                st.download_button(f"📄 Baixar {nome_arq}", data=arquivos_limpos_para_zip[nome_arq], file_name=nome_arq, mime="application/pdf", type="primary", key="dl_unico")
            
            st.markdown("#### Baixar por obra (Arquivos Separados em ZIP)")
            if (filtro_obra or filtro_codigo) and not df_final.empty:
                pares = df_final[["Código Obra", "Nome da Obra"]].drop_duplicates().sort_values(["Código Obra", "Nome da Obra"])
                if filtro_obra: pares = pares[pares["Nome da Obra"].isin(filtro_obra)]
                if filtro_codigo: pares = pares[pares["Código Obra"].isin(filtro_codigo)]
                if pares.empty: st.warning("Nenhuma obra corresponde à combinação de filtros selecionada.")
                else:
                    for _, row in pares.iterrows():
                        cod, nome = row["Código Obra"], row["Nome da Obra"]
                        contratos_da_obra = df_final.loc[(df_final["Código Obra"] == cod) & (df_final["Nome da Obra"] == nome), "Nº Fatura"].unique().tolist()
                        nomes_zip = [f"LIMPO_{c.replace(' ', '_')}.pdf" for c in contratos_da_obra if f"LIMPO_{c.replace(' ', '_')}.pdf" in arquivos_limpos_para_zip]
                        rotulo = f"{cod} · {nome}"
                        if not nomes_zip: st.warning(f"Obra **{rotulo}**: nenhum PDF limpo encontrado."); continue
                        nome_zip = f"contratos_{re.sub(r'[^A-Za-z0-9]+', '_', cod).strip('_')}_{re.sub(r'[^A-Za-z0-9]+', '_', nome).strip('_')}.zip"
                        st.download_button(f"📦 Baixar PDFs – {rotulo} ({len(nomes_zip)} contrato(s))", data=montar_zip_cache(tuple(nomes_zip), arquivos_limpos_items), file_name=nome_zip, mime="application/zip", key=f"dl_obra_{cod}_{nome}")
            else: st.info("Marque um **Nome da Obra** e/ou um **Código da Obra** no filtro lateral para baixar os contratos separados por obra.")
            
            st.markdown("---")
            st.subheader("4. Unificar PDFs da mesma obra em um único arquivo")
            st.write("Selecione uma obra no filtro lateral para juntar todas as faturas dessa obra em um único PDF.")
            if (filtro_obra or filtro_codigo) and not df_final.empty:
                pares = df_final[["Código Obra", "Nome da Obra"]].drop_duplicates().sort_values(["Código Obra", "Nome da Obra"])
                if filtro_obra: pares = pares[pares["Nome da Obra"].isin(filtro_obra)]
                if filtro_codigo: pares = pares[pares["Código Obra"].isin(filtro_codigo)]
                for _, row in pares.iterrows():
                    cod, nome = row["Código Obra"], row["Nome da Obra"]
                    contratos_da_obra = df_final.loc[(df_final["Código Obra"] == cod) & (df_final["Nome da Obra"] == nome), "Nº Fatura"].unique().tolist()
                    nomes_pdf = [f"LIMPO_{c.replace(' ', '_')}.pdf" for c in contratos_da_obra if f"LIMPO_{c.replace(' ', '_')}.pdf" in arquivos_limpos_para_zip]
                    if not nomes_pdf: continue
                    total_paginas = sum(len(PdfReader(io.BytesIO(arquivos_limpos_para_zip[n_pdf])).pages) for n_pdf in nomes_pdf)
                    nome_unificado = f"UNIFICADO_{re.sub(r'[^A-Za-z0-9]+', '_', cod).strip('_')}_{re.sub(r'[^A-Za-z0-9]+', '_', nome).strip('_')}.pdf"
                    st.download_button(label=f"📄 Unificar PDF – {cod} · {nome} ({len(nomes_pdf)} contratos, {total_paginas} páginas)", data=unificar_pdfs_cache(tuple(nomes_pdf), arquivos_limpos_items), file_name=nome_unificado, mime="application/pdf", key=f"unificar_obra_{cod}_{nome}", type="primary")
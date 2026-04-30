import streamlit as st
import pandas as pd
import calendar
import json
from datetime import datetime
import io
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Mapeamento de meses para português
MESES_PT_BR = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# Configuração da página
st.set_page_config(layout="wide", page_title="Agenda de Consultas", page_icon="🗕️")

# --- ESTILO CSS PERSONALIZADO ---
st.markdown("""
<style>
    .calendar-day {
        border-radius: 5px;
        padding: 8px;
        min-height: 80px;
        margin: 2px;
        cursor: pointer;
    }
    .calendar-day:hover {
        opacity: 0.8;
    }
    .selected-day {
        border: 2px solid #FF4B4B !important;
    }
    .weekday-header {
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
        color: #333;
    }
    .stAlert {
        padding: 10px;
        border-radius: 5px;
    }
    .invisible-button {
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        opacity: 0;
        cursor: pointer;
    }
    .day-container {
        position: relative;
    }
    .filter-active {
        background-color: #e6f7ff;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 4px solid #1890ff;
    }
    .connection-test {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .connection-success {
        background-color: #e6ffed;
        border-left: 4px solid #52c41a;
    }
    .connection-warning {
        background-color: #fffbe6;
        border-left: 4px solid #faad14;
    }
    .connection-error {
        background-color: #fff2f0;
        border-left: 4px solid #ff4d4f;
    }

    /* Estilo da tela de login */
    .login-box {
        max-width: 400px;
        margin: 80px auto;
        padding: 40px;
        border-radius: 12px;
        background-color: #f9f9f9;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        text-align: center;
    }
    .login-title {
        font-size: 1.8em;
        font-weight: bold;
        color: #002060;
        margin-bottom: 8px;
    }
    .login-subtitle {
        font-size: 0.95em;
        color: #666;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# --- FUNÇÕES COM REQUESTS (SEM SELENIUM) ---
# ============================================================

def criar_sessao_com_retry():
    """Cria uma sessão com retry automático"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fazer_login(session, username, password):
    """Faz login no Vivver usando requests"""
    try:
        # Primeiro, pegar a página de login para obter cookies/tokens
        login_url = "https://itabira-mg.vivver.com/login"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        }
        
        # Primeira requisição para pegar cookies
        response = session.get(login_url, headers=headers, timeout=30)
        
        # Dados do login
        login_data = {
            'conta': username,
            'password': password,
            'action': 'login'
        }
        
        # Tentativa de login
        response = session.post(login_url, data=login_data, headers=headers, timeout=30)
        
        # Verificar se login foi bem sucedido
        if 'dashboard' in response.url or response.status_code == 200:
            # Verificar se não voltou para página de login (erro)
            if 'login' not in response.url:
                return True, "Login realizado com sucesso!"
            else:
                return False, "Usuário ou senha inválidos"
        
        return False, "Falha no login"
        
    except Exception as e:
        return False, f"Erro no login: {str(e)}"

def buscar_dados_api(session):
    """Busca os dados da API após login"""
    try:
        # URL da API com todos os parâmetros
        url_api = "https://itabira-mg.vivver.com/bit/gadget/view_paginate.json?id=228&draw=1&columns%5B0%5D%5Bdata%5D=0&columns%5B0%5D%5Bname%5D=&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=true&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=1&columns%5B1%5D%5Bname%5D=&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=true&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=2&columns%5B2%5D%5Bname%5D=&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=3&columns%5B3%5D%5Bname%5D=&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B4%5D%5Bdata%5D=4&columns%5B4%5D%5Bname%5D=&columns%5B4%5D%5Bsearchable%5D=true&columns%5B4%5D%5Borderable%5D=true&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B5%5D%5Bdata%5D=5&columns%5B5%5D%5Bname%5D=&columns%5B5%5D%5Bsearchable%5D=true&columns%5B5%5D%5Borderable%5D=true&columns%5B5%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B5%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B6%5D%5Bdata%5D=6&columns%5B6%5D%5Bname%5D=&columns%5B6%5D%5Bsearchable%5D=true&columns%5B6%5D%5Borderable%5D=true&columns%5B6%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B6%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B7%5D%5Bdata%5D=7&columns%5B7%5D%5Bname%5D=&columns%5B7%5D%5Bsearchable%5D=true&columns%5B7%5D%5Borderable%5D=true&columns%5B7%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B7%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B8%5D%5Bdata%5D=8&columns%5B8%5D%5Bname%5D=&columns%5B8%5D%5Bsearchable%5D=true&columns%5B8%5D%5Borderable%5D=true&columns%5B8%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B8%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B9%5D%5Bdata%5D=9&columns%5B9%5D%5Bname%5D=&columns%5B9%5D%5Bsearchable%5D=true&columns%5B9%5D%5Borderable%5D=true&columns%5B9%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B9%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B10%5D%5Bdata%5D=10&columns%5B10%5D%5Bname%5D=&columns%5B10%5D%5Bsearchable%5D=true&columns%5B10%5D%5Borderable%5D=true&columns%5B10%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B10%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B11%5D%5Bdata%5D=11&columns%5B11%5D%5Bname%5D=&columns%5B11%5D%5Bsearchable%5D=true&columns%5B11%5D%5Borderable%5D=true&columns%5B11%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B11%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=0&order%5B0%5D%5Bdir%5D=asc&start=0&length=10000&search%5Bvalue%5D=&search%5Bregex%5D=false&_=1746727676517"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        }
        
        response = session.get(url_api, headers=headers, timeout=30)
        response.raise_for_status()
        
        dados = response.json()
        return dados
        
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao buscar dados da API: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Erro ao decodificar JSON: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache de 1 hora
def carregar_dados_reais(username: str, password: str):
    """
    Carrega dados usando requests (sem Selenium)
    """
    try:
        # Criar sessão com retry
        session = criar_sessao_com_retry()
        
        # Fazer login
        sucesso, mensagem = fazer_login(session, username, password)
        
        if not sucesso:
            if "inválidos" in mensagem.lower():
                return "LOGIN_INVALIDO"
            else:
                st.error(mensagem)
                return None
        
        # Buscar dados da API
        dados = buscar_dados_api(session)
        
        if dados is None:
            return None
            
        return dados
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

def processar_dados(dados):
    if not dados or "data" not in dados:
        return pd.DataFrame()

    df = pd.DataFrame(dados["data"])
    df.columns = [
        "DT_RowId", "Unidade", "Especialidade", "Profissional", "Serviço",
        "Origem", "Tipo", "Hora", "Agenda direta", "Data",
        "Data_Cadastro", "Profissional do Cadastro", "Tipo de Serviço", "Obs"
    ]
    df = df.drop(columns=["DT_RowId"])
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
    df["Hora"] = pd.to_datetime(df["Hora"], format='%H:%M', errors='coerce').dt.time
    df = df.dropna(subset=["Data"])
    return df

def testar_conexao():
    """Testa se o site está acessível"""
    try:
        response = requests.get("https://itabira-mg.vivver.com", timeout=10)
        if response.status_code == 200:
            return "success", "✅ Site Vivver está acessível!"
        else:
            return "warning", f"⚠️ Site respondeu com status {response.status_code}"
    except Exception as e:
        return "error", f"❌ Falha na conexão: {str(e)}"

def gerar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Agendas')
        writer.close()
    return output.getvalue()

def mostrar_calendario_mensal(df, origem_selecionada='Todos'):
    try:
        if origem_selecionada != 'Todos':
            df = df[df['Origem'] == origem_selecionada]

        df = df.sort_values('Data')
        datas_unicas = df['Data'].dt.date.unique()

        hoje = datetime.now().date()
        hora_atual = datetime.now().time()

        proximos_dias = []
        for data in sorted(datas_unicas):
            if data > hoje:
                proximos_dias.append(data)
            elif data == hoje:
                df_dia = df[df['Data'].dt.date == data]
                df_dia = df_dia[df_dia['Hora'] >= hora_atual]
                if len(df_dia) > 0:
                    proximos_dias.append(data)

        proximos_dias = proximos_dias[:15]

        st.subheader("Próximas Vagas Disponíveis (15 dias)")

        meses_para_mostrar = set()
        for data in proximos_dias:
            meses_para_mostrar.add((data.month, data.year))

        for mes, ano in sorted(meses_para_mostrar):
            st.markdown(f"### {MESES_PT_BR[mes]} {ano}")

            df_mes = df[(df['Data'].dt.month == mes) & (df['Data'].dt.year == ano)]
            dias_com_vagas = [d.day for d in proximos_dias if d.month == mes and d.year == ano]

            cal = calendar.Calendar(firstweekday=6)
            dias_mes = cal.monthdays2calendar(ano, mes)

            cols = st.columns(7)
            dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
            for i, dia in enumerate(dias_semana):
                cols[i].markdown(f"<div class='weekday-header'>{dia}</div>", unsafe_allow_html=True)

            for semana in dias_mes:
                cols = st.columns(7)
                for i, (dia, _) in enumerate(semana):
                    with cols[i]:
                        data_atual = datetime(ano, mes, dia).date() if dia != 0 else None

                        if dia == 0:
                            st.write("")
                        else:
                            if data_atual in proximos_dias:
                                df_dia = df_mes[df_mes['Data'].dt.date == data_atual]

                                if data_atual == hoje:
                                    df_dia = df_dia[df_dia['Hora'] >= hora_atual]

                                ppi_count = df_dia['Serviço'].str.contains('PPI', case=False, na=False).sum()
                                cmce_count = df_dia['Serviço'].str.contains('CMCE', case=False, na=False).sum()
                                oncologia_count = df_dia['Serviço'].str.contains('ONCOLOGIA', case=False, na=False).sum()
                                glaucoma_count = df_dia['Serviço'].str.contains('GLAUCOMA', case=False, na=False).sum()

                                tem_servicos_especificos = ppi_count > 0 or cmce_count > 0 or oncologia_count > 0 or glaucoma_count > 0

                                if tem_servicos_especificos:
                                    bg_color = "#002060"
                                    text_color = "#ffffff"
                                    border_color = "#002060"
                                else:
                                    bg_color = "#002060"
                                    text_color = "#002060"
                                    border_color = "#002060"

                                border_width = "2px" if data_atual == hoje else "1px"
                                border_color = "#2196F3" if data_atual == hoje else border_color
                                selected_class = "selected-day" if 'selected_date' in st.session_state and st.session_state.selected_date == data_atual else ""

                                servicos_html = ""
                                if tem_servicos_especificos:
                                    if ppi_count > 0:
                                        servicos_html += f"<div style='color: #FFFFFF; font-size: 0.9em;'>PPI: {ppi_count}</div>"
                                    if cmce_count > 0:
                                        servicos_html += f"<div style='color: #FFFFFF; font-size: 0.9em;'>CMCE: {cmce_count}</div>"
                                    if oncologia_count > 0:
                                        servicos_html += f"<div style='color: #FFFFFF; font-size: 0.9em;'>ONCO: {oncologia_count}</div>"
                                    if glaucoma_count > 0:
                                        servicos_html += f"<div style='color: #FFFFFF; font-size: 0.9em;'>GLAU: {glaucoma_count}</div>"

                                day_html = f"""
                                <div class='day-container'>
                                    <div class='calendar-day {selected_class}'
                                        style='border: {border_width} solid {border_color};
                                        border-radius: 5px; padding: 8px; min-height: 80px; margin: 2px;
                                        background-color: {bg_color}; color: {text_color}'>
                                        <div style='font-weight: bold; font-size: 1.1em;'>{dia}</div>
                                """

                                if servicos_html:
                                    day_html += servicos_html
                                elif not tem_servicos_especificos and data_atual >= hoje:
                                    day_html += "<div style='font-size: 0.7em;'>SEM SERVIÇOS</div>"

                                day_html += """
                                    </div>
                                </div>
                                """

                                st.markdown(day_html, unsafe_allow_html=True)

                                # Botão invisível para seleção
                                if st.button("", key=f"day_{dia}_{mes}_{ano}"):
                                    st.session_state.selected_date = data_atual
                                    st.rerun()
                            else:
                                st.write(f"<div style='text-align: center; color: #999;'>{dia}</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao gerar calendário: {str(e)}")

# ============================================================
# --- TELA DE LOGIN ---
# ============================================================
def tela_login():
    """Exibe a tela de login e armazena as credenciais na sessão."""
    st.markdown("""
    <div style='text-align:center; margin-top: 60px;'>
        <div style='font-size:2.2em; font-weight:bold; color:#002060;'>🗕️ Agenda de Consultas</div>
        <div style='font-size:1em; color:#555; margin-top:6px; margin-bottom:30px;'>
            Sistema de Acompanhamento de Vagas
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("#### 🔐 Acesso ao sistema")
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário", key="input_usuario")
        senha = st.text_input("Senha", placeholder="Digite sua senha", type="password", key="input_senha")

        if st.button("Entrar", use_container_width=True, type="primary"):
            if not usuario or not senha:
                st.error("Preencha o usuário e a senha.")
            else:
                # Salva as credenciais na sessão e marca como autenticado
                st.session_state["vivver_user"] = usuario
                st.session_state["vivver_pass"] = senha
                st.session_state["autenticado"] = True
                st.rerun()

        st.markdown("""
        <div style='font-size:0.8em; color:#999; text-align:center; margin-top:16px;'>
            As credenciais são usadas apenas para acessar o Vivver<br>e não são armazenadas permanentemente.
        </div>
        """, unsafe_allow_html=True)

# --- FUNÇÃO PRINCIPAL ---
def main():
    st.title("📅 Acompanhamento de Vagas")

    # Botão de logout na sidebar
    if st.sidebar.button("🚪 Sair (Logout)"):
        for key in ["autenticado", "vivver_user", "vivver_pass", "selected_date"]:
            st.session_state.pop(key, None)
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown(f"👤 Usuário: **{st.session_state.get('vivver_user', '')}**")

    with st.sidebar.expander("🔧 Diagnóstico do Sistema", expanded=False):
        if st.button("🧪 Testar Conexão com Vivver"):
            with st.spinner("Testando conexão..."):
                status, mensagem = testar_conexao()
                st.markdown(f"""
                <div class='connection-test connection-{status}'>
                    {mensagem}
                </div>
                """, unsafe_allow_html=True)

    if st.sidebar.button("🔄 Recarregar dados"):
        st.cache_data.clear()
        st.session_state.selected_date = None
        st.rerun()

    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None

    # Carregar dados usando as credenciais da sessão
    with st.spinner("Carregando dados do Vivver..."):
        try:
            dados = carregar_dados_reais(
                st.session_state["vivver_user"],
                st.session_state["vivver_pass"]
            )

            # Credenciais inválidas detectadas
            if dados == "LOGIN_INVALIDO":
                st.error("❌ Usuário ou senha inválidos no Vivver. Faça login novamente.")
                for key in ["autenticado", "vivver_user", "vivver_pass"]:
                    st.session_state.pop(key, None)
                st.rerun()

            if dados is None:
                st.error("❌ Falha ao carregar dados. Verifique sua conexão.")
                st.stop()

            df = processar_dados(dados)
        except Exception as e:
            st.error(f"Falha crítica ao carregar dados: {str(e)}")
            st.stop()

    if df.empty:
        st.warning("Nenhum dado foi carregado. Verifique a conexão ou as credenciais.")
        return

    # Filtros
    st.sidebar.header("Filtros")

    data_atual = datetime.now()
    ano_atual = data_atual.year
    mes_atual = data_atual.month

    anos_disponiveis = sorted(df['Data'].dt.year.unique(), reverse=True)
    if ano_atual not in anos_disponiveis:
        anos_disponiveis.insert(0, ano_atual)

    ano = st.sidebar.selectbox("Selecione o ano", anos_disponiveis, index=anos_disponiveis.index(ano_atual) if ano_atual in anos_disponiveis else 0)
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    mes_nome = st.sidebar.selectbox("Selecione o mês", list(meses.values()), index=mes_atual - 1)
    mes = list(meses.keys())[list(meses.values()).index(mes_nome)]

    origens_disponiveis = ['Todos'] + sorted(df['Origem'].dropna().unique().tolist())
    origem_selecionada = st.sidebar.selectbox("Filtrar por Origem", origens_disponiveis)

    if origem_selecionada != 'Todos':
        st.markdown(f"""
        <div class='filter-active'>
            <strong>Filtro Ativo:</strong> Mostrando apenas agendamentos da origem <strong>{origem_selecionada}</strong>
        </div>
        """, unsafe_allow_html=True)

    mostrar_calendario_mensal(df, origem_selecionada)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Resumo de Vagas**")

    if st.session_state.selected_date:
        df_filtrado = df[df['Data'].dt.date == st.session_state.selected_date]
        if st.session_state.selected_date == datetime.now().date():
            hora_atual = datetime.now().time()
            df_filtrado = df_filtrado[df_filtrado['Hora'] >= hora_atual]
        periodo = f"no dia {st.session_state.selected_date.strftime('%d/%m/%Y')}"
    else:
        df_filtrado = df[(df['Data'].dt.month == mes) & (df['Data'].dt.year == ano)]
        periodo = f"em {mes_nome} {ano}"

    if origem_selecionada != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Origem'] == origem_selecionada]
        periodo += f" (Origem: {origem_selecionada})"

    servicos_interesse = ['PPI', 'CMCE', 'ONCOLOGIA', 'GLAUCOMA']
    df_filtrado_servicos = df_filtrado[df_filtrado['Serviço'].str.contains('|'.join(servicos_interesse), case=False, na=False)]

    st.sidebar.metric(label=f"Vagas PPI {periodo}", value=len(df_filtrado[df_filtrado['Serviço'].str.contains('PPI', case=False, na=False)]))
    st.sidebar.metric(label=f"Vagas CMCE {periodo}", value=len(df_filtrado[df_filtrado['Serviço'].str.contains('CMCE', case=False, na=False)]))
    st.sidebar.metric(label=f"Vagas ONCO {periodo}", value=len(df_filtrado[df_filtrado['Serviço'].str.contains('ONCOLOGIA', case=False, na=False)]))
    st.sidebar.metric(label=f"Vagas GLAU {periodo}", value=len(df_filtrado[df_filtrado['Serviço'].str.contains('GLAUCOMA', case=False, na=False)]))
    st.sidebar.markdown("---")

    if not df_filtrado_servicos.empty:
        st.markdown(f"### 📋 Vagas {periodo}")
        if st.session_state.selected_date and st.button("📅 Mostrar todos os agendamentos do mês"):
            st.session_state.selected_date = None
            st.rerun()

        st.dataframe(
            df_filtrado_servicos.sort_values(['Data', 'Hora']),
            column_config={
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Hora": st.column_config.TimeColumn("Hora", format="HH:mm")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"Nenhuma consulta dos serviços selecionados agendada {periodo}.")

    st.sidebar.markdown(
        """
        <div style="text-align: right; font-size: 0.9em; color: #777; margin-top: 20px;">
            Desenvolvido por<br>
            <strong>Vinicius Viana</strong><br>
            <strong>V26.04.30</strong>
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# --- PONTO DE ENTRADA ---
# ============================================================
if __name__ == "__main__":
    if not st.session_state.get("autenticado", False):
        tela_login()
    else:
        main()

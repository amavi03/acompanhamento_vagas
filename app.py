import streamlit as st
import pandas as pd
from streamlit_calendar import calendar

# -----------------------------------
# CONFIG
# -----------------------------------
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/127RFRNh2YtDF0m9jTEjrP6PC6QZ-skvFvm96KgIUEbA/export?format=csv"

st.set_page_config(
    page_title="Acompanhamento de Vagas",
    layout="wide"
)

st.title("📅 Acompanhamento de Vagas")


# -----------------------------------
# CARREGAR DADOS
# -----------------------------------
@st.cache_data(ttl=60)
def carregar_dados():
    return pd.read_csv(URL_PLANILHA)


try:
    df = carregar_dados()

    df["data agenda"] = pd.to_datetime(
        df["data agenda"],
        dayfirst=True,
        errors="coerce"
    )

    df["quantidade"] = pd.to_numeric(
        df["quantidade"],
        errors="coerce"
    ).fillna(0)

    # -----------------------------------
    # FILTROS
    # -----------------------------------
    st.sidebar.header("Filtros")

    filtro_prestador = st.sidebar.selectbox(
        "Prestador",
        ["Todos"] + sorted(df["prestador"].dropna().unique())
    )

    filtro_especialidade = st.sidebar.selectbox(
        "Especialidade",
        ["Todas"] + sorted(df["especialidade"].dropna().unique())
    )

    filtro_profissional = st.sidebar.selectbox(
        "Profissional",
        ["Todos"] + sorted(df["profissional"].dropna().unique())
    )

    filtro_procedimento = st.sidebar.selectbox(
        "Tipo de procedimento",
        ["Todos"] + sorted(df["tipo de procedimento"].dropna().unique())
    )

    df_filtrado = df.copy()

    if filtro_prestador != "Todos":
        df_filtrado = df_filtrado[df_filtrado["prestador"] == filtro_prestador]

    if filtro_especialidade != "Todas":
        df_filtrado = df_filtrado[df_filtrado["especialidade"] == filtro_especialidade]

    if filtro_profissional != "Todos":
        df_filtrado = df_filtrado[df_filtrado["profissional"] == filtro_profissional]

    if filtro_procedimento != "Todos":
        df_filtrado = df_filtrado[df_filtrado["tipo de procedimento"] == filtro_procedimento]

    # -----------------------------------
    # DASHBOARD
    # -----------------------------------
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total vagas", int(df_filtrado["quantidade"].sum()))
    col2.metric("Total agendas", len(df_filtrado))
    col3.metric("Prestadores", df_filtrado["prestador"].nunique())
    col4.metric("Especialidades", df_filtrado["especialidade"].nunique())

   # -----------------------------------
# CALENDÁRIO (HOJE + 15 DIAS)
# -----------------------------------
    hoje = pd.Timestamp.today().normalize()
    limite = hoje + pd.Timedelta(days=15)

    # filtra apenas período desejado
    df_calendario = df_filtrado[
        (df_filtrado["data agenda"] >= hoje) &
        (df_filtrado["data agenda"] <= limite)
    ]

    resumo = (
        df_calendario.groupby("data agenda")["quantidade"]
        .sum()
        .reset_index()
    )

    eventos = []

    for _, row in resumo.iterrows():
        eventos.append({
            "title": f"{int(row['quantidade'])} vagas",
            "start": row["data agenda"].strftime("%Y-%m-%d"),
            "allDay": True
    })

    calendar_options = {
        "initialView": "dayGridMonth",
        "locale": "pt-br",
        "height": 650,

        # impede navegação para datas antigas
        "validRange": {
            "start": hoje.strftime("%Y-%m-%d"),
            "end": limite.strftime("%Y-%m-%d")
        }
    }

    st.subheader(
        f"Calendário de vagas ({hoje.strftime('%d/%m')} até {limite.strftime('%d/%m')})"
    )

    calendar_result = calendar(
        events=eventos,
        options=calendar_options,
        key="calendario_vagas"
    )

    # DEBUG → veja o retorno real
    # st.write(calendar_result)

    # -----------------------------------
    # CAPTURA CLIQUE
    # -----------------------------------
    if "data_clicada" not in st.session_state:
        st.session_state.data_clicada = None

    if calendar_result:

        # clique no evento "X vagas"
        if "eventClick" in calendar_result:
            event_data = calendar_result["eventClick"]

            if isinstance(event_data, dict):

                if "event" in event_data:
                    st.session_state.data_clicada = event_data["event"]["start"]

                elif "start" in event_data:
                    st.session_state.data_clicada = event_data["start"]

        # clique no dia vazio
        elif "dateClick" in calendar_result:
            date_data = calendar_result["dateClick"]

            if isinstance(date_data, dict):
                st.session_state.data_clicada = date_data.get("date")

    # -----------------------------------
    # DETALHES
    # -----------------------------------
    if st.session_state.data_clicada:

        data_selecionada = pd.to_datetime(
            st.session_state.data_clicada
        ).date()

        st.subheader(
            f"📌 Detalhes das vagas - {pd.to_datetime(data_selecionada).strftime('%d/%m/%Y')}"
        )

        detalhes = df_filtrado[
            df_filtrado["data agenda"].dt.date == data_selecionada
        ]

        if not detalhes.empty:
            detalhes = detalhes.sort_values("hora agenda")

            st.dataframe(
                detalhes[
                    [
                        "prestador",
                        "profissional",
                        "especialidade",
                        "hora agenda",
                        "quantidade",
                        "tipo de procedimento"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Nenhuma vaga encontrada para esta data.")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")

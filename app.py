import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
from investimentos import PortfolioManager

# Configuração da Página
st.set_page_config(
    page_title="Terminal de Inteligência Pessoal",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Gerenciador de Portfólio
pm = PortfolioManager()

# Estilização CSS Customizada
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --bg-color: #0E1117;
        --card-bg: #1A1C23;
        --accent-color: #00FFA3;
        --text-color: #E0E0E0;
    }

    .main { background-color: var(--bg-color); color: var(--text-color); font-family: 'Inter', sans-serif; }
    .metric-card {
        background: var(--card-bg); border: 1px solid #30363D; border-radius: 8px;
        padding: 12px; text-align: left; box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .research-item { background: #1A1C23; border-radius: 6px; border: 1px solid #30363D; padding: 8px 12px; margin-bottom: 4px; }
    .status-badge { padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 700; background: rgba(0, 255, 163, 0.1); color: #00FFA3; border: 1px solid rgba(0, 255, 163, 0.3); }
    
    h1 { font-size: 1.2rem !important; margin-bottom: 0 !important; }
    h2 { font-size: 1rem !important; margin-top: 10px !important; }
    h3 { font-size: 0.9rem !important; }
    [data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# Funções de Dados
@st.cache_data(ttl=300)
def fetch_finance_data(tickers_dict):
    data = {}
    for name, ticker in tickers_dict.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if not hist.empty and len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = ((current_price - prev_price) / prev_price) * 100
                data[name] = {"price": current_price, "change": change}
            else:
                data[name] = {"price": 0.0, "change": 0.0}
        except:
            data[name] = {"price": 0.0, "change": 0.0}
    return data

# Navegação Lateral
with st.sidebar:
    st.title("🤖 Terminal")
    page = st.radio("Navegação", ["📊 Dashboard", "💰 Carteira Fictícia", "⚙️ Configurações"])
    
    st.divider()
    summary = pm.get_portfolio_summary()
    
    if page == "💰 Carteira Fictícia":
        st.subheader("⚙️ Parâmetros de Aporte")
        aporte_base = st.number_input("Aporte Semanal (R$)", min_value=100, max_value=5000, value=250, step=50)
        
        st.info(f"🏦 Reserva de Oportunidade: R$ {summary['reserve']:,.2f}")
        
        novos_divs = pm.update_dividends()
        if novos_divs > 0:
            st.toast(f"💰 Novos proventos recebidos: R$ {novos_divs:.2f}!", icon="✨")
    
    st.divider()
    if page == "📊 Dashboard":
        st.info("Monitoramento Global")
    elif page == "💰 Carteira Fictícia":
        st.success(f"Gestão Ativa: R$ {aporte_base:.2f}/sem")

if page == "📊 Dashboard":
    MARKET_TICKERS = {"USD/BRL": "USDBRL=X", "Brent": "BZ=F", "IBOV": "^BVSP", "BTC": "BTC-USD"}
    FII_TICKERS = {"GARE11": "GARE11.SA", "MXRF11": "MXRF11.SA", "RURA11": "RURA11.SA", "VGIA11": "VGIA11.SA", "XPSF11": "XPSF11.SA"}
    st.title("⚡ DASHBOARD")
    st.caption(f"Sincronizado: {datetime.now().strftime('%H:%M:%S')}")
    finance_data = fetch_finance_data(MARKET_TICKERS)
    cols = st.columns(4)
    for i, (name, info) in enumerate(finance_data.items()):
        with cols[i % 4]:
            color = "#00FFA3" if info['change'] >= 0 else "#FF4B4B"
            st.markdown(f'<div class="metric-card"><p style="font-size: 0.65rem; color: #8B949E; margin: 0;">{name}</p><h3 style="margin: 0; color: white;">{info["price"]:,.2f}</h3><p style="color: {color}; font-size: 0.7rem; margin: 0;">{info["change"]:+.2f}%</p></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    fii_data = fetch_finance_data(FII_TICKERS)
    fii_cols = st.columns(5)
    for i, (name, info) in enumerate(fii_data.items()):
        with fii_cols[i % 5]:
            color = "#00FFA3" if info['change'] >= 0 else "#FF4B4B"
            st.markdown(f'<div class="metric-card" style="border-left: 2px solid #7928CA;"><p style="font-size: 0.65rem; color: #8B949E; margin: 0;">{name}</p><h3 style="margin: 0; color: white; font-size: 0.85rem;">R$ {info["price"]:,.2f}</h3><p style="color: {color}; font-size: 0.6rem; margin: 0;">{info["change"]:+.2f}%</p></div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("🧪 Pesquisas Clínicas")
    research_data = [
        {"titulo": "Vacina mRNA-4157", "fase": "Fase 3", "prog": 85, "status": "Redução 44% recorrência"},
        {"titulo": "Anti-PD-1 Combo", "fase": "Fase 2", "prog": 60, "status": "Eficácia em tumores sólidos"},
        {"titulo": "CAR-T Cell v2", "fase": "Fase 1", "prog": 30, "status": "Primeiros testes em humanos"}
    ]
    for res in research_data:
        st.markdown(f"""
            <div class="research-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-weight: 600; font-size: 0.85rem; color: white;">{res['titulo']}</span>
                        <br><span style="font-size: 0.7rem; color: #8B949E;">{res['status']}</span>
                    </div>
                    <div style="text-align: right;">
                        <span class="status-badge">{res['fase']}</span>
                        <div style="font-size: 0.75rem; color: #00FFA3; font-weight: bold; margin-top: 2px;">{res['prog']}%</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

elif page == "💰 Carteira Fictícia":
    st.title("📈 Carteira de Longo Prazo")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Patrimônio Total", f"R$ {summary['total_value']:,.2f}")
    col2.metric("Rentabilidade", f"{summary['profit_perc']:+.2f}%", f"R$ {summary['profit']:,.2f}")
    col3.metric("Proventos Acum.", f"R$ {summary['dividends']:,.2f}")
    
    with col4:
        total_proximo = aporte_base + summary['dividends']
        if st.button(f"🚀 Realizar Aporte"):
            with st.spinner("Analisando mercado..."):
                result = pm.perform_weekly_investment(aporte_base)
                if result['status'] == 'success':
                    st.balloons(); st.success("Aporte realizado!"); st.session_state['last_report'] = result['data']['rationale']; st.rerun()
                elif result['status'] == 'wait': st.warning(result['message'])
                else: st.error(result['message'])

    if 'last_report' in st.session_state:
        st.markdown("---"); st.markdown(st.session_state['last_report']); st.markdown("---")

    if summary['holdings']:
        df = pd.DataFrame(summary['holdings'])
        st.subheader("📋 Seus Ativos")
        df_display = df.copy()
        df_display['Valor'] = df['value'].apply(lambda x: f"R$ {x:,.2f}")
        df_display['Rent.'] = df['profit_perc'].apply(lambda x: f"{x:+.2f}%")
        st.dataframe(df_display[['ticker', 'sector', 'qty', 'Valor', 'Rent.']], use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("Alocação por Setor")
            fig = go.Figure(data=[go.Pie(labels=df['sector'], values=df['value'], hole=.3)])
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.write("Desempenho vs IBOVESPA (Base 100)")
            vh = summary['valuation_history']
            if vh:
                vdf = pd.DataFrame(vh)
                vdf['Portfolio Norm'] = (vdf['portfolio_value'] / vdf['portfolio_value'].iloc[0]) * 100
                vdf['IBOV Norm'] = (vdf['ibov_value'] / vdf['ibov_value'].iloc[0]) * 100
                fig_bench = go.Figure()
                fig_bench.add_trace(go.Scatter(x=vdf['date'], y=vdf['Portfolio Norm'], name="Sua Carteira", line=dict(color='#00FFA3')))
                fig_bench.add_trace(go.Scatter(x=vdf['date'], y=vdf['IBOV Norm'], name="IBOVESPA", line=dict(color='#8B949E', dash='dash')))
                fig_bench.update_layout(margin=dict(t=20, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig_bench, use_container_width=True)
    else:
        st.info("Aguardando primeiro aporte...")

elif page == "⚙️ Configurações":
    st.title("⚙️ Definição de Metas")
    st.write("Ajuste sua alocação alvo ideal:")
    targets = summary['targets']
    s_p = st.slider("Ações (%)", 0, 100, int(targets['Ações']*100))
    f_p = st.slider("FIIs (%)", 0, 100, int(targets['FIIs']*100))
    st_p = 100 - s_p - f_p
    st.write(f"Estratégicos (Diferencial): **{st_p}%**")
    if st_p < 0: st.error("A soma de Ações e FIIs não pode exceder 100%!")
    elif st.button("Salvar Novas Metas"):
        pm.update_targets(s_p, f_p, st_p); st.success("Metas atualizadas!")
    
    st.divider()
    if st.button("Resetar Tudo"):
        if os.path.exists('portfolio_data.json'): os.remove('portfolio_data.json'); st.rerun()

st.markdown('<div style="text-align: center; color: #484F58; font-size: 0.7rem; margin-top: 50px;">PROTÓTIPO V4.0 | Inteligência de Elite | Antigravity</div>', unsafe_allow_html=True)

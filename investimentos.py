import pandas as pd
import yfinance as yf
import json
import os
from datetime import datetime
import base64
try:
    from github import Github
    import streamlit as st
except ImportError:
    Github = None
    st = None

class PortfolioManager:
    def __init__(self, data_file='portfolio_data.json', repo_name='vitoriaraangel1991/TERMINAL'):
        self.data_file = data_file
        self.repo_name = repo_name
        self.assets_config = {
            'Ações': {
                'TICKERS': ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBAS3.SA', 'ABEV3.SA', 'WEGE3.SA', 'EGIE3.SA', 'RENT3.SA'],
                'SECTORS': {
                    'PETR4.SA': 'Energia/Commodities', 'VALE3.SA': 'Mineração', 
                    'ITUB4.SA': 'Financeiro', 'BBAS3.SA': 'Financeiro',
                    'ABEV3.SA': 'Consumo', 'WEGE3.SA': 'Industrial',
                    'EGIE3.SA': 'Utilidade Pública', 'RENT3.SA': 'Logística'
                }
            },
            'FIIs': {
                'TICKERS': ['HGLG11.SA', 'MXRF11.SA', 'KNIP11.SA', 'KNCR11.SA', 'XPLG11.SA', 'VISC11.SA'],
                'SECTORS': {
                    'HGLG11.SA': 'Logístico', 'MXRF11.SA': 'Papel',
                    'KNIP11.SA': 'Papel', 'KNCR11.SA': 'Papel',
                    'XPLG11.SA': 'Logístico', 'VISC11.SA': 'Shoppings'
                }
            },
            'Estratégicos': {
                'TICKERS': ['IVVB11.SA', 'GOLD11.SA', 'BOVA11.SA', 'LFTS11.SA'],
                'SECTORS': {
                    'IVVB11.SA': 'Global', 'GOLD11.SA': 'Proteção',
                    'BOVA11.SA': 'Índice BR', 'LFTS11.SA': 'Renda Fixa/Caixa'
                }
            }
        }
        self.max_assets = {'Ações': 6, 'FIIs': 5, 'Estratégicos': 3}
        self.load_data()

    def load_data(self):
        defaults = {
            'holdings': {}, 'history': [], 'accumulated_dividends': 0.0,
            'opportunity_reserve': 0.0, 'last_dividend_update': datetime.now().strftime('%Y-%m-%d'),
            'target_allocation': {'Ações': 0.40, 'FIIs': 0.40, 'Estratégicos': 0.20},
            'valuation_history': []
        }
        
        # Tentar carregar do GitHub primeiro se estiver no Cloud
        if st and "GITHUB_TOKEN" in st.secrets:
            try:
                g = Github(st.secrets["GITHUB_TOKEN"])
                repo = g.get_repo(self.repo_name)
                contents = repo.get_contents(self.data_file)
                self.data = json.loads(contents.decoded_content.decode('utf-8'))
                # Salvar localmente para cache
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=4, ensure_ascii=False)
                return
            except:
                pass

        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            for key, value in defaults.items():
                if key not in self.data:
                    self.data[key] = value
        else:
            self.data = defaults
            self.save_data()

    def save_data(self):
        # Salvar local
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        
        # Sincronizar com GitHub se o Token existir
        if st and "GITHUB_TOKEN" in st.secrets:
            try:
                g = Github(st.secrets["GITHUB_TOKEN"])
                repo = g.get_repo(self.repo_name)
                contents = repo.get_contents(self.data_file)
                repo.update_file(
                    contents.path, 
                    f"Update portfolio: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                    json.dumps(self.data, indent=4, ensure_ascii=False), 
                    contents.sha
                )
            except Exception as e:
                st.error(f"Erro ao sincronizar com GitHub: {e}")

    def update_targets(self, stock_p, fii_p, strat_p):
        self.data['target_allocation'] = {'Ações': stock_p/100, 'FIIs': fii_p/100, 'Estratégicos': strat_p/100}
        self.save_data()

    def update_dividends(self):
        last_update = datetime.strptime(self.data.get('last_dividend_update', '2000-01-01'), '%Y-%m-%d')
        if (datetime.now() - last_update).days >= 30:
            summary = self.get_portfolio_summary()
            new_divs = summary['total_value'] * 0.006 
            if new_divs > 0:
                self.data['accumulated_dividends'] += new_divs
                self.data['last_dividend_update'] = datetime.now().strftime('%Y-%m-%d')
                self.data['history'].append({'date': datetime.now().strftime('%Y-%m-%d %H:%M'), 'ticker': "PROVENTOS", 'total': new_divs, 'rationale': "Dividendos mensais reinvestidos."})
                self.save_data()
                return new_divs
        return 0

    def get_market_data(self, tickers):
        data = {}
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="5d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    info = t.info
                    high_52 = info.get('fiftyTwoWeekHigh') or t.history(period="1y")['High'].max()
                    data[ticker] = {'price': current_price, 'high_52': high_52, 'discount': (current_price/high_52)-1}
            except: continue
        return data

    def perform_weekly_investment(self, base_amount=250.0):
        total_available = base_amount + self.data.get('accumulated_dividends', 0.0)
        self.data['accumulated_dividends'] = 0.0
        
        all_tickers = [t for cat in self.assets_config.values() for t in cat['TICKERS']] + ['^BVSP']
        market_data = self.get_market_data(all_tickers)
        current_holdings = self.data['holdings']
        
        total_value = sum(h['qty'] * market_data.get(t, {}).get('price', h['avg_price']) for t, h in current_holdings.items())
        cat_values = {cat: sum(h['qty'] * market_data.get(t, {}).get('price', h['avg_price']) for t, h in current_holdings.items() if h['type'] == cat) for cat in self.assets_config}
        
        targets = self.data.get('target_allocation', {'Ações': 0.4, 'FIIs': 0.4, 'Estratégicos': 0.2})
        if total_value == 0: chosen_cat = 'Ações'
        else:
            diffs = [(cat, targets[cat] - (cat_values[cat]/total_value)) for cat in self.assets_config]
            chosen_cat = sorted(diffs, key=lambda x: x[1], reverse=True)[0][0]
            
        potential = []
        for t in self.assets_config[chosen_cat]['TICKERS']:
            if t in market_data:
                is_new = t not in current_holdings
                if is_new and sum(1 for h in current_holdings.values() if h['type'] == chosen_cat) >= self.max_assets[chosen_cat]: continue
                score = market_data[t]['discount'] + (0.15 * sum(1 for h in current_holdings.keys() if self.get_asset_sector(h) == self.get_asset_sector(t))) + (-0.05 if not is_new else 0)
                potential.append((t, score, market_data[t]['price'], market_data[t]['discount']))
        
        potential.sort(key=lambda x: x[1])
        if potential and potential[0][3] > -0.05:
            self.data['opportunity_reserve'] += total_available
            self.save_data()
            return {"status": "wait", "message": f"Janela desfavorável em {chosen_cat}. R$ {total_available:.2f} enviados para Reserva."}

        use_reserve = False
        if potential and potential[0][3] < -0.15 and self.data['opportunity_reserve'] > 0:
            use_reserve = True; total_available += self.data['opportunity_reserve']; self.data['opportunity_reserve'] = 0
            
        top = potential[:2]
        amount_per = total_available / len(top)
        transactions = []
        for ticker, score, price, discount in top:
            qty = int(amount_per // price)
            if qty > 0:
                cost = qty * price
                if ticker not in self.data['holdings']: self.data['holdings'][ticker] = {'qty': 0, 'avg_price': 0.0, 'type': chosen_cat}
                h = self.data['holdings'][ticker]
                h['avg_price'] = ((h['qty'] * h['avg_price']) + cost) / (h['qty'] + qty)
                h['qty'] += qty
                transactions.append({'ticker': ticker, 'qty': qty, 'price': price, 'discount': discount})

        if not transactions: return {"status": "error", "message": "Saldo insuficiente."}

        rationale = f"### {'🔥 COMPRA AGRESSIVA' if use_reserve else '🎯 Aporte Focado'}: R$ {sum(t['qty']*t['price'] for t in transactions):.2f}\n"
        for t in transactions: rationale += f"- **{t['ticker']}**: {t['qty']} un. Desconto: **{t['discount']:.1%}**.\n"
        
        entry = {'date': datetime.now().strftime('%Y-%m-%d %H:%M'), 'ticker': f"Aporte {chosen_cat}", 'total': sum(t['qty']*t['price'] for t in transactions), 'rationale': rationale}
        self.data['history'].append(entry)
        self.data['valuation_history'].append({'date': datetime.now().strftime('%Y-%m-%d'), 'portfolio_value': total_value + entry['total'], 'ibov_value': market_data.get('^BVSP', {}).get('price', 0)})
        self.save_data()
        return {"status": "success", "data": entry}

    def get_asset_sector(self, ticker):
        for cat in self.assets_config.values():
            if ticker in cat['SECTORS']: return cat['SECTORS'][ticker]
        return "Geral"

    def get_portfolio_summary(self):
        all_t = list(self.data['holdings'].keys()) + ['^BVSP']
        m_data = self.get_market_data(all_t)
        holdings = []
        total_v = 0; total_c = 0
        for t, h in self.data['holdings'].items():
            p = m_data.get(t, {}).get('price', h['avg_price'])
            val = h['qty'] * p; cost = h['qty'] * h['avg_price']
            total_v += val; total_c += cost
            holdings.append({'ticker': t, 'qty': h['qty'], 'avg_price': h['avg_price'], 'current_price': p, 'value': val, 'type': h['type'], 'profit_perc': (val/cost-1)*100 if cost > 0 else 0, 'sector': self.get_asset_sector(t)})
        return {"total_value": total_v, "total_cost": total_c, "profit": total_v - total_c, "profit_perc": (total_v/total_c-1)*100 if total_c > 0 else 0, "holdings": holdings, "dividends": self.data.get('accumulated_dividends', 0), "reserve": self.data.get('opportunity_reserve', 0), "valuation_history": self.data.get('valuation_history', []), "targets": self.data.get('target_allocation', {'Ações': 0.4, 'FIIs': 0.4, 'Estratégicos': 0.2})}

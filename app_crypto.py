import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplcyberpunk
import requests
from matplotlib.ticker import FuncFormatter

# Configuração da página
st.set_page_config(page_title="Análise de Criptomoedas",
                   page_icon="📈", layout="centered")
plt.style.use("cyberpunk")

# Função para buscar e analisar dados


def obter_criptos():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": False
    }
    resposta = requests.get(url, params=params)
    if resposta.status_code == 200:
        return [f"{moeda['symbol'].upper()}-USD" for moeda in resposta.json()]
    else:
        st.error("Erro ao buscar criptomoedas.")
        return []


def analisar_cripto(ticker):
    dados = yf.download(ticker)
    dados["retorno"] = dados["Adj Close"].pct_change()
    dados_retornos_completos = dados["retorno"]
    dados["media_maximas"] = dados["High"].rolling(window=20).mean()
    dados["media_minimas"] = dados["Low"].rolling(window=20).mean()
    dados["sinal_compra"] = 0
    dados["sinal_venda"] = 0
    dados["sinal_compra"] = (
        dados["Close"] > dados["media_maximas"]).astype(int)
    dados["sinal_venda"] = (
        dados["Close"] < dados["media_minimas"]).astype(int)

    dados["posicao"] = 0

    for i in range(1, len(dados)):
        if dados['sinal_compra'].iloc[i] == 1:
            dados["posicao"].iloc[i] = 1
        elif dados['sinal_venda'].iloc[i] == 1:
            dados["posicao"].iloc[i] = 0
        else:
            if (dados['posicao'].iloc[i-1] == 1) and (dados['sinal_venda'].iloc[i] == 0):
                dados["posicao"].iloc[i] = 1
            else:
                dados["posicao"].iloc[i] = 0

    dados["posicao"] = dados["posicao"].shift()
    dados['trades'] = (dados['posicao'] != dados['posicao'].shift()).cumsum()
    dados['trades'] = dados['trades'].where(dados['posicao'] == 1)
    dados = dados.dropna(subset=["trades"])

    df_retorno_acumulado = (1 + dados["retorno"]).cumprod() - 1

    dados_retornos_completos_acum = (
        1 + dados_retornos_completos).cumprod() - 1
    print(df_retorno_acumulado.iloc[-1],
          dados_retornos_completos_acum.iloc[-1])

    dados['acao'] = np.where(dados['posicao'] == 1, 'Compra', np.where(
        dados['sinal_venda'] == 1, 'Venda', 'Neutra'))

    return dados, df_retorno_acumulado, dados_retornos_completos_acum


# Interface do Streamlit
st.title("Análise de Criptomoedas")
cripto_opcoes = obter_criptos()
cripto_escolhida = st.selectbox("Selecione a criptomoeda:", cripto_opcoes)

dados, df_retorno_acumulado, dados_retornos_completos_acum = analisar_cripto(
    cripto_escolhida)

st.subheader(f"Resultados para {cripto_escolhida}")
fig, ax = plt.subplots(figsize=(12, 6))
dados_retornos_completos_acum.plot(label="Ativo", ax=ax)
df_retorno_acumulado.plot(label="Modelo", ax=ax)
ax.legend()
ax.set_title(f"Retorno Acumulado - {cripto_escolhida}")
st.pyplot(fig)

fig2, ax2 = plt.subplots(figsize=(12, 6))
ax2.plot(dados.index, dados['Close'],
         label='Preço de Fechamento', color='cyan')
ax2.scatter(dados.index[dados['sinal_compra'] == 1], dados['Close']
            [dados['sinal_compra'] == 1], color='green', label='Compra', marker='^', s=100)
ax2.scatter(dados.index[dados['sinal_venda'] == 1], dados['Close']
            [dados['sinal_venda'] == 1], color='red', label='Venda', marker='v', s=100)
ax2.set_title(f"Pontos de Entrada e Saída - {cripto_escolhida}")
ax2.legend()
st.pyplot(fig2)

st.dataframe(dados.tail())

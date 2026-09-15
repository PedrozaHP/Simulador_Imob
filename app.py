import streamlit as st
import pandas as pd
import io

# 1. Configuração da página
st.set_page_config(page_title="Simulador Imobiliário Profissional", layout="centered")

# ==========================================
# 2. SISTEMA DE LOGIN E SEGURANÇA POR E-MAIL
# ==========================================
# Sua base de dados de clientes licenciados
CLIENTES_AUTORIZADOS = {
    "seu_email@teste.com": {
        "nome": "João Silva - CRECI 12345-SP",
        "telefone": "(11) 99999-9999"
    },
    "cobaia@imoveis.com": {
        "nome": "Carlos Corretor - CRECI 54321-SP",
        "telefone": "(11) 98888-8888"
    }
}

st.title("🔒 Simulador Imobiliário Profissional")

# Controlando o estado de login na sessão
if "email_logado" not in st.session_state:
    st.session_state.email_logado = None

# Se não estiver logado, mostra a tela de bloqueio
if not st.session_state.email_logado:
    st.info("💡 Área restrita para corretores licenciados. Insira seu e-mail cadastrado para acessar a ferramenta.")
    email_input = st.text_input("Seu E-mail de Acesso:")
    
    if st.button("🔓 Entrar na Ferramenta"):
        if email_input in CLIENTES_AUTORIZADOS:
            st.session_state.email_logado = email_input
            st.rerun()
        else:
            st.error("❌ E-mail não encontrado ou licença inativa. Entre em contato para adquirir seu acesso.")
    st.stop() # Para a execução aqui se não estiver logado!

# ==========================================
# 3. ÁREA LOGADA (Usuário Autenticado)
# ==========================================
# Puxa automaticamente os dados travados do corretor (ele não consegue alterar)
dados_usuario = CLIENTES_AUTORIZADOS[st.session_state.email_logado]
nome_corretor = dados_usuario["nome"]
telefone = dados_usuario["telefone"]

# Barra lateral com dados da conta e botão de sair
st.sidebar.success(f"Logado como:\n**{nome_corretor}**")
if st.sidebar.button("Sair / Trocar Conta"):
    st.session_state.email_logado = None
    st.rerun()

st.markdown("---")
st.write("Gere simulações de financiamento (Tabela SAC) personalizadas e profissionais com a sua marca.")

# ==========================================
# 4. DADOS DA NEGOCIAÇÃO
# ==========================================
st.subheader("Dados da Negociação")
col1, col2 = st.columns(2)
with col1:
    valor_imovel = st.number_input("Valor do Imóvel (R$)", value=500000.0, step=10000.0)
    taxa_juros = st.number_input("Taxa de Juros Anual (%)", value=9.5, step=0.1)
with col2:
    entrada = st.number_input("Valor da Entrada (R$)", value=100000.0, step=10000.0)
    meses = st.number_input("Prazo (Meses)", value=360, step=12)

# ==========================================
# 5. PROCESSAMENTO E GERAÇÃO DO EXCEL
# ==========================================
if st.button("🚀 Gerar Simulação e Planilha Profissional"):
    valor_financiado = valor_imovel - entrada
    taxa_mensal = (taxa_juros / 100) / 12
    amortizacao = valor_financiado / meses
    saldo_devedor = valor_financiado
    
    # Calculando a tabela SAC
    dados = []
    for mes in range(1, meses + 1):
        juros = saldo_devedor * taxa_mensal
        prestacao = amortizacao + juros
        saldo_devedor -= amortizacao
        dados.append({
            "Mês": mes,
            "Prestação (R$)": round(prestacao, 2),
            "Amortização (R$)": round(amortizacao, 2),
            "Juros (R$)": round(juros, 2),
            "Saldo Devedor (R$)": round(max(saldo_devedor, 0), 2)
        })
        
    df_sac = pd.DataFrame(dados)
    
    st.success("✅ Simulação gerada com sucesso! Veja uma prévia abaixo:")
    st.dataframe(df_sac.head(5))
    
    # Criando o Excel com Design Profissional (XlsxWriter)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        cor_cabecalho = "#1F4E78" # Azul corporativo
        
        fmt_titulo = workbook.add_format({
            'bold': True, 'font_size': 14, 'font_color': '#1F4E78', 'bottom': 2, 'bottom_color': '#1F4E78'
        })
        fmt_cabecalho_tabela = workbook.add_format({
            'bold': True, 'font_color': 'white', 'bg_color': cor_cabecalho, 
            'align': 'center', 'valign': 'middle', 'border': 1
        })
        fmt_celula = workbook.add_format({
            'align': 'center', 'valign': 'middle', 'border': 1
        })
        fmt_moeda = workbook.add_format({
            'num_format': 'R$ #,##0.00', 'align': 'right', 'valign': 'middle', 'border': 1
        })
        fmt_destaque_chave = workbook.add_format({
            'bold': True, 'font_color': '#333333', 'bg_color': '#F2F2F2', 'border': 1, 'valign': 'middle'
        })
        fmt_destaque_valor = workbook.add_format({
            'bold': True, 'font_color': '#1F4E78', 'bg_color': '#F2F2F2', 'border': 1, 'align': 'right', 'valign': 'middle', 'num_format': 'R$ #,##0.00'
        })

        # --- ABA 1: RESUMO DA PROPOSTA ---
        ws_resumo = workbook.add_worksheet('Resumo da Proposta')
        ws_resumo.set_column('A:A', 28)
        ws_resumo.set_column('B:B', 32)
        
        ws_resumo.write('A1', 'PROPOSTA COMERCIAL & FLUXO', fmt_titulo)
        
        dados_resumo = [
            ("Corretor Responsável", nome_corretor),
            ("WhatsApp de Contato", telefone),
            ("Valor Total do Imóvel", valor_imovel),
            ("Valor da Entrada", entrada),
            ("Valor Financiado", valor_financiado),
            ("Prazo Total", f"{meses} Meses ({meses//12} Anos)"),
            ("Taxa de Juros Anual", f"{taxa_juros}% a.a.")
        ]
        
        linha = 3
        for item, valor in dados_resumo:
            ws_resumo.write(linha, 0, item, fmt_destaque_chave)
            if isinstance(valor, (int, float)):
                ws_resumo.write(linha, 1, valor, fmt_destaque_valor)
            else:
                ws_resumo.write(linha, 1, str(valor), fmt_destaque_chave)
            linha += 1

        # --- ABA 2: FLUXO DE PAGAMENTO SAC ---
        ws_sac = workbook.add_worksheet('Fluxo SAC')
        
        cabecalhos = ["Mês", "Prestação (R$)", "Amortização (R$)", "Juros (R$)", "Saldo Devedor (R$)"]
        for col_num, cabecalho in enumerate(cabecalhos):
            ws_sac.write(0, col_num, cabecalho, fmt_cabecalho_tabela)
            
        ws_sac.set_column('A:A', 10)
        ws_sac.set_column('B:E', 22)
        
        for row_idx, linha_dados in enumerate(dados, start=1):
            ws_sac.write(row_idx, 0, linha_dados["Mês"], fmt_celula)
            ws_sac.write(row_idx, 1, linha_dados["Prestação (R$)"], fmt_moeda)
            ws_sac.write(row_idx, 2, linha_dados["Amortização (R$)"], fmt_moeda)
            ws_sac.write(row_idx, 3, linha_dados["Juros (R$)" ], fmt_moeda)
            ws_sac.write(row_idx, 4, linha_dados["Saldo Devedor (R$)"], fmt_moeda)

    # Botão de Download
    st.download_button(
        label="📥 Baixar Planilha Profissional para o Cliente",
        data=buffer.getvalue(),
        file_name="Proposta_Imobiliaria_Profissional.xlsx",
        mime="application/vnd.ms-excel"
    )

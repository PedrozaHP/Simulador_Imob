import streamlit as st
import pandas as pd
import io

# 1. Configuração da página
st.set_page_config(page_title="Simulador Imobiliário Profissional", layout="wide")

# ==========================================
# 2. SISTEMA DE LOGIN VIA COFRE SEGURO (SECRETS)
# ==========================================
CLIENTES_AUTORIZADOS = st.secrets.get("CLIENTES_AUTORIZADOS", {})
SENHA_EXCEL = st.secrets.get("SENHA_EXCEL", "SenhaMestraProtecao123")

st.title("🏗️ Simulador Imobiliário Profissional")

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if not st.session_state.usuario_logado:
    st.info("💡 Área restrita para corretores licenciados. Insira seu Usuário cadastrado para acessar a ferramenta.")
    usuario_input = st.text_input("Seu Usuário de Acesso:")
    
    if st.button("🔓 Entrar na Ferramenta"):
        usuario_limpo = usuario_input.strip().lower()
        if usuario_limpo in CLIENTES_AUTORIZADOS:
            st.session_state.usuario_logado = usuario_limpo
            st.rerun()
        else:
            st.error("❌ Usuário não encontrado ou licença inativa.")
    st.stop()

# ==========================================
# 3. ÁREA LOGADA - DADOS ESTÁTICOS
# ==========================================
dados_usuario = CLIENTES_AUTORIZADOS[st.session_state.usuario_logado]

nome_corretor = dados_usuario.get("nome", "Não Informado")
telefone = dados_usuario.get("telefone", "Não Informado")
creci_corretor = dados_usuario.get("creci", "Não Informado")

st.sidebar.title("👤 Corretor Licenciado")
st.sidebar.markdown(f"""
**Nome:** {nome_corretor}  
**CRECI:** {creci_corretor}  
**Contato:** {telefone}
""")

if st.sidebar.button("Sair / Trocar Conta"):
    st.session_state.usuario_logado = None
    st.rerun()

st.markdown("---")

# ==========================================
# 4. DADOS DA NEGOCIAÇÃO E COMPOSIÇÃO
# ==========================================
st.subheader("🏗️ Dados do Imóvel e Composição de Pagamento")

sistema_amortizacao = st.radio(
    "Sistema de Amortização (Pós-Chaves / Financiamento):",
    ["Tabela SAC (Prestações Decrescentes)", "Tabela Price (Prestações Fixas)"],
    horizontal=True
)

col1, col2 = st.columns(2)
with col1:
    valor_imovel = st.number_input("Valor Total do Imóvel (R$)", value=230000.0, step=10000.0, format="%.2f")
    financiamento_base_input = st.number_input("Financiamento Bancário Aprovado (R$)", value=150000.0, step=10000.0, format="%.2f")
with col2:
    sinal_entrada = st.number_input("Valor do Ato / Sinal (R$)", value=15000.0, step=5000.0, format="%.2f")
    prazo_banco_meses = st.number_input("Prazo do Financiamento Bancário (Meses)", value=360, min_value=1, max_value=420, step=1)

taxa_juros = st.number_input("Taxa de Juros Anual do Financiamento (%)", value=9.5, step=0.1, format="%.2f")

# Condições Especiais da Planta
st.markdown("---")
st.subheader("💡 Condições Especiais da Planta")

# FGTS
col_fgts1, col_fgts2 = st.columns(2)
with col_fgts1:
    usar_fgts = st.checkbox("Cliente vai utilizar FGTS?")
with col_fgts2:
    valor_fgts = st.number_input("Valor do FGTS (R$)", value=15000.0, step=5000.0, format="%.2f", disabled=not usar_fgts)

fgts_efetivo = valor_fgts if usar_fgts else 0.0
destino_fgts = "Abater do Sinal / Entrada"
valor_financiado_banco = financiamento_base_input

if usar_fgts:
    destino_fgts = st.radio(
        "Como o FGTS será utilizado na composição?",
        ["Abater do Sinal / Entrada (Recursos Próprios)", "Somar ao Financiamento / Aumentar Crédito com o Banco"],
        horizontal=True
    )
    
    if "Somar ao Financiamento" in destino_fgts:
        valor_financiado_banco = financiamento_base_input + fgts_efetivo
        st.info(f"ℹ️ **Efeito do FGTS:** Somado ao crédito. Financiamento Bancário Efetivo ajustado para **R$ {valor_financiado_banco:,.2f}**.")
    else:
        st.info("ℹ️ **Efeito do FGTS:** Abatido do sinal/entrada, aliviando o bolso do cliente no ato.")

# Evolução de Obra & Banco
st.markdown("#### 🏦 Evolução de Obra (Estimativa Banco)")
col_obra1, col_obra2 = st.columns(2)
with col_obra1:
    incluir_obra = st.checkbox("Incluir Estimativa de Evolução de Obra?", value=True)
with col_obra2:
    meses_obra_duracao = st.number_input("Duração da Obra (Meses)", value=36, min_value=1, max_value=72, step=1, disabled=not incluir_obra)

# Parcelamento Construtora, Anuais e INCC
st.markdown("#### 🏢 Parcelamento Construtora, Anuais & INCC")
col_constr_opc1, col_constr_opc2 = st.columns(2)
with col_constr_opc1:
    usar_construtora = st.checkbox("Parcelar saldo restante direto com a Construtora?", value=True)
with col_constr_opc2:
    sincronizar_prazos = st.checkbox("Igualar prazo da Construtora ao prazo da Obra", value=True, disabled=not usar_construtora or not incluir_obra)

padrao_meses_construtora = meses_obra_duracao if (incluir_obra and sincronizar_prazos) else 36

col_c1, col_c2 = st.columns(2)
with col_c1:
    meses_construtora = st.number_input(
        "Prazo das Mensais Construtora (Meses)", 
        value=padrao_meses_construtora, 
        min_value=1, 
        max_value=120, 
        step=1, 
        disabled=not usar_construtora
    )
with col_c2:
    taxa_incc_estimada = st.number_input(
        "Estimativa de INCC Mensal (%)", 
        value=0.50, 
        step=0.05, 
        format="%.2f",
        disabled=not usar_construtora,
        help="Projeção média mensal do reajuste de INCC."
    )

# Configuração de Parcelas Anuais / Intermediárias
st.markdown("##### 📅 Parcelas Anuais / Intermediárias (Substituem a Mensal)")
col_an1, col_an2, col_an3 = st.columns(3)
with col_an1:
    usar_anuais = st.checkbox("Incluir Parcelas Anuais?", value=True, disabled=not usar_construtora)
with col_an2:
    max_anuais_possiveis = max(1, meses_construtora // 12)
    num_anuais = st.number_input("Qtd. de Anuais", value=min(3, max_anuais_possiveis), min_value=1, max_value=10, step=1, disabled=not usar_anuais or not usar_construtora)
with col_an3:
    valor_anual_unitaria = st.number_input("Valor de cada Anual (R$)", value=5000.0, step=1000.0, format="%.2f", disabled=not usar_anuais or not usar_construtora)

# CÁLCULO DA PARCELA MENSAL REDUZIDA
saldo_construtora = 0.0
prestacao_construtora_mensal = 0.0
total_anuais_val = 0.0

if usar_construtora:
    abatimento_entrada_fgts = fgts_efetivo if ("Abater do Sinal" in destino_fgts) else 0.0
    sinal_efetivo_calculo = sinal_entrada + abatimento_entrada_fgts
    
    saldo_construtora = valor_imovel - financiamento_base_input - sinal_efetivo_calculo
    if saldo_construtora < 0: saldo_construtora = 0.0
    
    if usar_anuais:
        total_anuais_val = num_anuais * valor_anual_unitaria
        if total_anuais_val > saldo_construtora:
            total_anuais_val = saldo_construtora
            st.warning("⚠️ O valor total das anuais ultrapassa o saldo com a construtora. Ajustado ao saldo limite.")
        
        saldo_para_mensais = saldo_construtora - total_anuais_val
        meses_mensais_efetivas = meses_construtora - num_anuais
        
        if meses_mensais_efetivas > 0:
            prestacao_construtora_mensal = saldo_para_mensais / meses_mensais_efetivas
        else:
            prestacao_construtora_mensal = 0.0
    else:
        prestacao_construtora_mensal = saldo_construtora / meses_construtora if meses_construtora > 0 else 0.0
    
    st.success(
        f"💡 **Saldo Construtora:** R$ {saldo_construtora:,.2f} | "
        f"**Mensal Padrão Reduzida:** R$ {prestacao_construtora_mensal:,.2f}/mês | "
        f"**Anuais (Substituem a mensal):** {num_anuais}x de R$ {valor_anual_unitaria:,.2f}" if usar_anuais else f"💡 **Saldo Construtora:** R$ {saldo_construtora:,.2f} | **Mensal Base:** R$ {prestacao_construtora_mensal:,.2f}/mês"
    )

# ==========================================
# 5. PROCESSAMENTO DA TABELA COMERCIAL
# ==========================================
st.markdown("---")
if st.button("🚀 Gerar Proposta Comercial Simplificada"):
    if valor_imovel <= 0 or prazo_banco_meses <= 0:
        st.warning("⚠️ Preencha os valores principais corretamente.")
    else:
        taxa_mensal_banco = (taxa_juros / 100) / 12
        taxa_incc_dec = taxa_incc_estimada / 100
        is_sac = "SAC" in sistema_amortizacao
        nome_sistema = "Tabela SAC" if is_sac else "Tabela Price"
        
        # ------------------------------------------
        # TABELA 1: FLUXO PRÉ-CHAVES SIMPLIFICADO
        # ------------------------------------------
        dados_pre_chaves = []
        prazo_loop = meses_obra_duracao if incluir_obra else meses_construtora
        
        for mes in range(1, prazo_loop + 1):
            # Identifica se é um mês de Parcela Anual
            eh_mes_anual = False
            if usar_construtora and usar_anuais:
                if (mes % 12 == 0) and ((mes // 12) <= num_anuais):
                    eh_mes_anual = True

            # Lógica de substituição: no mês anual, a mensal zera e entra a anual cheia
            if eh_mes_anual:
                parc_mensal_base = 0.0
                parc_anual_mes = valor_anual_unitaria
            else:
                parc_mensal_base = prestacao_construtora_mensal if (usar_construtora and mes <= meses_construtora) else 0.0
                parc_anual_mes = 0.0
            
            # Estimativa INCC sobre o valor do boleto da construtora naquele mês
            fator_incc = (1 + taxa_incc_dec) ** mes
            base_para_incc = parc_mensal_base + parc_anual_mes
            est_incc_mes = base_para_incc * (fator_incc - 1)
            
            # Estimativa Evolução de Obra (Banco)
            est_obra_mes = 0.0
            if incluir_obra:
                pct_avanco = mes / prazo_loop
                saldo_fin_corrigido = valor_financiado_banco * fator_incc
                est_obra_mes = (saldo_fin_corrigido * pct_avanco) * taxa_mensal_banco
            
            total_desembolso = parc_mensal_base + parc_anual_mes + est_incc_mes + est_obra_mes
            
            dados_pre_chaves.append({
                "Mês": mes,
                "Mensal Construtora (R$)": round(parc_mensal_base, 2),
                "Anual / Intermediária (R$)": round(parc_anual_mes, 2),
                "Est. INCC (R$)": round(est_incc_mes, 2),
                "Est. Obra Banco (R$)": round(est_obra_mes, 2),
                "Total Mês (R$)": round(total_desembolso, 2)
            })
        
        # ------------------------------------------
        # TABELA 2: PÓS-CHAVES (BANCO)
        # ------------------------------------------
        dados_banco = []
        if is_sac:
            amortizacao_base = valor_financiado_banco / prazo_banco_meses if prazo_banco_meses > 0 else 0
            for mes in range(1, prazo_banco_meses + 1):
                saldo_parcial = valor_financiado_banco - (amortizacao_base * (mes - 1))
                if saldo_parcial < 0: saldo_parcial = 0
                juros_banco = saldo_parcial * taxa_mensal_banco
                prestacao_total = amortizacao_base + juros_banco
                
                dados_banco.append({
                    "Mês Bancário": mes,
                    "Amortização (R$)": round(amortizacao_base, 2),
                    "Juros (R$)": round(juros_banco, 2),
                    "Parcela Total (R$)": round(prestacao_total, 2)
                })
        else: # Price
            if taxa_mensal_banco > 0 and prazo_banco_meses > 0:
                prestacao_price = valor_financiado_banco * (taxa_mensal_banco * (1 + taxa_mensal_banco)**prazo_banco_meses) / ((1 + taxa_mensal_banco)**prazo_banco_meses - 1)
            else:
                prestacao_price = valor_financiado_banco / prazo_banco_meses if prazo_banco_meses > 0 else 0
                
            saldo_atual = valor_financiado_banco
            for mes in range(1, prazo_banco_meses + 1):
                juros_banco = saldo_atual * taxa_mensal_banco
                amort_price = prestacao_price - juros_banco
                saldo_atual -= amort_price
                
                dados_banco.append({
                    "Mês Bancário": mes,
                    "Amortização (R$)": round(max(0.0, amort_price), 2),
                    "Juros (R$)": round(juros_banco, 2),
                    "Parcela Total (R$)": round(prestacao_price, 2)
                })

        df_pre_chaves = pd.DataFrame(dados_pre_chaves)
        df_banco = pd.DataFrame(dados_banco)
        
        st.success("✅ Proposta Comercial gerada com sucesso!")
        
        # Exibição por Abas
        tab_pre, tab_pos = st.tabs(["🏗️ Fluxo Pré-Chaves (Comercial Simplificado)", "🏦 Pós-Chaves (Financiamento Bancário)"])
        
        with tab_pre:
            st.dataframe(df_pre_chaves, use_container_width=True, height=400)
                
        with tab_pos:
            st.dataframe(df_banco, use_container_width=True, height=400)

        # ------------------------------------------
        # GERANDO EXCEL LIMPO E COMERCIAL
        # ------------------------------------------
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            ws = workbook.add_worksheet('Proposta Comercial')
            ws.hide_gridlines(2)
            ws.protect(SENHA_EXCEL)
            
            cor_azul_escuro = "#1F4E78"
            cor_cinza_claro = "#F2F2F2"
            
            fmt_titulo = workbook.add_format({
                'bold': True, 'font_size': 12, 'font_color': 'white', 'bg_color': cor_azul_escuro, 'align': 'center', 'valign': 'middle'
            })
            fmt_rotulo = workbook.add_format({
                'bold': True, 'font_color': '#333333', 'bg_color': cor_cinza_claro, 'border': 1, 'valign': 'middle'
            })
            fmt_valor_dado = workbook.add_format({
                'font_color': '#000000', 'bg_color': cor_cinza_claro, 'border': 1, 'align': 'right', 'valign': 'middle', 'num_format': 'R$ #,##0.00'
            })
            fmt_valor_texto = workbook.add_format({
                'font_color': '#000000', 'bg_color': cor_cinza_claro, 'border': 1, 'align': 'left', 'valign': 'middle'
            })
            fmt_cabecalho_tabela = workbook.add_format({
                'bold': True, 'font_color': 'white', 'bg_color': '#2F5597', 'align': 'center', 'valign': 'middle', 'border': 1, 'text_wrap': True
            })
            fmt_celula = workbook.add_format({'align': 'center', 'valign': 'middle', 'border': 1})
            fmt_moeda = workbook.add_format({'num_format': 'R$ #,##0.00', 'align': 'right', 'valign': 'middle', 'border': 1})
            
            ws.set_column('A:A', 8)
            ws.set_column('B:F', 22)
            
            # Resumo Executivo
            ws.merge_range('A1:F1', 'RESUMO DA PROPOSTA COMERCIAL', fmt_titulo)
            
            resumo_linhas = [
                ("Corretor Responsável", nome_corretor),
                ("CRECI", creci_corretor),
                ("Contato WhatsApp", telefone),
                ("Valor Total do Imóvel", valor_imovel),
                ("Sinal / Entrada", sinal_entrada),
                ("Utilização de FGTS", f"R$ {fgts_efetivo:,.2f} ({destino_fgts})" if usar_fgts else "Não Utilizado"),
                ("Financiamento Bancário Aprovado", valor_financiado_banco),
                ("Saldo Restante Construtora", saldo_construtora if usar_construtora else 0.0),
                ("Mensais Construtora (Reduzidas)", f"{meses_construtora - num_anuais}x de R$ {prestacao_construtora_mensal:,.2f}" if (usar_construtora and usar_anuais) else f"{meses_construtora}x de R$ {prestacao_construtora_mensal:,.2f}"),
                ("Anuais Construtora (Preço Cheio)", f"{num_anuais}x de R$ {valor_anual_unitaria:,.2f}" if (usar_construtora and usar_anuais) else "Sem Anuais"),
                ("Estimativa INCC Mensal", f"{taxa_incc_estimada:.2f}% a.m."),
                ("Taxa Juros Banco (Financiamento)", f"{taxa_juros:.2f}% a.a.")
            ]

            idx_linha = 2
            for rotulo, val in resumo_linhas:
                ws.write(idx_linha, 0, rotulo, fmt_rotulo)
                if isinstance(val, (int, float)):
                    ws.merge_range(idx_linha, 1, idx_linha, 5, val, fmt_valor_dado)
                else:
                    ws.merge_range(idx_linha, 1, idx_linha, 5, str(val), fmt_valor_texto)
                idx_linha += 1
                
            idx_linha += 1

            # Tabela 1: Pré-Chaves Simplificada
            if not df_pre_chaves.empty:
                ws.merge_range(idx_linha, 0, idx_linha, 5, 'FLUXO DE PAGAMENTO PRÉ-CHAVES (ESTIMATIVAS)', fmt_titulo)
                idx_linha += 1
                
                cabecalhos_c = list(df_pre_chaves.columns)
                for col_idx, cab in enumerate(cabecalhos_c):
                    ws.write(idx_linha, col_idx, cab, fmt_cabecalho_tabela)
                
                for item in dados_pre_chaves:
                    idx_linha += 1
                    ws.write(idx_linha, 0, item["Mês"], fmt_celula)
                    ws.write(idx_linha, 1, item["Mensal Construtora (R$)"], fmt_moeda)
                    ws.write(idx_linha, 2, item["Anual / Intermediária (R$)"], fmt_moeda)
                    ws.write(idx_linha, 3, item["Est. INCC (R$)"], fmt_moeda)
                    ws.write(idx_linha, 4, item["Est. Obra Banco (R$)"], fmt_moeda)
                    ws.write(idx_linha, 5, item["Total Mês (R$)"], fmt_moeda)
                
                idx_linha += 2

            # Tabela 2: Bancário Pós-Chaves
            ws.merge_range(idx_linha, 0, idx_linha, 3, f'FLUXO PÓS-CHAVES (BANCO - {nome_sistema.upper()})', fmt_titulo)
            idx_linha += 1
            
            cabecalhos_b = list(df_banco.columns)
            for col_idx, cab in enumerate(cabecalhos_b):
                ws.write(idx_linha, col_idx, cab, fmt_cabecalho_tabela)
            
            for item in dados_banco:
                idx_linha += 1
                ws.write(idx_linha, 0, item["Mês Bancário"], fmt_celula)
                ws.write(idx_linha, 1, item["Amortização (R$)"], fmt_moeda)
                ws.write(idx_linha, 2, item["Juros (R$)"], fmt_moeda)
                ws.write(idx_linha, 3, item["Parcela Total (R$)"], fmt_moeda)

        # Botão de Download
        st.download_button(
            label="📥 Baixar Proposta Comercial (.xlsx)",
            data=buffer.getvalue(),
            file_name="Proposta_Comercial_Planta.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

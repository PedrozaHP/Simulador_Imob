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
st.markdown("#### 🏦 Evolução de Obras (Banco)")
col_obra1, col_obra2, col_obra3 = st.columns(3)
with col_obra1:
    incluir_obra = st.checkbox("Simular Evolução de Obra?", value=True)
with col_obra2:
    meses_obra_duracao = st.number_input("Duração da Obra (Meses)", value=36, min_value=1, max_value=72, step=1, disabled=not incluir_obra)
with col_obra3:
    custos_fixos_banco = st.number_input("Custos Fixos Banco/Mês (MIP/DFI/Taxa R$)", value=55.0, step=5.0, format="%.2f", disabled=not incluir_obra)

# Parcelamento Construtora e INCC
st.markdown("#### 🏢 Parcelamento Direto com a Construtora & Reajuste INCC")
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
        help="Projeção do reajuste acumulado mês a mês sobre o saldo e parcelas da construtora."
    )

saldo_construtora = 0.0
prestacao_construtora_mensal = 0.0
if usar_construtora:
    abatimento_entrada_fgts = fgts_efetivo if ("Abater do Sinal" in destino_fgts) else 0.0
    sinal_efetivo_calculo = sinal_entrada + abatimento_entrada_fgts
    
    saldo_construtora = valor_imovel - financiamento_base_input - sinal_efetivo_calculo
    if saldo_construtora < 0: saldo_construtora = 0.0
    prestacao_construtora_mensal = saldo_construtora / meses_construtora if meses_construtora > 0 else 0.0
    st.info(f"💡 **Saldo Restante com Construtora:** R$ {saldo_construtora:,.2f} | **Parcela Base Sem INCC:** R$ {prestacao_construtora_mensal:,.2f}/mês.")

# ==========================================
# 5. PROCESSAMENTO DAS TABELAS
# ==========================================
st.markdown("---")
if st.button("🚀 Gerar Fluxo de Caixa Mês a Mês"):
    if valor_imovel <= 0 or prazo_banco_meses <= 0:
        st.warning("⚠️ Preencha os valores principais corretamente.")
    else:
        taxa_mensal_banco = (taxa_juros / 100) / 12
        taxa_incc_dec = taxa_incc_estimada / 100
        is_sac = "SAC" in sistema_amortizacao
        nome_sistema = "Tabela SAC" if is_sac else "Tabela Price"
        
        # ------------------------------------------
        # TABELA 1: FLUXO DE CAIXA PRÉ-CHAVES (MODELAGEM COMPLETA)
        # ------------------------------------------
        dados_pre_chaves = []
        prazo_obra_loop = meses_obra_duracao if incluir_obra else meses_construtora
        
        for mes in range(1, prazo_obra_loop + 1):
            # [EIXO TEMPORAL & OBRA]
            avanco_acumulado_pct = (mes / prazo_obra_loop) if incluir_obra else 1.0
            
            # [FLUXO CONSTRUTORA]
            fator_incc_acum = (1 + taxa_incc_dec) ** mes
            parc_base = prestacao_construtora_mensal if (usar_construtora and mes <= meses_construtora) else 0.0
            reajuste_incc_constr = parc_base * (fator_incc_acum - 1)
            parc_constr_corrigida = parc_base + reajuste_incc_constr
            
            # [FLUXO BANCO - EVOLUÇÃO DE OBRAS]
            if incluir_obra:
                saldo_financiado_incc = valor_financiado_banco * fator_incc_acum
                valor_repassado_construtora = saldo_financiado_incc * avanco_acumulado_pct
                juros_obra_mes = (valor_repassado_construtora * taxa_mensal_banco) + custos_fixos_banco
            else:
                saldo_financiado_incc = 0.0
                valor_repassado_construtora = 0.0
                juros_obra_mes = 0.0
            
            # [RESUMO DO DESEMBOLSO]
            desembolso_total_mes = parc_constr_corrigida + juros_obra_mes
            
            dados_pre_chaves.append({
                "Mês": mes,
                "% Avanço Obra": f"{avanco_acumulado_pct * 100:.2f}%",
                "Parc. Base Construtora (R$)": round(parc_base, 2),
                "Reajuste INCC (R$)": round(reajuste_incc_constr, 2),
                "Parc. Construtora Corrigida (R$)": round(parc_constr_corrigida, 2),
                "Saldo Financiado c/ INCC (R$)": round(saldo_financiado_incc, 2),
                "Valor Repassado (R$)": round(valor_repassado_construtora, 2),
                "Taxa Evolução Obra (R$)": round(juros_obra_mes, 2),
                "Desembolso Total Mensal (R$)": round(desembolso_total_mes, 2)
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
        
        st.success("✅ Fluxo de Caixa gerado com sucesso!")
        
        # Exibição em Abas
        tab_pre_chaves, tab_banco = st.tabs(["🏗️ Fluxo de Caixa Pré-Chaves (Detalhado)", "🏦 Pós-Chaves (Financiamento Bancário)"])
        
        with tab_pre_chaves:
            st.dataframe(df_pre_chaves, use_container_width=True, height=400)
                
        with tab_banco:
            st.dataframe(df_banco, use_container_width=True, height=400)

        # ------------------------------------------
        # GERANDO EXCEL PROFISSIONAL PROTEGIDO
        # ------------------------------------------
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            ws = workbook.add_worksheet('Modelagem Financeira')
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
            
            # Ajuste de larguras (Colunas A até I)
            ws.set_column('A:A', 8)
            ws.set_column('B:B', 14)
            ws.set_column('C:I', 20)
            
            # 1. Resumo Executivo
            ws.merge_range('A1:I1', 'RESUMO DA PROPOSTA COMERCIAL', fmt_titulo)
            
            resumo_linhas = [
                ("Corretor Responsável", nome_corretor),
                ("CRECI", creci_corretor),
                ("Contato WhatsApp", telefone),
                ("Valor Total do Imóvel", valor_imovel),
                ("Sinal / Entrada", sinal_entrada),
                ("Utilização de FGTS", f"R$ {fgts_efetivo:,.2f} ({destino_fgts})" if usar_fgts else "Não Utilizado"),
                ("Financiamento Bancário Aprovado", valor_financiado_banco),
                ("Saldo Restante Construtora", saldo_construtora if usar_construtora else 0.0),
                ("Projeção INCC Mensal", f"{taxa_incc_estimada:.2f}% a.m."),
                ("Taxa Juros Banco", f"{taxa_juros:.2f}% a.a."),
                ("Custos Fixos Banco (MIP/DFI/Taxa)", custos_fixos_banco)
            ]

            idx_linha = 2
            for rotulo, val in resumo_linhas:
                ws.write(idx_linha, 0, rotulo, fmt_rotulo)
                if isinstance(val, (int, float)):
                    ws.merge_range(idx_linha, 1, idx_linha, 8, val, fmt_valor_dado)
                else:
                    ws.merge_range(idx_linha, 1, idx_linha, 8, str(val), fmt_valor_texto)
                idx_linha += 1
                
            idx_linha += 1

            # 2. Tabela 1: Modelagem Pré-Chaves
            if not df_pre_chaves.empty:
                ws.merge_range(idx_linha, 0, idx_linha, 8, 'FLUXO DE CAIXA PRÉ-CHAVES (CONSTRUTORA vs EVOLUÇÃO DE OBRA)', fmt_titulo)
                idx_linha += 1
                
                cabecalhos_c = list(df_pre_chaves.columns)
                for col_idx, cab in enumerate(cabecalhos_c):
                    ws.write(idx_linha, col_idx, cab, fmt_cabecalho_tabela)
                
                for item in dados_pre_chaves:
                    idx_linha += 1
                    ws.write(idx_linha, 0, item["Mês"], fmt_celula)
                    ws.write(idx_linha, 1, item["% Avanço Obra"], fmt_celula)
                    ws.write(idx_linha, 2, item["Parc. Base Construtora (R$)"], fmt_moeda)
                    ws.write(idx_linha, 3, item["Reajuste INCC (R$)"], fmt_moeda)
                    ws.write(idx_linha, 4, item["Parc. Construtora Corrigida (R$)"], fmt_moeda)
                    ws.write(idx_linha, 5, item["Saldo Financiado c/ INCC (R$)"], fmt_moeda)
                    ws.write(idx_linha, 6, item["Valor Repassado (R$)"], fmt_moeda)
                    ws.write(idx_linha, 7, item["Taxa Evolução Obra (R$)"], fmt_moeda)
                    ws.write(idx_linha, 8, item["Desembolso Total Mensal (R$)"], fmt_moeda)
                
                idx_linha += 2

            # 3. Tabela 2: Bancário Pós-Chaves
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
            label="📥 Baixar Planilha Executiva (.xlsx)",
            data=buffer.getvalue(),
            file_name="Modelagem_Financeira_Planta.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

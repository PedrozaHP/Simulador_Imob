import streamlit as st
import pandas as pd
import io

# 1. Configuração da página
st.set_page_config(page_title="Simulador Imobiliário Profissional", layout="centered")

# ==========================================
# 2. SISTEMA DE LOGIN VIA COFRE SEGURO (SECRETS)
# ==========================================
CLIENTES_AUTORIZADOS = st.secrets.get("CLIENTES_AUTORIZADOS", {})

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
# 3. ÁREA LOGADA
# ==========================================
dados_usuario = CLIENTES_AUTORIZADOS[st.session_state.usuario_logado]
nome_corretor = dados_usuario["nome"]
telefone = dados_usuario["telefone"]

st.sidebar.success(f"Logado como:\n**{nome_corretor}**")
if st.sidebar.button("Sair / Trocar Conta"):
    st.session_state.usuario_logado = None
    st.rerun()

st.markdown("---")

# ==========================================
# 4. DADOS DA NEGOCIAÇÃO E MODELO VIVAZ
# ==========================================
st.subheader("🏗️ Dados do Imóvel e Composição de Pagamento")

sistema_amortizacao = st.radio(
    "Sistema de Amortização (Pós-Chaves / Financiamento):",
    ["Tabela SAC (Prestações Decrescentes)", "Tabela Price (Prestações Fixas)"],
    horizontal=True
)

col1, col2 = st.columns(2)
with col1:
    valor_imovel = st.number_input("Valor Total do Imóvel (R$)", value=200000.0, step=10000.0, format="%.2f")
    valor_financiado_banco = st.number_input("Financiamento Bancário Aprovado (R$)", value=120000.0, step=10000.0, format="%.2f")
with col2:
    sinal_entrada = st.number_input("Valor do Ato / Sinal (R$)", value=10000.0, step=5000.0, format="%.2f")
    prazo_banco_meses = st.number_input("Prazo do Financiamento Bancário (Meses)", value=360, min_value=1, max_value=420, step=1)

taxa_juros = st.number_input("Taxa de Juros Anual do Financiamento (%)", value=9.5, step=0.1, format="%.2f")

# Seção de Condições de Planta (FGTS, Construtora e Obra)
st.markdown("---")
st.subheader("💡 Condições Especiais da Planta (Estilo Construtora)")

col_fgts1, col_fgts2 = st.columns(2)
with col_fgts1:
    usar_fgts = st.checkbox("Cliente vai utilizar FGTS?")
with col_fgts2:
    valor_fgts = st.number_input("Valor do FGTS (R$)", value=15000.0, step=5000.0, format="%.2f", disabled=not usar_fgts)

# Cálculo automático do saldo que fica com a construtora (Modelo Vivaz)
fgts_efetivo = valor_fgts if usar_fgts else 0.0
saldo_construtora = valor_imovel - valor_financiado_banco - sinal_entrada - fgts_efetivo
if saldo_construtora < 0: saldo_construtora = 0.0

st.info(f"💡 **Saldo Restante com a Construtora (Calculado):** R$ {saldo_construtora:,.2f} (Diferença entre o valor do imóvel, o financiamento, sinal e FGTS).")

col_constr1, col_constr2 = st.columns(2)
with col_constr1:
    meses_construtora = st.number_input("Prazo das Mensais da Construtora (Meses / Obra)", value=36, min_value=1, max_value=60, step=1)
with col_constr2:
    incluir_obra = st.checkbox("Incluir estimativa de Evolução de Obra?")

valor_medio_obra = 0.0
if incluir_obra:
    valor_medio_obra = st.number_input("Valor Médio Estimado da Evolução de Obra/Mês (R$)", value=450.0, step=50.0, format="%.2f")
    st.info("ℹ️ **Fonte Oficial de Acompanhamento:** Durante a construção, os valores da evolução de obra podem ser monitorados de forma oficial pelo **App Habitação CAIXA** ou portal do banco financiador.")

# ==========================================
# 5. PROCESSAMENTO DO FLUXO
# ==========================================
if st.button("🚀 Gerar Planilha Executiva para o Cliente"):
    if valor_imovel <= 0 or prazo_banco_meses <= 0:
        st.warning("⚠️ Preencha os valores principais corretamente.")
    else:
        taxa_mensal = (taxa_juros / 100) / 12
        is_sac = "SAC" in sistema_amortizacao
        nome_sistema = "Tabela SAC" if is_sac else "Tabela Price"
        
        prestacao_construtora_mensal = saldo_construtora / meses_construtora if meses_construtora > 0 else 0.0
        
        dados_financiamento = []
        
        # Vamos simular o fluxo mês a mês cobrindo o período da construtora/obra e depois o pós-obra
        total_meses_simulacao = max(prazo_banco_meses, meses_construtora)
        
        if is_sac:
            amortizacao_base = valor_financiado_banco / prazo_banco_meses if prazo_banco_meses > 0 else 0
            
            for mes in range(1, total_meses_simulacao + 1):
                # Mensalidade da construtora (enquanto estiver no prazo definido)
                parc_constr = prestacao_construtora_mensal if mes <= meses_construtora else 0.0
                
                # Juros de obra / Evolução de obra estimada
                parc_obra = valor_medio_obra if (incluir_obra and mes <= meses_construtora) else 0.0
                
                # Parcela do financiamento banco (assume-se que começa após a entrega/obra, ou integrada)
                # Para simplificar e mostrar o encargo total na planta:
                if mes <= meses_construtora:
                    # Durante a obra o cliente paga a mensalidade da construtora + evolução de obra
                    prestacao_total = parc_constr + parc_obra
                    fase_desc = "Fase de Obras (Construtora + Juros Estimados)"
                    amort_mes = 0.0
                else:
                    # Pós-obra: entra o financiamento bancário puro
                    # Calculamos o juro proporcional ao mês do financiamento
                    mes_banco = mes - meses_construtora
                    # Aproximação simplificada para exibição do encargo SAC pós-obra
                    saldo_parcial = valor_financiado_banco - (amortizacao_base * (mes_banco - 1))
                    if saldo_parcial < 0: saldo_parcial = 0
                    juros_banco = saldo_parcial * taxa_mensal
                    prestacao_total = amortizacao_base + juros_banco
                    fase_desc = "Pós-Obra / Financiamento Bancário"
                    amort_mes = amortizacao_base
                
                dados_financiamento.append({
                    "Mês": mes,
                    "Ano": f"Ano {(mes - 1) // 12 + 1}",
                    "Fase / Descrição": fase_desc,
                    "Parcela Total (R$)": round(prestacao_total, 2),
                    "Amortização (R$)": round(amort_mes, 2)
                })
        else:
            # Lógica Price
            if taxa_mensal > 0 and prazo_banco_meses > 0:
                prestacao_price = valor_financiado_banco * (taxa_mensal * (1 + taxa_mensal)**prazo_banco_meses) / ((1 + taxa_mensal)**prazo_banco_meses - 1)
            else:
                prestacao_price = valor_financiado_banco / prazo_banco_meses if prazo_banco_meses > 0 else 0
                
            for mes in range(1, total_meses_simulacao + 1):
                parc_constr = prestacao_construtora_mensal if mes <= meses_construtora else 0.0
                parc_obra = valor_medio_obra if (incluir_obra and mes <= meses_construtora) else 0.0
                
                if mes <= meses_construtora:
                    prestacao_total = parc_constr + parc_obra
                    fase_desc = "Fase de Obras (Construtora + Juros Estimados)"
                    amort_mes = 0.0
                else:
                    mes_banco = mes - meses_construtora
                    juros_banco = valor_financiado_banco * taxa_mensal # aproximação visual
                    amort_price = prestacao_price - juros_banco
                    prestacao_total = prestacao_price
                    fase_desc = "Pós-Obra / Financiamento Bancário"
                    amort_mes = max(0.0, amort_price)
                    
                dados_financiamento.append({
                    "Mês": mes,
                    "Ano": f"Ano {(mes - 1) // 12 + 1}",
                    "Fase / Descrição": fase_desc,
                    "Parcela Total (R$)": round(prestacao_total, 2),
                    "Amortização (R$)": round(amort_mes, 2)
                })

        df_cliente = pd.DataFrame(dados_financiamento)
        
        st.success(f"✅ Proposta gerada com sucesso! Total de parcelas mapeadas: {len(df_cliente)}")
        st.dataframe(df_cliente, use_container_width=True, height=350)
        
        # ------------------------------------------
        # GERANDO EXCEL PROFISSIONAL (SEM SALDO DEVEDOR)
        # ------------------------------------------
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            ws = workbook.add_worksheet('Proposta Comercial')
            ws.hide_gridlines(0)
            
            cor_azul_escuro = "#1F4E78"
            cor_cinza_claro = "#F2F2F2"
            
            fmt_titulo = workbook.add_format({
                'bold': True, 'font_size': 13, 'font_color': 'white', 'bg_color': cor_azul_escuro, 'align': 'center', 'valign': 'middle'
            })
            fmt_rotulo = workbook.add_format({
                'bold': True, 'font_color': '#333333', 'bg_color': cor_cinza_claro, 'border': 1, 'valign': 'middle'
            })
            fmt_valor_dado = workbook.add_format({
                'font_color': '#000000', 'bg_color': cor_cinza_claro, 'border': 1, 'align': 'right', 'valign': 'middle', 'num_format': 'R$ #,##0.00'
            })
            fmt_valor_texto = workbook.add_format({
                'font_color': '#000000', 'bg_color': cor_cinza_claro, 'border': 1, 'align': 'center', 'valign': 'middle'
            })
            fmt_cabecalho_tabela = workbook.add_format({
                'bold': True, 'font_color': 'white', 'bg_color': '#2F5597', 'align': 'center', 'valign': 'middle', 'border': 1
            })
            fmt_celula = workbook.add_format({
                'align': 'center', 'valign': 'middle', 'border': 1
            })
            fmt_moeda = workbook.add_format({
                'num_format': 'R$ #,##0.00', 'align': 'right', 'valign': 'middle', 'border': 1
            })
            
            # Larguras das colunas (4 colunas agora, sem saldo devedor)
            ws.set_column('A:A', 10)
            ws.set_column('B:B', 14)
            ws.set_column('C:C', 38)
            ws.set_column('D:E', 22)
            
            # Bloco Superior: Resumo Executivo para o Cliente
            ws.merge_range('A1:E1', 'RESUMO DA PROPOSTA COMERCIAL & FLUXO', fmt_titulo)
            
            resumo_linhas = [
                ("Corretor Responsável", nome_corretor),
                ("Contato WhatsApp", telefone),
                ("Valor Total do Imóvel", valor_imovel),
                ("Sinal / Entrada", sinal_entrada),
                ("Utilização de FGTS", f"R$ {fgts_efetivo:,.2f}" if usar_fgts else "Não Utilizado"),
                ("Financiamento Bancário Aprovado", valor_financiado_banco),
                ("Saldo Restante com a Construtora", saldo_construtora),
                ("Prazo Mensais Construtora", f"{meses_construtora} Meses (Valor: R$ {prestacao_construtora_mensal:,.2f}/mês)"),
                ("Sistema Pós-Chaves", nome_sistema)
            ]
            
            if incluir_obra:
                resumo_linhas.append(("Evolução de Obra (Estimada)", f"R$ {valor_medio_obra:,.2f} / mês por {meses_construtora} meses"))
                resumo_linhas.append(("Canal Oficial de Acompanhamento", "App Habitação CAIXA / Portal do Banco"))

            idx_linha = 2
            for rotulo, val in resumo_linhas:
                ws.write(idx_linha, 0, rotulo, fmt_rotulo)
                ws.merge_range(idx_linha, 1, idx_linha, 4, "", fmt_rotulo)
                if isinstance(val, (int, float)):
                    ws.write(idx_linha, 1, val, fmt_valor_dado)
                else:
                    ws.write(idx_linha, 1, str(val), fmt_valor_texto)
                idx_linha += 1
                
            idx_linha += 1
            ws.merge_range(idx_linha, 0, idx_linha, 4, 'FLUXO DETALHADO DE PAGAMENTO', fmt_titulo)
            idx_linha += 1
            
            # Cabeçalhos da Tabela Mês a Mês (Sem saldo devedor)
            cabecalhos = ["Mês", "Período", "Fase / Descrição", "Parcela Total (R$)", "Amortização (R$)"]
            for col_idx, cab in enumerate(cabecalhos):
                ws.write(idx_linha, col_idx, cab, fmt_cabecalho_tabela)
            
            linha_inicio_tabela = idx_linha + 1
            
            # Preenchendo as linhas do fluxo
            for item in dados_financiamento:
                idx_linha += 1
                ws.write(idx_linha, 0, item["Mês"], fmt_celula)
                ws.write(idx_linha, 1, item["Ano"], fmt_celula)
                ws.write(idx_linha, 2, item["Fase / Descrição"], fmt_celula)
                ws.write(idx_linha, 3, item["Parcela Total (R$)"], fmt_moeda)
                ws.write(idx_linha, 4, item["Amortização (R$)"], fmt_moeda)
                
            ws.freeze_panes(linha_inicio_tabela, 0)

        # Botão de Download
        st.download_button(
            label="📥 Baixar Planilha Executiva Estilo Construtora (.xlsx)",
            data=buffer.getvalue(),
            file_name="Proposta_Comercial_Imovel_Planta.xlsx",
            mime="application/vnd.ms-excel"
        )

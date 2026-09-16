import streamlit as st
import pandas as pd
import io

# 1. Configuração da página
st.set_page_config(page_title="Simulador Imobiliário Profissional", layout="centered")

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
# 3. ÁREA LOGADA - DADOS ESTÁTICOS (IMPOSSÍVEL ALTERAR)
# ==========================================
dados_usuario = CLIENTES_AUTORIZADOS[st.session_state.usuario_logado]

# Busca segura no dicionário para evitar crash se faltar alguma chave
nome_corretor = dados_usuario.get("nome", "Não Informado")
telefone = dados_usuario.get("telefone", "Não Informado")
creci_corretor = dados_usuario.get("creci", "Não Informado")

# Exibição estática (somente leitura)
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

# Seção de Condições Especiais da Planta
st.markdown("---")
st.subheader("💡 Condições Especiais da Planta (Opcionais)")

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

# Evolução de Obra
col_obra1, col_obra2 = st.columns(2)
with col_obra1:
    incluir_obra = st.checkbox("Incluir estimativa de Evolução de Obra?")
with col_obra2:
    meses_obra_duracao = st.number_input("Duração da Obra (Meses)", value=36, min_value=1, max_value=72, step=1, disabled=not incluir_obra)
    valor_medio_obra = st.number_input("Valor Médio Estimado da Obra/Mês (R$)", value=450.0, step=50.0, format="%.2f", disabled=not incluir_obra)

if incluir_obra:
    st.info("ℹ️ **Fonte Oficial de Acompanhamento:** App Habitação CAIXA / Portal do Banco.")

# Parcelamento Construtora
st.markdown("#### 🏢 Parcelamento Direto com a Construtora")
col_constr_opc1, col_constr_opc2 = st.columns(2)
with col_constr_opc1:
    usar_construtora = st.checkbox("Parcelar saldo restante direto com a Construtora?")
with col_constr_opc2:
    sincronizar_prazos = st.checkbox("Igualar prazo da Construtora ao prazo da Obra", value=True, disabled=not usar_construtora or not incluir_obra)

padrao_meses_construtora = meses_obra_duracao if (incluir_obra and sincronizar_prazos) else 36

meses_construtora = st.number_input(
    "Prazo das Mensais da Construtora (Meses)", 
    value=padrao_meses_construtora, 
    min_value=1, 
    max_value=120, 
    step=1, 
    disabled=not usar_construtora
)

saldo_construtora = 0.0
prestacao_construtora_mensal = 0.0
if usar_construtora:
    abatimento_entrada_fgts = fgts_efetivo if ("Abater do Sinal" in destino_fgts) else 0.0
    sinal_efetivo_calculo = sinal_entrada + abatimento_entrada_fgts
    
    saldo_construtora = valor_imovel - financiamento_base_input - sinal_efetivo_calculo
    if saldo_construtora < 0: saldo_construtora = 0.0
    prestacao_construtora_mensal = saldo_construtora / meses_construtora if meses_construtora > 0 else 0.0
    st.info(f"💡 **Saldo Restante com a Construtora (Calculado):** R$ {saldo_construtora:,.2f} dividido em {meses_construtora}x de R$ {prestacao_construtora_mensal:,.2f}.")

# ==========================================
# 5. PROCESSAMENTO E GERAÇÃO DA PLANILHA
# ==========================================
st.markdown("---")
if st.button("🚀 Gerar Planilha Executiva para o Cliente"):
    if valor_imovel <= 0 or prazo_banco_meses <= 0:
        st.warning("⚠️ Preencha os valores principais corretamente.")
    else:
        taxa_mensal = (taxa_juros / 100) / 12
        is_sac = "SAC" in sistema_amortizacao
        nome_sistema = "Tabela SAC" if is_sac else "Tabela Price"
        
        dados_financiamento = []
        prazo_fase_obras = 0
        if usar_construtora:
            prazo_fase_obras = max(prazo_fase_obras, meses_construtora)
        if incluir_obra:
            prazo_fase_obras = max(prazo_fase_obras, meses_obra_duracao)
            
        total_meses_simulacao = prazo_fase_obras + prazo_banco_meses
        
        if is_sac:
            amortizacao_base = valor_financiado_banco / prazo_banco_meses if prazo_banco_meses > 0 else 0
            
            for mes in range(1, total_meses_simulacao + 1):
                if mes <= prazo_fase_obras:
                    parc_constr = prestacao_construtora_mensal if (usar_construtora and mes <= meses_construtora) else 0.0
                    parc_obra = valor_medio_obra if (incluir_obra and mes <= meses_obra_duracao) else 0.0
                    
                    prestacao_total = parc_constr + parc_obra
                    fase_desc = "Fase de Obras / Pré-Chaves (Construtora + Juros de Obra)"
                    amort_mes = 0.0
                else:
                    mes_banco = mes - prazo_fase_obras
                    saldo_parcial = valor_financiado_banco - (amortizacao_base * (mes_banco - 1))
                    if saldo_parcial < 0: saldo_parcial = 0
                    juros_banco = saldo_parcial * taxa_mensal
                    prestacao_total = amortizacao_base + juros_banco
                    fase_desc = "Pós-Obra / Financiamento Bancário"
                    amort_mes = amortizacao_base
                
                dados_financiamento.append({
                    "Mês": mes,
                    "Fase / Descrição": fase_desc,
                    "Parcela Total (R$)": round(prestacao_total, 2),
                    "Amortização (R$)": round(amort_mes, 2)
                })
        else:
            if taxa_mensal > 0 and prazo_banco_meses > 0:
                prestacao_price = valor_financiado_banco * (taxa_mensal * (1 + taxa_mensal)**prazo_banco_meses) / ((1 + taxa_mensal)**prazo_banco_meses - 1)
            else:
                prestacao_price = valor_financiado_banco / prazo_banco_meses if prazo_banco_meses > 0 else 0
                
            for mes in range(1, total_meses_simulacao + 1):
                if mes <= prazo_fase_obras:
                    parc_constr = prestacao_construtora_mensal if (usar_construtora and mes <= meses_construtora) else 0.0
                    parc_obra = valor_medio_obra if (incluir_obra and mes <= meses_obra_duracao) else 0.0
                    
                    prestacao_total = parc_constr + parc_obra
                    fase_desc = "Fase de Obras / Pré-Chaves (Construtora + Juros de Obra)"
                    amort_mes = 0.0
                else:
                    juros_banco = valor_financiado_banco * taxa_mensal
                    amort_price = prestacao_price - juros_banco
                    prestacao_total = prestacao_price
                    fase_desc = "Pós-Obra / Financiamento Bancário"
                    amort_mes = max(0.0, amort_price)
                    
                dados_financiamento.append({
                    "Mês": mes,
                    "Fase / Descrição": fase_desc,
                    "Parcela Total (R$)": round(prestacao_total, 2),
                    "Amortização (R$)": round(amort_mes, 2)
                })

        df_cliente = pd.DataFrame(dados_financiamento)
        
        st.success(f"✅ Proposta gerada com sucesso! Total de parcelas mapeadas: {len(df_cliente)}")
        st.dataframe(df_cliente, use_container_width=True, height=350)
        
        # ------------------------------------------
        # GERANDO EXCEL PROFISSIONAL PROTEGIDO
        # ------------------------------------------
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            ws = workbook.add_worksheet('Proposta Comercial')
            ws.hide_gridlines(2)
            
            # 🔒 BLOQUEIO DA PLANILHA: Exige a senha para desproteger e alterar células
            ws.protect(SENHA_EXCEL)
            
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
                'font_color': '#000000', 'bg_color': cor_cinza_claro, 'border': 1, 'align': 'left', 'valign': 'middle'
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
            
            ws.set_column('A:A', 30)
            ws.set_column('B:B', 40)
            ws.set_column('C:D', 20)
            
            # Bloco Superior: Resumo Executivo
            ws.merge_range('A1:D1', 'RESUMO DA PROPOSTA COMERCIAL & FLUXO', fmt_titulo)
            
            resumo_linhas = [
                ("Corretor Responsável", nome_corretor),
                ("CRECI", creci_corretor),
                ("Contato WhatsApp", telefone),
                ("Valor Total do Imóvel", valor_imovel),
                ("Sinal / Entrada", sinal_entrada),
                ("Utilização de FGTS", f"R$ {fgts_efetivo:,.2f} ({destino_fgts})" if usar_fgts else "Não Utilizado"),
                ("Financiamento Bancário Aprovado", valor_financiado_banco)
            ]
            
            if usar_construtora:
                resumo_linhas.append(("Saldo Restante com a Construtora", saldo_construtora))
                resumo_linhas.append(("Prazo Mensais Construtora", f"{meses_construtora} Meses (R$ {prestacao_construtora_mensal:,.2f}/mês)"))
            
            resumo_linhas.append(("Sistema Pós-Chaves", nome_sistema))
            
            if incluir_obra:
                resumo_linhas.append(("Evolução de Obra (Estimada)", f"R$ {valor_medio_obra:,.2f} / mês por {meses_obra_duracao} meses"))
                resumo_linhas.append(("Canal Oficial de Acompanhamento", "App Habitação CAIXA / Portal do Banco"))

            idx_linha = 2
            for rotulo, val in resumo_linhas:
                ws.write(idx_linha, 0, rotulo, fmt_rotulo)
                if isinstance(val, (int, float)):
                    ws.merge_range(idx_linha, 1, idx_linha, 3, val, fmt_valor_dado)
                else:
                    ws.merge_range(idx_linha, 1, idx_linha, 3, str(val), fmt_valor_texto)
                idx_linha += 1
                
            idx_linha += 1
            ws.merge_range(idx_linha, 0, idx_linha, 3, 'FLUXO DETALHADO DE PAGAMENTO', fmt_titulo)
            idx_linha += 1
            
            cabecalhos = ["Mês", "Fase / Descrição", "Parcela Total (R$)", "Amortização (R$)"]
            for col_idx, cab in enumerate(cabecalhos):
                ws.write(idx_linha, col_idx, cab, fmt_cabecalho_tabela)
            
            linha_inicio_tabela = idx_linha + 1
            
            for item in dados_financiamento:
                idx_linha += 1
                ws.write(idx_linha, 0, item["Mês"], fmt_celula)
                ws.write(idx_linha, 1, item["Fase / Descrição"], fmt_celula)
                ws.write(idx_linha, 2, item["Parcela Total (R$)"], fmt_moeda)
                ws.write(idx_linha, 3, item["Amortização (R$)"], fmt_moeda)
                
            ws.freeze_panes(linha_inicio_tabela, 0)

        # Botão de Download Atualizado
        st.download_button(
            label="📥 Baixar Planilha Executiva Personalizada (.xlsx)",
            data=buffer.getvalue(),
            file_name="Proposta_Comercial_Imovel.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

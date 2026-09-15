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
# 4. DADOS DA NEGOCIAÇÃO
# ==========================================
st.subheader("🏗️ Dados da Negociação e Amortização")

sistema_amortizacao = st.radio(
    "Sistema de Amortização:",
    ["Tabela SAC (Prestações Decrescentes)", "Tabela Price (Prestações Fixas)"],
    horizontal=True
)

col1, col2 = st.columns(2)
with col1:
    valor_imovel = st.number_input("Valor do Imóvel (R$)", value=300000.0, step=10000.0, format="%.2f")
    taxa_juros = st.number_input("Taxa de Juros Anual (%)", value=9.5, step=0.1, format="%.2f")
with col2:
    entrada = st.number_input("Valor da Entrada (R$)", value=60000.0, step=10000.0, format="%.2f")
    meses = st.number_input("Prazo (Meses)", value=360, min_value=1, max_value=420, step=1)

# Campo extra pensado para o corretor: Simulação de Amortização Extra
st.markdown("---")
st.subheader("💡 Simulação de Amortização Extra (Opcional)")
col_a, col_b = st.columns(2)
with col_a:
    valor_amortizacao_extra = st.number_input("Valor de Recurso Extra / FGTS (R$)", value=20000.0, step=5000.0, format="%.2f")
with col_b:
    mes_amortizacao = st.number_input("Mês em que será aplicada a amortização", value=12, min_value=1, max_value=meses, step=1)
    opcao_amortizacao = st.selectbox("Efeito da Amortização:", ["Reduzir o Prazo (Economiza mais juros)", "Reduzir o Valor da Parcela"])

# ==========================================
# 5. PROCESSAMENTO DO FLUXO
# ==========================================
if st.button("🚀 Gerar Planilha Executiva para o Cliente"):
    if valor_imovel <= 0 or meses <= 0:
        st.warning("⚠️ Preencha o Valor do Imóvel e o Prazo corretamente.")
    else:
        valor_financiado = valor_imovel - entrada
        taxa_mensal = (taxa_juros / 100) / 12
        is_sac = "SAC" in sistema_amortizacao
        nome_sistema = "Tabela SAC" if is_sac else "Tabela Price"
        
        dados_financiamento = []
        saldo_devedor = valor_financiado
        
        if is_sac:
            amortizacao_base = valor_financiado / meses if meses > 0 else 0
            for mes in range(1, meses + 1):
                juros = saldo_devedor * taxa_mensal
                prestacao = amortizacao_base + juros
                
                # Verifica se há amortização extra neste mês específico
                amortizacao_total_mes = amortizacao_base
                if mes == mes_amortizacao and valor_amortizacao_extra > 0:
                    amortizacao_total_mes += valor_amortizacao_extra
                
                saldo_devedor -= amortizacao_total_mes
                if saldo_devedor < 0:
                    saldo_devedor = 0
                    
                dados_financiamento.append({
                    "Mês": mes,
                    "Ano": f"Ano {(mes - 1) // 12 + 1}",
                    "Parcela (R$)": round(prestacao, 2),
                    "Amortização (R$)": round(amortizacao_total_mes, 2),
                    "Saldo Devedor (R$)": round(saldo_devedor, 2)
                })
                if saldo_devedor == 0:
                    break
        else:
            if taxa_mensal > 0 and meses > 0:
                prestacao_price = valor_financiado * (taxa_mensal * (1 + taxa_mensal)**meses) / ((1 + taxa_mensal)**meses - 1)
            else:
                prestacao_price = valor_financiado / meses
                
            for mes in range(1, meses + 1):
                juros = saldo_devedor * taxa_mensal
                amortizacao_price = prestacao_price - juros
                
                if mes == mes_amortizacao and valor_amortizacao_extra > 0:
                    amortizacao_price += valor_amortizacao_extra
                    
                saldo_devedor -= amortizacao_price
                if saldo_devedor < 0:
                    saldo_devedor = 0
                    
                dados_financiamento.append({
                    "Mês": mes,
                    "Ano": f"Ano {(mes - 1) // 12 + 1}",
                    "Parcela (R$)": round(prestacao_price, 2),
                    "Amortização (R$)": round(amortizacao_price, 2),
                    "Saldo Devedor (R$)": round(saldo_devedor, 2)
                })
                if saldo_devedor == 0:
                    break

        df_cliente = pd.DataFrame(dados_financiamento)
        
        st.success(f"✅ Proposta gerada com sucesso! Total de parcelas mapeadas: {len(df_cliente)}")
        st.dataframe(df_cliente, use_container_width=True, height=350)
        
        # ------------------------------------------
        # GERANDO EXCEL PROFISSIONAL EM UMA ÚNICA PÁGINA
        # ------------------------------------------
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            ws = workbook.add_worksheet('Proposta Comercial')
            
            # Deixando a grade visível
            ws.hide_gridlines(0)
            
            # Cores e Estilos
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
            
            # Larguras das colunas
            ws.set_column('A:A', 10)
            ws.set_column('B:B', 14)
            ws.set_column('C:E', 22)
            
            # Bloco Superior: Resumo Executivo para o Cliente (Tudo na mesma página)
            ws.merge_range('A1:E1', 'RESUMO DA PROPOSTA COMERCIAL', fmt_titulo)
            
            resumo_linhas = [
                ("Imóvel / Operação", f"Imóvel Residencial ({nome_sistema})"),
                ("Corretor Responsável", nome_corretor),
                ("Contato WhatsApp", telefone),
                ("Valor do Imóvel", valor_imovel),
                ("Valor da Entrada", entrada),
                ("Valor Financiado", valor_financiado),
                ("Prazo Contratual", f"{meses} Meses"),
                ("Taxa de Juros", f"{taxa_juros}% a.a."),
                ("Valor da 1ª Parcela", df_cliente.iloc[0]['Parcela (R$)'])
            ]
            
            if valor_amortizacao_extra > 0:
                resumo_linhas.append(("Amortização Extra Simulada", f"R$ {valor_amortizacao_extra:,.2f} no mês {mes_amortizacao}"))

            idx_linha = 2
            for rotulo, val in resumo_linhas:
                ws.write(idx_linha, 0, rotulo, fmt_rotulo)
                ws.merge_range(idx_linha, 1, idx_linha, 4, "", fmt_rotulo) # preenche o fundo
                if isinstance(val, (int, float)):
                    ws.write(idx_linha, 1, val, fmt_valor_dado)
                else:
                    ws.write(idx_linha, 1, str(val), fmt_valor_texto)
                idx_linha += 1
                
            # Espaço antes da tabela
            idx_linha += 1
            ws.merge_range(idx_linha, 0, idx_linha, 4, 'FLUXO DETALHADO DA EVOLUÇÃO DO FINANCIAMENTO', fmt_titulo)
            idx_linha += 1
            
            # Cabeçalhos da Tabela Mês a Mês
            cabecalhos = ["Mês", "Período", "Valor da Parcela", "Amortização", "Saldo Devedor Atual"]
            for col_idx, cab in enumerate(cabecalhos):
                ws.write(idx_linha, col_idx, cab, fmt_cabecalho_tabela)
            
            linha_inicio_tabela = idx_linha + 1
            
            # Preenchendo as linhas do fluxo
            for item in dados_financiamento:
                idx_linha += 1
                ws.write(idx_linha, 0, item["Mês"], fmt_celula)
                ws.write(idx_linha, 1, item["Ano"], fmt_celula)
                ws.write(idx_linha, 2, item["Parcela (R$)"], fmt_moeda)
                ws.write(idx_linha, 3, item["Amortização (R$)"], fmt_moeda)
                ws.write(idx_linha, 4, item["Saldo Devedor (R$)"], fmt_moeda)
                
            # Congela painéis logo abaixo do cabeçalho da tabela para rolar com facilidade
            ws.freeze_panes(linha_inicio_tabela, 0)

        # Botão de Download
        st.download_button(
            label=f"📥 Baixar Planilha Executiva para o Cliente ({nome_sistema})",
            data=buffer.getvalue(),
            file_name=f"Proposta_Comercial_{nome_sistema.replace(' ', '_')}.xlsx",
            mime="application/vnd.ms-excel"
        )

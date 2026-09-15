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

# Controlando o estado de login na sessão
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

# Se não estiver logado, mostra a tela de bloqueio
if not st.session_state.usuario_logado:
    st.info("💡 Área restrita para corretores licenciados. Insira seu Usuário cadastrado para acessar a ferramenta.")
    usuario_input = st.text_input("Seu Usuário de Acesso:")
    
    if st.button("🔓 Entrar na Ferramenta"):
        usuario_limpo = usuario_input.strip().lower()
        
        if usuario_limpo in CLIENTES_AUTORIZADOS:
            st.session_state.usuario_logado = usuario_limpo
            st.rerun()
        else:
            st.error("❌ Usuário não encontrado ou licença inativa. Entre em contato para adquirir seu acesso.")
    st.stop()

# ==========================================
# 3. ÁREA LOGADA (Usuário Autenticado)
# ==========================================
dados_usuario = CLIENTES_AUTORIZADOS[st.session_state.usuario_logado]
nome_corretor = dados_usuario["nome"]
telefone = dados_usuario["telefone"]

# Barra lateral com dados da conta e botão de sair
st.sidebar.success(f"Logado como:\n**{nome_corretor}**")
if st.sidebar.button("Sair / Trocar Conta"):
    st.session_state.usuario_logado = None
    st.rerun()

st.markdown("---")
st.write("Gere simulações de financiamento personalizadas e profissionais com a sua marca.")

# ==========================================
# 4. DADOS DA NEGOCIAÇÃO E ESCOLHA DO SISTEMA
# ==========================================
st.subheader("🏗️ Dados da Negociação")

sistema_amortizacao = st.radio(
    "Escolha o Sistema de Amortização desejado:",
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

# ==========================================
# 5. PROCESSAMENTO E GERAÇÃO DA SIMULAÇÃO
# ==========================================
if st.button("🚀 Gerar Simulação e Planilha Profissional"):
    if valor_imovel <= 0 or meses <= 0:
        st.warning("⚠️ Por favor, preencha o Valor do Imóvel e o Prazo corretamente para gerar a simulação.")
    else:
        valor_financiado = valor_imovel - entrada
        taxa_mensal = (taxa_juros / 100) / 12
        
        is_sac = "SAC" in sistema_amortizacao
        nome_sistema_escolhido = "Tabela SAC" if is_sac else "Tabela Price"
        
        dados_financiamento = []
        
        if is_sac:
            amortizacao_sac = valor_financiado / meses if meses > 0 else 0
            saldo_devedor = valor_financiado
            for mes in range(1, meses + 1):
                juros = saldo_devedor * taxa_mensal
                prestacao = amortizacao_sac + juros
                saldo_devedor -= amortizacao_sac
                dados_financiamento.append({
                    "Mês": mes,
                    "Ano": f"Ano {(mes - 1) // 12 + 1}",
                    "Prestação (R$)": round(prestacao, 2),
                    "Amortização (R$)": round(amortizacao_sac, 2),
                    "Juros (R$)": round(juros, 2),
                    "Saldo Devedor (R$)": round(max(saldo_devedor, 0), 2)
                })
        else:
            saldo_devedor = valor_financiado
            if taxa_mensal > 0 and meses > 0:
                prestacao_price = valor_financiado * (taxa_mensal * (1 + taxa_mensal)**meses) / ((1 + taxa_mensal)**meses - 1)
            else:
                prestacao_price = valor_financiado / meses if meses > 0 else 0
                
            for mes in range(1, meses + 1):
                juros = saldo_devedor * taxa_mensal
                amortizacao_price = prestacao_price - juros
                saldo_devedor -= amortizacao_price
                dados_financiamento.append({
                    "Mês": mes,
                    "Ano": f"Ano {(mes - 1) // 12 + 1}",
                    "Prestação (R$)": round(prestacao_price, 2),
                    "Amortização (R$)": round(amortizacao_price, 2),
                    "Juros (R$)": round(juros, 2),
                    "Saldo Devedor (R$)": round(max(saldo_devedor, 0), 2)
                })
                
        df_escolhido = pd.DataFrame(dados_financiamento)
        
        st.success(f"✅ Simulação gerada com sucesso via **{nome_sistema_escolhido}** contemplando todos os **{meses} meses**!")
        
        # Exibindo a prévia interativa com scroll na tela
        st.write(f"📋 **Evolução Completa (do Mês 1 ao Mês {meses}):**")
        st.dataframe(df_escolhido, use_container_width=True, height=400)
        
        # ------------------------------------------
        # CRIANDO O EXCEL COMPLETO COM CONGELAMENTO E LINHAS TOTAIS
        # ------------------------------------------
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            cor_cabecalho = "#1F4E78" 
            
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
            
            if is_sac:
                valor_prestacao_destaque = df_escolhido.iloc[0]['Prestação (R$)']
                label_prestacao = "1ª Prestação SAC"
            else:
                valor_prestacao_destaque = df_escolhido.iloc[0]['Prestação (R$)']
                label_prestacao = "Prestação Mensal Fixa (Price)"

            dados_resumo = [
                ("Corretor Responsável", nome_corretor),
                ("WhatsApp de Contato", telefone),
                ("Sistema Selecionado", nome_sistema_escolhido),
                ("Valor Total do Imóvel", valor_imovel),
                ("Valor da Entrada", entrada),
                ("Valor Financiado", valor_financiado),
                ("Prazo Total", f"{meses} Meses ({meses//12} Anos)"),
                ("Taxa de Juros Anual", f"{taxa_juros}% a.a."),
                (label_prestacao, valor_prestacao_destaque)
            ]
            
            linha = 3
            for item, valor in dados_resumo:
                ws_resumo.write(linha, 0, item, fmt_destaque_chave)
                if isinstance(valor, (int, float)):
                    ws_resumo.write(linha, 1, valor, fmt_destaque_valor)
                else:
                    ws_resumo.write(linha, 1, str(valor), fmt_destaque_chave)
                linha += 1

            # --- ABA 2: FLUXO MÊS A MÊS COMPLETO ---
            nome_aba_fluxo = "Fluxo SAC" if is_sac else "Fluxo Price"
            ws_fluxo = workbook.add_worksheet(nome_aba_fluxo)
            
            # Congela a primeira linha para o cabeçalho ficar sempre visível ao rolar os meses
            ws_fluxo.freeze_panes(1, 0)
            
            cabecalhos = ["Mês", "Período", "Prestação (R$)", "Amortização (R$)", "Juros (R$)", "Saldo Devedor (R$)"]
            
            for col_num, cabecalho in enumerate(cabecalhos):
                ws_fluxo.write(0, col_num, cabecalho, fmt_cabecalho_tabela)
                
            ws_fluxo.set_column('A:A', 10)
            ws_fluxo.set_column('B:B', 14)
            ws_fluxo.set_column('C:F', 22)
            
            # Escreve todas as linhas de 1 até o último mês escolhido
            for row_idx, linha_dados in enumerate(dados_financiamento, start=1):
                ws_fluxo.write(row_idx, 0, linha_dados["Mês"], fmt_celula)
                ws_fluxo.write(row_idx, 1, linha_dados["Ano"], fmt_celula)
                ws_fluxo.write(row_idx, 2, linha_dados["Prestação (R$)"], fmt_moeda)
                ws_fluxo.write(row_idx, 3, linha_dados["Amortização (R$)"], fmt_moeda)
                ws_fluxo.write(row_idx, 4, linha_dados["Juros (R$)"], fmt_moeda)
                ws_fluxo.write(row_idx, 5, linha_dados["Saldo Devedor (R$)"], fmt_moeda)

        # Botão de Download atualizado
        st.download_button(
            label=f"📥 Baixar Planilha Completa ({meses} Meses) - {nome_sistema_escolhido}",
            data=buffer.getvalue(),
            file_name=f"Proposta_{nome_sistema_escolhido.replace(' ', '_')}_{meses}Meses.xlsx",
            mime="application/vnd.ms-excel"
        )

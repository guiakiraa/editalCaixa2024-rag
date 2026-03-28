import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
from chain import ask

st.set_page_config(
    page_title="Assistente de Edital",
    page_icon="📄",
    layout="centered",
)

st.markdown("""
<style>
    .main { background-color: #0f1117; }

    .header-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 1.5rem 0 0.5rem 0;
    }
    .header-icon { font-size: 2.5rem; }
    .header-text h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
    }
    .header-text p {
        margin: 2px 0 0 0;
        font-size: 0.82rem;
        color: #8b8fa8;
        letter-spacing: 0.01em;
    }
    .divider {
        border: none;
        border-top: 1px solid #2a2d3e;
        margin: 0.75rem 0 1.5rem 0;
    }
    .chat-message-user {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 1rem;
    }
    .chat-message-assistant {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 1rem;
    }
    .bubble-user {
        background-color: #2563eb;
        color: #ffffff;
        padding: 0.75rem 1.1rem;
        border-radius: 18px 18px 4px 18px;
        max-width: 75%;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .bubble-assistant {
        background-color: #1e2130;
        color: #e2e8f0;
        padding: 0.75rem 1.1rem;
        border-radius: 18px 18px 18px 4px;
        max-width: 75%;
        font-size: 0.95rem;
        line-height: 1.5;
        border: 1px solid #2a2d3e;
    }
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        flex-shrink: 0;
    }
    .avatar-assistant {
        background-color: #2563eb;
        margin-right: 10px;
        margin-top: 4px;
    }
    .avatar-user {
        background-color: #374151;
        margin-left: 10px;
        margin-top: 4px;
    }
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #4b5563;
    }
    .empty-state .icon { font-size: 3rem; margin-bottom: 1rem; }
    .empty-state h3 { color: #6b7280; font-weight: 500; margin-bottom: 0.5rem; }
    .empty-state p { font-size: 0.875rem; color: #4b5563; }
    .stButton > button {
        background-color: #1e2130 !important;
        border: 1px solid #2a2d3e !important;
        border-radius: 12px !important;
        color: #9ca3af !important;
        font-size: 0.8rem !important;
        padding: 0.6rem 0.9rem !important;
        width: 100% !important;
        text-align: left !important;
        transition: border-color 0.2s !important;
    }
    .stButton > button:hover {
        border-color: #2563eb !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)


# Header
st.markdown("""
<div class="header-container">
    <div class="header-icon">📄</div>
    <div class="header-text">
        <h1>Assistente de Edital</h1>
        <p>Concurso Público · Caixa Econômica Federal · Engenheiro de Segurança do Trabalho e Médico do Trabalho · 2024</p>
    </div>
</div>
<hr class="divider"/>
""", unsafe_allow_html=True)


# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending" not in st.session_state:
    st.session_state.pending = None


def render_message(msg: dict):
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="chat-message-user">
            <div class="bubble-user">{msg["content"]}</div>
            <div class="avatar avatar-user">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message-assistant">
            <div class="avatar avatar-assistant">🤖</div>
            <div class="bubble-assistant">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)


def submit(pergunta: str):
    st.session_state.messages.append({"role": "user", "content": pergunta})
    st.session_state.pending = pergunta


# Render chat history or empty state
if not st.session_state.messages and st.session_state.pending is None:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">💬</div>
        <h3>Nenhuma conversa ainda</h3>
        <p>Faça uma pergunta sobre o edital para começar</p>
    </div>
    """, unsafe_allow_html=True)

    suggestions = [
        "Qual o valor total do edital?",
        "Quais são os requisitos para participar?",
        "Qual o prazo de inscrição?",
        "Como é feita a avaliação?",
    ]

    col1, col2 = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(suggestion, key=f"suggestion_{i}"):
                submit(suggestion)
                st.rerun()
else:
    for msg in st.session_state.messages:
        render_message(msg)

    # Se há uma pergunta pendente, mostra o spinner logo abaixo da mensagem do usuário
    if st.session_state.pending:
        with st.spinner("Buscando no documento..."):
            response = ask(st.session_state.pending)
        st.session_state.pending = None
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()


# Chat input
user_input = st.chat_input("Digite sua pergunta sobre o edital...")

if user_input:
    submit(user_input)
    st.rerun()


# Clear button
if st.session_state.messages:
    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("🗑️ Limpar conversa", key="clear"):
        st.session_state.messages = []
        st.rerun()

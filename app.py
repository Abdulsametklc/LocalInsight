import streamlit as st
from modules.database import (
    init_db, log_message_db,
    save_document, get_all_documents, get_document_by_id,
    get_all_summaries, get_summaries_by_document,
    get_all_flashcards, get_flashcards_for_review, update_flashcard_review,
    get_all_quiz_questions, get_random_quiz, log_quiz_result,
    get_learning_stats
)
from modules.auth import init_auth_db, register_user, login_user, get_user_by_id
from modules.document_handler import get_document_text, get_combined_text
from modules.rag_engine import create_vector_db, get_ai_response, get_quick_answer
from modules.study_tools import generate_summary, generate_flashcards, generate_quiz, generate_study_material

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="LocalInsights", 
    page_icon="logo.png", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Configuration ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stAppViewContainer"] {
        background: #0a0a0a;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: #111111;
        border-right: 1px solid #1a1a1a;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: #ffffff;
    }
    
    /* Chat Interface Styling */
    .stChatMessage {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 25px !important;
    }
    
    [data-testid="stChatMessageContent"] {
        background: #161616 !important;
        border: 1px solid #222 !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        color: #e0e0e0 !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
    }
    
    [data-testid="stChatMessageAvatarAssistant"], 
    [data-testid="stChatMessageAvatarUser"] {
        display: none !important;
    }
    
    [data-testid="stChatMessage"] > div {
        padding-left: 0 !important;
    }
    
    /* Chat Input & Model Selector Alignment */
    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 30px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 100% !important;
        max-width: 800px !important;
        z-index: 999 !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    [data-testid="stChatInput"] > div {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        border-radius: 16px !important; 
        padding: 10px 15px 50px 15px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.6) !important;
    }

    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
        caret-color: #fff !important;
    }
     
    [data-testid="stChatInput"] button {
        background-color: #2a2a2a !important;
        color: #fff !important;
        border-radius: 50% !important;
        bottom: 15px !important;
        right: 15px !important;
        width: 34px !important;
        height: 34px !important;
    }
    [data-testid="stChatInput"] button:hover {
        background-color: #444 !important;
    }

    .model-selector-wrapper {
        position: fixed !important;
        bottom: 45px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 100% !important;
        max-width: 800px !important;
        z-index: 1000 !important;
        pointer-events: none !important;
        height: 50px;
        display: flex;
        align-items: center;
        padding-left: 20px;
    }

    div[data-testid="stChatModel"] {
        pointer-events: auto !important;
        width: 150px !important;
    }
    
    div[data-testid="stChatModel"] > div > div {
        background: transparent !important;
        border: none !important;
    }
    div[data-testid="stChatModel"] [data-baseweb="select"] {
        background: transparent !important;
    }
    div[data-testid="stChatModel"] [data-baseweb="select"] > div {
        background: transparent !important;
        color: #ddd !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    div[data-testid="stChatModel"] [data-baseweb="icon"] {
        color: #666 !important;
    }
    div[data-testid="stChatModel"] label {
        display: none !important;
    }
    
    /* General UI Components */
    .stButton > button {
        background: #ffffff;
        color: #000000;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #e0e0e0;
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #1a1a1a;
        border: 1px solid #252525;
        border-radius: 8px;
        color: white;
    }
    .stTextInput > div > div > input:focus {
        border-color: #fff;
    }
    
    [data-testid="stSelectbox"] > div > div {
        background: #1a1a1a;
        border: 1px solid #252525;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        gap: 0;
        border-bottom: 1px solid #252525;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 0;
        color: #666;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: 12px 24px;
        font-weight: 500;
        font-size: 0.9rem;
        letter-spacing: 0.02em;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #ffffff !important;
        border-bottom: 2px solid #ffffff !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #aaa;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #ffffff !important;
    }
    .stTabs [data-baseweb="tab-border"] {
        background-color: transparent !important;
    }
    
    .flashcard {
        background: #1a1a1a;
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        min-height: 180px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1em;
        border: 1px solid #333;
    }
    .flashcard-answer {
        background: #1a1a1a;
        border: 1px solid #4ade80;
    }
    
    .streamlit-expanderHeader {
        background: #1a1a1a;
        border-radius: 8px;
    }
    
    [data-testid="stMetric"] {
        background: #1a1a1a;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    
    [data-testid="stFileUploader"] {
        background: #1a1a1a;
        border-radius: 10px;
        border: 1px dashed #333;
    }
    
    .stProgress > div > div {
        background: #333;
    }
    .stProgress > div > div > div {
        background: #fff;
    }
    
    hr {
        border-color: #333;
    }
</style>
""", unsafe_allow_html=True)

# Veritabanlarını başlat
init_db()
init_auth_db()

def render_login_page():
    """Giriş/Kayıt sayfasını oluşturur - Minimalist tasarım."""
    
    # Login Page Specific CSS
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] {
            background: #0a0a0a;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        .brand-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #ffffff;
            text-align: center;
            margin-bottom: 5px;
            margin-top: 10px;
        }
        .brand-subtitle {
            color: rgba(255, 255, 255, 0.5);
            text-align: center;
            font-size: 0.9rem;
            margin-bottom: 25px;
        }
        .stTextInput > div > div > input {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            color: white;
            padding: 12px 15px;
        }
        .stTextInput > div > div > input:focus {
            border-color: #fff;
            box-shadow: none;
        }
        .stButton > button {
            background: #ffffff;
            color: #000000;
            border: none;
            border-radius: 8px;
            padding: 12px 30px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .stButton > button:hover {
            background: #e0e0e0;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background: #1a1a1a;
            border-radius: 8px;
            color: rgba(255, 255, 255, 0.6);
            padding: 10px 25px;
            border: 1px solid #333;
        }
        .stTabs [aria-selected="true"] {
            background: #ffffff;
            color: #000000;
        }
        div[data-testid="stForm"] {
            background: transparent;
            border: none;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Center layout
    col1, col2, col3 = st.columns([1.3, 1, 1.3])
    
    with col2:
        # Logo SVG
        st.markdown('''
            <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px;">
                <svg width="60" height="60" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <!-- L harfi -->
                    <path d="M15 10 L15 90 L50 90" stroke="#ffffff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    <!-- I harfi -->
                    <line x1="75" y1="10" x2="75" y2="90" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
                </svg>
            </div>
        ''', unsafe_allow_html=True)
        
        # Başlık
        st.markdown('<p class="brand-title">LocalInsights</p>', unsafe_allow_html=True)
        st.markdown('<p class="brand-subtitle">Akıllı Çalışma Asistanınız</p>', unsafe_allow_html=True)
        
        # Sekmeler
        tab1, tab2 = st.tabs(["Giriş", "Kayıt"])
        
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="ornek@email.com", label_visibility="collapsed")
                password = st.text_input("Şifre", type="password", placeholder="Şifreniz", label_visibility="collapsed")
                
                st.markdown("")
                submit = st.form_submit_button("Giriş Yap", use_container_width=True)
                
                if submit:
                    if email and password:
                        success, message, user_data = login_user(email, password)
                        if success:
                            st.session_state['logged_in'] = True
                            st.session_state['user'] = user_data
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Email ve şifre gerekli.")
        
        with tab2:
            with st.form("register_form", clear_on_submit=False):
                full_name = st.text_input("Ad Soyad", placeholder="Adınız Soyadınız", key="reg_name", label_visibility="collapsed")
                new_email = st.text_input("Email", placeholder="ornek@email.com", key="reg_email", label_visibility="collapsed")
                new_password = st.text_input("Şifre", type="password", placeholder="En az 6 karakter", key="reg_pass", label_visibility="collapsed")
                confirm_password = st.text_input("Şifre Tekrar", type="password", placeholder="Şifrenizi tekrar girin", key="reg_confirm", label_visibility="collapsed")
                
                st.markdown("")
                register = st.form_submit_button("Hesap Oluştur", use_container_width=True)
                
                if register:
                    if not full_name or not new_email or not new_password:
                        st.warning("Tüm alanları doldurun.")
                    elif len(new_password) < 6:
                        st.warning("Şifre en az 6 karakter olmalı.")
                    elif new_password != confirm_password:
                        st.error("Şifreler eşleşmiyor.")
                    elif "@" not in new_email:
                        st.error("Geçerli bir email girin.")
                    else:
                        success, message, user_id = register_user(new_email, new_password, full_name)
                        if success:
                            st.success("Hesap oluşturuldu! Giriş yapabilirsiniz.")
                        else:
                            st.error(message)
        
        # Alt bilgi
        st.markdown("")
        st.markdown("")
        st.markdown(
            '<p style="text-align: center; color: rgba(255,255,255,0.3); font-size: 0.8rem;">Verileriniz güvenle saklanır</p>',
            unsafe_allow_html=True
        )


def render_sidebar():
    """Yan menüyü oluşturur."""
    with st.sidebar:
        # Kullanıcı bilgisi
        user = st.session_state.get('user', {})
        st.markdown(f"**{user.get('name', 'Kullanıcı')}**")
        
        # Dosya yükleme
        st.divider()
        st.markdown("**Dosya Yükle**")
        uploaded_files = st.file_uploader(
            "PDF veya Word dosyaları",
            accept_multiple_files=True, 
            type=["pdf", "docx", "doc"],
            help="Çalışma materyallerinizi yükleyin"
        )
        
        if uploaded_files:
            st.session_state['uploaded_files'] = uploaded_files
            
            # Model seçimi
            selected_model = st.selectbox(
                "Model", 
                ["llama3", "phi3", "mistral", "gemma"],
                label_visibility="collapsed"
            )
            st.session_state['selected_model'] = selected_model
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yükle", use_container_width=True):
                    with st.spinner("Dosyalar işleniyor..."):
                        documents = get_document_text(uploaded_files)
                        for doc in documents:
                            doc_id = save_document(
                                doc['filename'], 
                                doc['content'], 
                                doc['doc_type']
                            )
                            st.session_state[f'doc_{doc_id}_content'] = doc['content']
                        
                        # Vektör veritabanı oluştur
                        combined_text = get_combined_text(uploaded_files)
                        if combined_text:
                            st.session_state['vectorstore'] = create_vector_db(combined_text)
                            st.success(f"{len(documents)} dosya yüklendi")
            
            with col2:
                if st.button("Materyal Oluştur", use_container_width=True):
                    with st.spinner("AI materyaller oluşturuyor..."):
                        documents = get_document_text(uploaded_files)
                        for doc in documents:
                            doc_id = save_document(
                                doc['filename'], 
                                doc['content'], 
                                doc['doc_type']
                            )
                            results = generate_study_material(
                                doc['content'],
                                doc_id,
                                selected_model,
                                generate_summary_=True,
                                flashcard_count=10,
                                quiz_count=10
                            )
                        st.success("Materyaller oluşturuldu")
                        st.rerun()
        
        # Çıkış butonu - en altta
        st.divider()
        st.markdown("")
        st.markdown("")
        if st.button("Çıkış Yap", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user'] = None
            st.session_state['messages'] = []
            st.rerun()

def render_chat_tab(model_name):
    """Sohbet sekmesini oluşturur."""
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Mesajları göster
    chat_container = st.container()
    with chat_container:
        st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True) 
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        st.markdown('<div style="margin-bottom: 150px;"></div>', unsafe_allow_html=True)
    
    # Model Selector Wrapper
    st.markdown('<div class="model-selector-wrapper">', unsafe_allow_html=True)
    
    st.selectbox(
        "Model",
        ["llama3", "phi3", "mistral", "gemma"],
        label_visibility="collapsed",
        key="chat_model"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Giriş alanı
    if prompt := st.chat_input("Ask anything (Ctrl+L), @ to mention, / for workflows"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_message_db("user", prompt)
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner(""):
                    if "vectorstore" in st.session_state:
                        ai_msg, docs = get_ai_response(
                            selected_model, 
                            st.session_state.vectorstore, 
                            prompt,
                            st.session_state.messages
                        )
                        st.markdown(ai_msg)
                        
                        if docs:
                            with st.expander("Kaynaklar"):
                                for i, doc in enumerate(docs):
                                    st.caption(f"**Kaynak {i+1}:** {doc.page_content[:300]}...")
                    else:
                        ai_msg = get_quick_answer(selected_model, prompt)
                        st.markdown(ai_msg)
                
                st.session_state.messages.append({"role": "assistant", "content": ai_msg})
                log_message_db("assistant", ai_msg)
        st.rerun()

def render_summary_tab(model_name):
    """Özet sekmesini oluşturur."""
    st.markdown("**Özetler**")
    
    summaries = get_all_summaries()
    
    if summaries:
        st.markdown("Kayıtlı Özetler")
        for summary in summaries:
            with st.expander(f"{summary[1]} - {summary[3][:10]}"):
                st.markdown(summary[2])
    else:
        st.info("Henüz özet oluşturulmamış. Sol menüden dosya yükleyip 'Materyal' butonuna basın.")
    
    st.divider()
    st.markdown("**Yeni Özet Oluştur**")
    
    documents = get_all_documents()
    if documents:
        doc_options = {f"{doc[1]} ({doc[3][:10]})": doc[0] for doc in documents}
        selected_doc = st.selectbox("Doküman seçin:", list(doc_options.keys()))
        
        if st.button("Özet Oluştur"):
            doc_id = doc_options[selected_doc]
            doc_data = get_document_by_id(doc_id)
            
            with st.spinner("Özet oluşturuluyor..."):
                summary = generate_summary(doc_data[2], model_name)
                from modules.database import save_summary
                save_summary(doc_id, summary)
                st.success("Özet oluşturuldu!")
                st.markdown(summary)

def render_quiz_tab(model_name):
    """Sınav sekmesini oluşturur."""
    st.markdown("**Sınav**")
    
    if 'quiz_state' not in st.session_state:
        st.session_state.quiz_state = {
            'active': False,
            'questions': [],
            'current_index': 0,
            'score': 0,
            'answered': False
        }
    
    quiz_state = st.session_state.quiz_state
    
    if not quiz_state['active']:
        st.markdown("**Yeni Sınav Başlat**")
        
        documents = get_all_documents()
        all_questions = get_all_quiz_questions()
        
        if all_questions:
            col1, col2 = st.columns(2)
            with col1:
                question_count = st.slider("Soru sayısı:", 5, min(20, len(all_questions)), 10)
            with col2:
                doc_filter = st.selectbox("Doküman:", ["Tümü"] + [doc[1] for doc in documents])
            
            if st.button("🚀 Sınava Başla", type="primary"):
                if doc_filter == "Tümü":
                    questions = get_random_quiz(count=question_count)
                else:
                    doc_id = next((doc[0] for doc in documents if doc[1] == doc_filter), None)
                    questions = get_random_quiz(document_id=doc_id, count=question_count)
                
                if questions:
                    quiz_state['active'] = True
                    quiz_state['questions'] = questions
                    quiz_state['current_index'] = 0
                    quiz_state['score'] = 0
                    quiz_state['answered'] = False
                    st.rerun()
        else:
            st.info("Henüz soru yok. Sol menüden dosya yükleyip 'Materyal' butonuna basın.")
    else:
        questions = quiz_state['questions']
        idx = quiz_state['current_index']
        
        if idx < len(questions):
            q = questions[idx]
            q_id, q_type, q_text, options_str, correct, explanation = q
            
            st.progress((idx + 1) / len(questions), text=f"Soru {idx + 1}/{len(questions)}")
            st.subheader(f"{q_text}")
            
            if options_str:
                options = options_str.split('|||')
                for i, opt in enumerate(options):
                    if quiz_state['answered']:
                        if opt == correct:
                            st.success(f"{opt}")
                        elif st.session_state.get(f'selected_{idx}') == opt:
                            st.error(f"{opt}")
                        else:
                            st.write(f"⬜ {opt}")
                    else:
                        if st.button(opt, key=f"opt_{idx}_{i}", use_container_width=True):
                            st.session_state[f'selected_{idx}'] = opt
                            quiz_state['answered'] = True
                            if opt == correct:
                                quiz_state['score'] += 1
                                log_quiz_result(q_id, True)
                            else:
                                log_quiz_result(q_id, False)
                            st.rerun()
            
            if quiz_state['answered']:
                if explanation:
                    st.info(f"{explanation}")
                if st.button("Sonraki"):
                    quiz_state['current_index'] += 1
                    quiz_state['answered'] = False
                    st.rerun()
        else:
            st.balloons()
            st.success("Sınav Tamamlandı")
            score = quiz_state['score']
            total = len(questions)
            st.metric("Puan", f"{score}/{total} (%{score/total*100:.0f})")
            
            if st.button("Yeni Sınav"):
                st.session_state.quiz_state = {'active': False, 'questions': [], 'current_index': 0, 'score': 0, 'answered': False}
                st.rerun()

def render_flashcard_tab(model_name):
    """Flashcard sekmesini oluşturur."""
    st.markdown("**Bilgi Kartları**")
    
    if 'fc_state' not in st.session_state:
        st.session_state.fc_state = {'active': False, 'cards': [], 'idx': 0, 'show': False}
    
    fc = st.session_state.fc_state
    
    tab1, tab2 = st.tabs(["Calıs", "Tüm Kartlar"])
    
    with tab1:
        if not fc['active']:
            review_cards = get_flashcards_for_review(limit=20)
            st.metric("Tekrar Bekleyen", len(review_cards))
            
            if review_cards:
                count = st.slider("Kart sayısı:", 5, min(20, len(review_cards)), 10)
                if st.button("Başla", type="primary"):
                    fc['active'] = True
                    fc['cards'] = review_cards[:count]
                    fc['idx'] = 0
                    fc['show'] = False
                    st.rerun()
            else:
                st.info("Tekrar edilecek kart yok. Sol menüden materyal oluşturun.")
        else:
            cards = fc['cards']
            idx = fc['idx']
            
            if idx < len(cards):
                card = cards[idx]
                card_id, filename, question, answer, difficulty, times = card
                
                st.progress((idx + 1) / len(cards), text=f"Kart {idx + 1}/{len(cards)}")
                
                if not fc['show']:
                    st.markdown(f"""<div class="flashcard"><h3>{question}</h3></div>""", unsafe_allow_html=True)
                    if st.button("Cevabı Göster", use_container_width=True):
                        fc['show'] = True
                        st.rerun()
                else:
                    st.markdown(f"""<div class="flashcard" style="border-color: #4ade80;"><h3>{answer}</h3></div>""", unsafe_allow_html=True)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Bilmiyordum", use_container_width=True):
                            update_flashcard_review(card_id, False)
                            fc['idx'] += 1
                            fc['show'] = False
                            st.rerun()
                    with c2:
                        if st.button("Biliyordum", use_container_width=True):
                            update_flashcard_review(card_id, True)
                            fc['idx'] += 1
                            fc['show'] = False
                            st.rerun()
            else:
                st.balloons()
                st.success(f"{len(cards)} kartı tamamladınız")
                if st.button("Tekrar"):
                    fc['active'] = False
                    st.rerun()
    
    with tab2:
        all_cards = get_all_flashcards()
        if all_cards:
            for c in all_cards:
                with st.expander(f"{c[1]} | {c[2][:40]}..."):
                    st.write(f"**S:** {c[2]}")
                    st.write(f"**C:** {c[3]}")

def main():
    """Ana uygulama."""
    # Giriş kontrolü
    if not st.session_state.get('logged_in', False):
        render_login_page()
        return
    
    # Yan menü
    render_sidebar()
    
    # Varsayılan model
    model = st.session_state.get('selected_model', 'llama3')
    
    # Ana sekmeler
    tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Özet", "Sınav", "Kartlar"])
    
    with tab1:
        render_chat_tab(model)
    with tab2:
        render_summary_tab(model)
    with tab3:
        render_quiz_tab(model)
    with tab4:
        render_flashcard_tab(model)

if __name__ == "__main__":
    main()
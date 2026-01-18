import streamlit as st

# New multi-tenant ready modules
from modules.db import init_db
from modules.auth import (
    login, register, is_logged_in, get_current_user_id, 
    get_current_user, set_session, clear_session
)
from modules.repo_chat import (
    create_conversation, list_conversations, get_conversation,
    create_message, get_messages, log_model_call
)
from modules.repo_documents import (
    create_document, get_documents, get_document, delete_document,
    create_summary, get_summaries,
    create_flashcards_bulk, get_flashcards, get_flashcards_for_review, update_flashcard_review,
    create_quiz_questions_bulk, get_quiz_questions, get_random_quiz, log_quiz_result,
    get_learning_stats
)

# Other modules
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
    
    /* Chat Input - Modern Single Color Design */
    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 25px !important;
        left: calc(50% + 120px) !important;
        transform: translateX(-50%) !important;
        width: calc(100% - 280px) !important;
        max-width: 700px !important;
        z-index: 999 !important;
        background: transparent !important;
        border: none !important;
        padding: 0 20px !important;
    }
    
    /* Force ALL elements inside chat input to same color */
    [data-testid="stChatInput"] * {
        background-color: #1a1a1e !important;
        border-color: #1a1a1e !important;
    }
    
    [data-testid="stChatInput"] > div {
        border: 1px solid #333 !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
        padding: 4px 12px !important;
        background: #1a1a1e !important;
    }

    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        border: none !important;
        color: #e0e0e0 !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        caret-color: #fff !important;
        padding: 10px 4px !important;
    }
    
    [data-testid="stChatInput"] textarea::placeholder {
        color: #555 !important;
    }
     
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #5a5a60 0%, #3a3a40 100%) !important;
        color: #fff !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stChatInput"] button:hover {
        background: linear-gradient(135deg, #6a6a70 0%, #4a4a50 100%) !important;
        transform: scale(1.05) !important;
    }

    /* Sidebar - Modern styling */
    [data-testid="stSidebar"] {
        background: #0a0a0c !important;
        border-right: 1px solid #222 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stSelectbox"] > div {
        background: #1a1a1e !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stFileUploader"] > div {
        background: #1a1a1e !important;
        border: 1px dashed #444 !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stFileUploader"] label {
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
                        user = login(email, password)
                        if user:
                            set_session(user)  # user_id, user dict, logged_in
                            st.rerun()
                        else:
                            st.error("Email veya şifre hatalı.")  # Generic - enumeration koruması
                    else:
                        st.warning("Email ve şifre gerekli.")
        
        with tab2:
            with st.form("register_form", clear_on_submit=False):
                full_name = st.text_input("Ad Soyad", placeholder="Adınız Soyadınız", key="reg_name", label_visibility="collapsed")
                new_email = st.text_input("Email", placeholder="ornek@email.com", key="reg_email", label_visibility="collapsed")
                new_password = st.text_input("Şifre", type="password", placeholder="En az 6 karakter", key="reg_pass", label_visibility="collapsed")
                confirm_password = st.text_input("Şifre Tekrar", type="password", placeholder="Şifrenizi tekrar girin", key="reg_confirm", label_visibility="collapsed")
                
                st.markdown("")
                register_submit = st.form_submit_button("Hesap Oluştur", use_container_width=True)
                
                if register_submit:
                    if not full_name or not new_email or not new_password:
                        st.warning("Tüm alanları doldurun.")
                    elif len(new_password) < 6:
                        st.warning("Şifre en az 6 karakter olmalı.")
                    elif new_password != confirm_password:
                        st.error("Şifreler eşleşmiyor.")
                    elif "@" not in new_email:
                        st.error("Geçerli bir email girin.")
                    else:
                        user_id = register(new_email, new_password, full_name)
                        if user_id:
                            st.success("Hesap oluşturuldu! Giriş yapabilirsiniz.")
                        else:
                            st.error("Bu email zaten kayıtlı.")
        
        # Alt bilgi
        st.markdown("")
        st.markdown("")
        st.markdown(
            '<p style="text-align: center; color: rgba(255,255,255,0.3); font-size: 0.8rem;">Verileriniz güvenle saklanır</p>',
            unsafe_allow_html=True
        )


def render_sidebar():
    """Yan menuyu olusturur - Modern tasarim."""
    with st.sidebar:
        # Kullanici bilgisi
        user = st.session_state.get('user', {})
        st.markdown(f"**{user.get('name', 'Kullanici')}**")
        
        st.markdown("")
        
        # Model secimi - sidebar'da
        st.markdown("##### Model")
        model_list = ["qwen2.5:7b", "gemma2:9b", "llama3.1:8b", "mistral", "llama3"]
        model_names = ["Qwen 2.5", "Gemma 2", "Llama 3.1", "Mistral", "Llama 3"]
        
        if 'current_model_id' not in st.session_state:
            st.session_state.current_model_id = 'qwen2.5:7b'
        
        current_idx = model_list.index(st.session_state.current_model_id) if st.session_state.current_model_id in model_list else 0
        selected_name = st.selectbox(
            "Model Sec",
            model_names,
            index=current_idx,
            label_visibility="collapsed"
        )
        st.session_state.current_model_id = model_list[model_names.index(selected_name)]
        st.session_state['selected_model'] = st.session_state.current_model_id
        
        st.markdown("")
        
        # Dosya yukleme - minimal
        st.markdown("##### Dosya")
        uploaded_files = st.file_uploader(
            "yukle",
            accept_multiple_files=True, 
            type=["pdf", "docx", "doc"],
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            st.session_state['uploaded_files'] = uploaded_files
            user_id = get_current_user_id()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yukle", use_container_width=True):
                    with st.spinner(""):
                        documents = get_document_text(uploaded_files)
                        for doc in documents:
                            doc_id = create_document(
                                doc['filename'], 
                                doc['content'], 
                                doc['doc_type'],
                                user_id=user_id
                            )
                            st.session_state[f'doc_{doc_id}_content'] = doc['content']
                        
                        combined_text = get_combined_text(uploaded_files)
                        if combined_text:
                            # Vectorstore user_id ile cache'lenir
                            st.session_state['vectorstore'] = create_vector_db(combined_text)
                            st.session_state['vectorstore_user_id'] = user_id  # Izolasyon icin
                            st.success(f"{len(documents)} dosya")
            
            with col2:
                if st.button("Materyal", use_container_width=True):
                    with st.spinner(""):
                        documents = get_document_text(uploaded_files)
                        for doc in documents:
                            doc_id = create_document(
                                doc['filename'], 
                                doc['content'], 
                                doc['doc_type'],
                                user_id=user_id
                            )
                            results = generate_study_material(
                                doc['content'],
                                doc_id,
                                st.session_state.current_model_id,
                                generate_summary_=True,
                                flashcard_count=10,
                                quiz_count=10,
                                user_id=user_id  # Materyaller user_id ile kaydedilecek
                            )
                        st.success("Tamam")
                        st.rerun()
        
        # Bosluk
        st.markdown("")
        st.markdown("")
        st.markdown("")
        
        # Cikis butonu
        if st.button("Çıkış Yap", use_container_width=True):
            clear_session()  # Guvenli cikis - tum user verilerini ve cache'leri temizler
            st.rerun()

def render_chat_tab(model_name):
    """Sohbet sekmesini olusturur - Custom HTML ile."""
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Custom Chat CSS
    st.markdown("""
    <style>
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 20px 0;
        max-width: 800px;
        margin: 0 auto;
        padding-bottom: 120px;
    }
    .chat-message {
        display: flex;
        width: 100%;
    }
    .chat-message.user {
        justify-content: flex-end;
    }
    .chat-message.assistant {
        justify-content: flex-start;
    }
    .message-bubble {
        max-width: 70%;
        padding: 12px 18px;
        border-radius: 18px;
        font-size: 0.95rem;
        line-height: 1.5;
        word-wrap: break-word;
    }
    .message-bubble.user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;
        border-radius: 18px 18px 4px 18px;
    }
    .message-bubble.assistant {
        background: #1e1e24;
        color: #e0e0e0;
        border: 1px solid #2a2a30;
        border-radius: 18px 18px 18px 4px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Mesajlari custom HTML ile goster - her mesaj ayri render
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"].replace("\n", "<br>")
        
        if role == "user":
            st.markdown(f'''
            <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: #fff; padding: 12px 18px; border-radius: 18px 18px 4px 18px; 
                            max-width: 70%; font-size: 0.95rem; line-height: 1.5;">
                    {content}
                </div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div style="display: flex; justify-content: flex-start; margin-bottom: 12px;">
                <div style="background: #1e1e24; color: #e0e0e0; 
                            border: 1px solid #2a2a30; padding: 12px 18px; 
                            border-radius: 18px 18px 18px 4px; max-width: 70%; 
                            font-size: 0.95rem; line-height: 1.5;">
                    {content}
                </div>
            </div>
            ''', unsafe_allow_html=True)
    
    # Alt bosluk
    st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
    
    # Giris alani (Streamlit native - bunu degistiremiyoruz)
    if prompt := st.chat_input("Mesajinizi yazin..."):
        user_id = get_current_user_id()
        if not user_id:
            st.error("Oturum gecersiz. Lutfen tekrar giris yapin.")
            st.stop()
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Conversation yoksa olustur
        if 'conversation_id' not in st.session_state:
            conv_id = create_conversation(user_id=user_id, title=prompt[:50])
            st.session_state['conversation_id'] = conv_id
        
        # Mesaji kaydet
        create_message(
            st.session_state['conversation_id'], 
            "user", 
            prompt, 
            user_id=user_id
        )
        
        # AI yaniti al
        with st.spinner(""):
            if "vectorstore" in st.session_state:
                # Vectorstore user izolasyonu kontrol
                if st.session_state.get('vectorstore_user_id') != user_id:
                    st.warning("Bu vectorstore baska bir kullaniciya ait.")
                    st.stop()
                
                ai_msg, docs = get_ai_response(
                    st.session_state.current_model_id, 
                    st.session_state.vectorstore, 
                    prompt,
                    st.session_state.messages,
                    user_id=user_id  # Kisisellestirilmis hafiza icin
                )
                
                if docs:
                    with st.expander("Kaynaklar"):
                        for i, doc in enumerate(docs):
                            st.caption(f"**Kaynak {i+1}:** {doc.page_content[:300]}...")
            else:
                ai_msg = get_quick_answer(st.session_state.current_model_id, prompt, user_id=user_id)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_msg})
            
            # AI mesajini kaydet
            create_message(
                st.session_state['conversation_id'], 
                "assistant", 
                ai_msg, 
                user_id=user_id
            )
        st.rerun()

def render_summary_tab(model_name):
    """Özet sekmesini oluşturur."""
    user_id = get_current_user_id()
    if not user_id:
        st.error("Oturum gecersiz.")
        st.stop()
    
    st.markdown("**Özetler**")
    
    summaries = get_summaries(user_id=user_id)
    
    if summaries:
        st.markdown("Kayıtlı Özetler")
        for summary in summaries:
            with st.expander(f"{summary['filename']} - {str(summary['created_at'])[:10]}"):
                st.markdown(summary['summary_text'])
    else:
        st.info("Henüz özet oluşturulmamış. Sol menüden dosya yükleyip 'Materyal' butonuna basın.")
    
    st.divider()
    st.markdown("**Yeni Özet Oluştur**")
    
    documents = get_documents(user_id=user_id)
    if documents:
        doc_options = {f"{doc['filename']} ({str(doc['upload_date'])[:10]})": doc['id'] for doc in documents}
        selected_doc = st.selectbox("Doküman seçin:", list(doc_options.keys()))
        
        if st.button("Özet Oluştur"):
            doc_id = doc_options[selected_doc]
            doc_data = get_document(doc_id, user_id=user_id)
            
            if not doc_data:
                st.error("Dokuman bulunamadi veya erisim yetkiniz yok.")
                st.stop()
            
            with st.spinner("Özet oluşturuluyor..."):
                summary = generate_summary(doc_data['content'], model_name)
                create_summary(doc_id, summary, user_id=user_id)
                st.success("Özet oluşturuldu!")
                st.markdown(summary)

def render_quiz_tab(model_name):
    """Sınav sekmesini oluşturur."""
    user_id = get_current_user_id()
    if not user_id:
        st.error("Oturum gecersiz.")
        st.stop()
    
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
        
        documents = get_documents(user_id=user_id)
        all_questions = get_quiz_questions(user_id=user_id)
        
        if all_questions:
            col1, col2 = st.columns(2)
            with col1:
                question_count = st.slider("Soru sayısı:", 5, min(20, len(all_questions)), 10)
            with col2:
                doc_filter = st.selectbox("Doküman:", ["Tümü"] + [doc['filename'] for doc in documents])
            
            if st.button("🚀 Sınava Başla", type="primary"):
                if doc_filter == "Tümü":
                    questions = get_random_quiz(user_id=user_id, count=question_count)
                else:
                    doc_id = next((doc['id'] for doc in documents if doc['filename'] == doc_filter), None)
                    questions = get_random_quiz(user_id=user_id, document_id=doc_id, count=question_count)
                
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
            # Dict access - yeni repo fonksiyonlari dict doner
            q_id = q['id']
            q_type = q['question_type']
            q_text = q['question_text']
            options_str = q.get('options', '')
            correct = q['correct_answer']
            explanation = q.get('explanation', '')
            
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
                                log_quiz_result(q_id, True, user_id=user_id)
                            else:
                                log_quiz_result(q_id, False, user_id=user_id)
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
    user_id = get_current_user_id()
    if not user_id:
        st.error("Oturum gecersiz.")
        st.stop()
    
    st.markdown("**Bilgi Kartları**")
    
    if 'fc_state' not in st.session_state:
        st.session_state.fc_state = {'active': False, 'cards': [], 'idx': 0, 'show': False}
    
    fc = st.session_state.fc_state
    
    tab1, tab2 = st.tabs(["Calıs", "Tüm Kartlar"])
    
    with tab1:
        if not fc['active']:
            review_cards = get_flashcards_for_review(user_id=user_id, limit=20)
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
                # Dict access - yeni repo fonksiyonlari dict doner
                card_id = card['id']
                filename = card.get('filename', '')
                question = card['question']
                answer = card['answer']
                difficulty = card.get('difficulty', 'orta')
                times = card.get('times_reviewed', 0)
                
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
                            update_flashcard_review(card_id, False, user_id=user_id)
                            fc['idx'] += 1
                            fc['show'] = False
                            st.rerun()
                    with c2:
                        if st.button("Biliyordum", use_container_width=True):
                            update_flashcard_review(card_id, True, user_id=user_id)
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
        all_cards = get_flashcards(user_id=user_id)
        if all_cards:
            for c in all_cards:
                with st.expander(f"{c.get('filename', 'Bilinmiyor')} | {c['question'][:40]}..."):
                    st.write(f"**S:** {c['question']}")
                    st.write(f"**C:** {c['answer']}")

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
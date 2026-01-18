"""
RAG Engine Module
Retrieval-Augmented Generation sistemi ve kişiselleştirme.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import os

# Vektör veritabanı kaydetme/yükleme yolu
VECTORSTORE_PATH = "data/vectorstore"

def create_vector_db(text, persist=False):
    """
    Metni vektörlere çevirir.
    
    Args:
        text: Vektörleştirilecek metin
        persist: Vektör veritabanını diske kaydet
    
    Returns:
        FAISS vectorstore
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=750, 
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_text(text)
    
    # Çok dilli embedding modeli - Türkçe için optimize edilmiş
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    vectorstore = FAISS.from_texts(texts=chunks, embedding=embeddings)
    
    # Kalıcı kayıt
    if persist:
        os.makedirs(VECTORSTORE_PATH, exist_ok=True)
        vectorstore.save_local(VECTORSTORE_PATH)
    
    return vectorstore

def load_vector_db():
    """Kayıtlı vektör veritabanını yükler."""
    if os.path.exists(VECTORSTORE_PATH):
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'}
        )
        return FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
    return None

def add_to_vector_db(text, existing_vectorstore=None):
    """Mevcut vektör veritabanına yeni metin ekler."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=750, 
        chunk_overlap=150
    )
    chunks = text_splitter.split_text(text)
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    if existing_vectorstore:
        # Mevcut veritabanına ekle
        existing_vectorstore.add_texts(chunks)
        return existing_vectorstore
    else:
        # Yeni oluştur
        return FAISS.from_texts(texts=chunks, embedding=embeddings)

def get_personalized_context(user_id: int = None):
    """Kişiselleştirme için kullanıcı bağlamı oluşturur.
    
    Args:
        user_id: Kullanıcı ID (multi-tenant için zorunlu)
    
    Returns:
        (user_profile, learning_context) tuple
    """
    if not user_id:
        return "Kullanıcı hakkında özel bilgi yok.", ""
    
    try:
        from .memory_engine import build_memory_context
        memory_context = build_memory_context(user_id)
        
        if memory_context:
            return memory_context, ""
        else:
            return "Kullanıcı hakkında özel bilgi yok.", ""
    except Exception as e:
        print(f"Memory context error: {e}")
        return "Kullanıcı hakkında özel bilgi yok.", ""

def get_ai_response(model_name, vectorstore, user_question, chat_history=None, user_id=None):
    """
    Ollama'ya soruyu sorar. Kişiselleştirilmiş yanıt döndürür.
    
    Args:
        model_name: Kullanılacak model (llama3, phi3, mistral vb.)
        vectorstore: FAISS vektör veritabanı
        user_question: Kullanıcının sorusu
        chat_history: Önceki sohbet geçmişi (opsiyonel)
        user_id: Kullanıcı ID (kişiselleştirme için)
    
    Returns:
        tuple: (AI yanıtı, kaynak dokümanlar)
    """
    try:
        # 1. Kişiselleştirme bilgilerini al (user_id ile)
        user_profile, learning_context = get_personalized_context(user_id=user_id)

        # 2. Benzer içerikleri bul
        docs = vectorstore.similarity_search(user_question, k=4)
        pdf_context = "\n\n".join([doc.page_content for doc in docs])
        
        # 3. Sohbet geçmişini hazırla
        history_text = ""
        if chat_history:
            recent_history = chat_history[-6:]  # Son 3 soru-cevap
            for msg in recent_history:
                role = "Kullanıcı" if msg["role"] == "user" else "Asistan"
                history_text += f"{role}: {msg['content'][:200]}\n"
        
        # 4. Gelişmiş prompt - Chain of Thought + Türkçe yanıt
        template = """Sen LocalInsights asistanısın - akıllı, yardımsever ve kişiselleştirilmiş bir eğitim asistanısın.

⚠️ DİL KURALI: SADECE TÜRKÇE YANIŞ VER. ASLA BAŞKA DİL KULLANMA. NO CHINESE. NO ENGLISH.

KULLANICI BİLGİLERİ:
{user_profile}

{learning_context}

DÖKÜMAN İÇERİĞİ:
{pdf_context}

{history_section}

KULLANICI SORUSU: {question}

DÜŞÜNCE SÜRECİ (Adım adım düşün):
1. Önce kullanıcının ne sorduğunu anla.
2. Döküman içeriğinde ilgili bilgileri bul.
3. Bilgiyi kullanıcının seviyesine uygun şekilde açıkla.
4. Emin olmadığın bilgileri "Bu konuda dokümanda bilgi bulamadım" diye belirt.

KRİTİK KURALLAR:
- ⚠️ SADECE TÜRKÇE YANIT VER. ÇİNCE, İNGİLİZCE VEYA BAŞKA DİL KULLANMA!
- SADECE DÖKÜMAN İÇERİĞİNDEKİ bilgileri kullan. Uydurma yapma.
- Bilgi dokümanda yoksa açıkça belirt.
- Yapılandırılmış ve anlaşılır yanıtlar ver.
- Kullanıcıya ismiyle hitap et (KULLANICI BİLGİLERİ'nden).

YANIT FORMAT:
- Kısa ve öz cevaplar ver.
- Gerekirse madde işaretleri kullan.
- Teknik terimleri açıkla.

🇹🇷 TÜRKÇE YANITINI VER (BAŞKA DİL YASAK):"""
        
        history_section = f"SON SOHBET GEÇMİŞİ:\n{history_text}" if history_text else ""
        
        prompt = ChatPromptTemplate.from_template(template)
        llm = ChatOllama(model=model_name, temperature=0.1)
        chain = prompt | llm
        
        response = chain.invoke({
            "user_profile": user_profile,
            "learning_context": learning_context,
            "pdf_context": pdf_context,
            "history_section": history_section,
            "question": user_question
        })
        
        return response.content, docs
        
    except Exception as e:
        return f"HATA: {e}", []

def get_quick_answer(model_name, question, user_id=None):
    """
    Doküman olmadan hızlı cevap verir.
    
    Args:
        model_name: Kullanılacak model
        question: Kullanıcının sorusu
        user_id: Kullanıcı ID (kişiselleştirme için)
    
    Returns:
        str: AI yanıtı
    """
    try:
        user_profile, _ = get_personalized_context(user_id=user_id)
        template = """Sen LocalInsights asistanısın - akıllı ve yardımsever bir eğitim asistanı.

⚠️ DİL KURALI: SADECE TÜRKÇE YANIT VER. ÇİNCE, İNGİLİZCE VEYA BAŞKA DİL ASLA KULLANMA!

KULLANICI BİLGİLERİ: {user_profile}

KULLANICI SORUSU: {question}

DÜŞÜNCE SÜRECİ:
1. Soruyu anla.
2. Bildiğin bilgilerle kısa ve net yanıt ver.
3. Emin değilsen belirt.

KRİTİK KURALLAR:
- ⚠️ SADECE TÜRKÇE YANIT VER. NO CHINESE!
- Kullanıcıya ismiyle hitap et.
- Kısa ve samimi ol.
- Uydurma yapma, bilmiyorsan söyle.

🇹🇷 TÜRKÇE YANITINI VER:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        llm = ChatOllama(model=model_name, temperature=0.2)
        chain = prompt | llm
        
        response = chain.invoke({
            "user_profile": user_profile,
            "question": question
        })
        
        return response.content
        
    except Exception as e:
        return f"HATA: {e}"
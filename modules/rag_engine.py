"""
RAG Engine Module
Retrieval-Augmented Generation sistemi ve kişiselleştirme.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from modules.database import get_profile_db, get_learning_stats
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

def get_personalized_context():
    """Kişiselleştirme için kullanıcı bağlamı oluşturur."""
    user_profile = get_profile_db()
    if not user_profile:
        user_profile = "Kullanıcı hakkında özel bilgi yok."
    
    # Öğrenme istatistiklerini al
    try:
        stats = get_learning_stats()
        learning_context = f"""
Öğrenme İstatistikleri:
- Toplam Doküman: {stats.get('total_documents', 0)}
- Toplam Flashcard: {stats.get('total_flashcards', 0)}
- Bugün Tekrar Edilen: {stats.get('cards_reviewed_today', 0)}
- Genel Başarı Oranı: %{stats.get('success_rate', 0)}
"""
    except:
        learning_context = ""
    
    return user_profile, learning_context

def get_ai_response(model_name, vectorstore, user_question, chat_history=None):
    """
    Ollama'ya soruyu sorar. Kişiselleştirilmiş yanıt döndürür.
    
    Args:
        model_name: Kullanılacak model (llama3, phi3, mistral vb.)
        vectorstore: FAISS vektör veritabanı
        user_question: Kullanıcının sorusu
        chat_history: Önceki sohbet geçmişi (opsiyonel)
    
    Returns:
        tuple: (AI yanıtı, kaynak dokümanlar)
    """
    try:
        # 1. Kişiselleştirme bilgilerini al
        user_profile, learning_context = get_personalized_context()

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
- TÜM YANITLAR MUTLAKA TÜRKÇE OLMALIDIR.
- SADECE DÖKÜMAN İÇERİĞİNDEKİ bilgileri kullan. Uydurma yapma.
- Bilgi dokümanda yoksa açıkça belirt.
- Yapılandırılmış ve anlaşılır yanıtlar ver.
- Kullanıcıya ismiyle hitap et (KULLANICI BİLGİLERİ'nden).

YANIT FORMAT:
- Kısa ve öz cevaplar ver.
- Gerekirse madde işaretleri kullan.
- Teknik terimleri açıkla.

TÜRKÇE YANITINI VER:"""
        
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

def get_quick_answer(model_name, question):
    """
    Doküman olmadan hızlı cevap verir.
    
    Args:
        model_name: Kullanılacak model
        question: Kullanıcının sorusu
    
    Returns:
        str: AI yanıtı
    """
    try:
        user_profile, _ = get_personalized_context()
        template = """Sen LocalInsights asistanısın - akıllı ve yardımsever bir eğitim asistanı.

KULLANICI BİLGİLERİ: {user_profile}

KULLANICI SORUSU: {question}

DÜŞÜNCE SÜRECİ:
1. Soruyu anla.
2. Bildiğin bilgilerle kısa ve net yanıt ver.
3. Emin değilsen belirt.

KRİTİK KURALLAR:
- MUTLAKA TÜRKÇE yanıt ver.
- Kullanıcıya ismiyle hitap et.
- Kısa ve samimi ol.
- Uydurma yapma, bilmiyorsan söyle.

TÜRKÇE YANITINI VER:"""
        
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
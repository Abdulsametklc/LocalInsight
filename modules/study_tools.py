"""
Study Tools Module
AI destekli özet, sınav sorusu ve flashcard oluşturma modülü.
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import json
import re

# ============== PROMPT ŞABLONLARI ==============

SUMMARY_PROMPT = """
Sen bir eğitim asistanısın. Verilen metni analiz edip yapılandırılmış bir özet oluştur.

METİN:
{text}

GÖREV: Aşağıdaki formatta bir özet oluştur:

## 📚 Konu Başlığı
[Ana konu ve bağlamı]

## 🎯 Temel Kavramlar
- [Kavram 1]: Açıklama
- [Kavram 2]: Açıklama
- [Kavram 3]: Açıklama

## 📝 Özet
[3-5 paragraf halinde ana fikirleri özetle]

## 💡 Önemli Noktalar
1. [Önemli nokta 1]
2. [Önemli nokta 2]
3. [Önemli nokta 3]

## 🔗 İlişkili Konular
- [İlgili konu 1]
- [İlgili konu 2]

Türkçe olarak yanıt ver.
"""

FLASHCARD_PROMPT = """
Sen bir eğitim asistanısın. Verilen metinden {count} adet bilgi kartı (flashcard) oluştur.

METİN:
{text}

GÖREV: Her kart için aşağıdaki JSON formatında çıktı ver:

```json
[
  {{
    "question": "Açık ve net bir soru",
    "answer": "Kısa ve öz cevap (1-2 cümle)",
    "difficulty": "kolay" veya "orta" veya "zor"
  }},
  ...
]
```

KURALLAR:
1. Sorular metindeki önemli kavramları test etmeli
2. Cevaplar kısa ve ezberlenebilir olmalı
3. Zorluk seviyelerini dengeli dağıt
4. Sadece JSON formatında yanıt ver, başka bir şey yazma

JSON çıktısı:
"""

QUIZ_PROMPT = """
Sen bir eğitim asistanısın. Verilen metinden {count} adet sınav sorusu oluştur.

METİN:
{text}

GÖREV: Her soru için aşağıdaki JSON formatında çıktı ver:

```json
[
  {{
    "type": "çoktan_seçmeli" veya "açık_uçlu" veya "doğru_yanlış",
    "question": "Soru metni",
    "options": ["A şıkkı", "B şıkkı", "C şıkkı", "D şıkkı"],
    "answer": "Doğru cevap",
    "explanation": "Cevabın açıklaması"
  }},
  ...
]
```

KURALLAR:
1. Çoktan seçmeli sorular için 4 şık olmalı
2. Doğru/yanlış soruları için options boş olabilir
3. Açık uçlu sorular için options boş olmalı
4. Her sorunun bir açıklaması olmalı
5. Zorluk seviyelerini dengeli dağıt
6. Sadece JSON formatında yanıt ver

JSON çıktısı:
"""

# ============== YARDIMCI FONKSİYONLAR ==============

def extract_json_from_response(response_text):
    """AI yanıtından JSON verisini çıkarır."""
    # Markdown kod bloğu içindekileri bul
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Kod bloğu yoksa direkt JSON'u bul
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response_text
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # JSON parse edilemezse boş liste döndür
        print(f"JSON parse hatası: {json_str[:200]}...")
        return []

def chunk_text(text, max_chunk_size=4000):
    """Uzun metni parçalara böler."""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

# ============== ANA FONKSİYONLAR ==============

def generate_summary(text, model_name="llama3"):
    """
    Verilen metinden yapılandırılmış özet oluşturur.
    
    Args:
        text: Özetlenecek metin
        model_name: Kullanılacak Ollama modeli
    
    Returns:
        str: Markdown formatında özet
    """
    try:
        # Metin çok uzunsa parçala ve ana noktaları kullan
        if len(text) > 6000:
            text = text[:6000] + "\n\n[Metin kısaltıldı...]"
        
        prompt = ChatPromptTemplate.from_template(SUMMARY_PROMPT)
        llm = ChatOllama(model=model_name, temperature=0.3)
        chain = prompt | llm
        
        response = chain.invoke({"text": text})
        return response.content
    
    except Exception as e:
        return f"Özet oluşturulurken hata: {e}"

def generate_flashcards(text, count=10, model_name="llama3"):
    """
    Verilen metinden flashcard'lar oluşturur.
    
    Args:
        text: Kaynak metin
        count: Oluşturulacak kart sayısı
        model_name: Kullanılacak Ollama modeli
    
    Returns:
        list: Flashcard sözlükleri listesi
    """
    try:
        # Metin çok uzunsa parçala
        if len(text) > 5000:
            text = text[:5000]
        
        prompt = ChatPromptTemplate.from_template(FLASHCARD_PROMPT)
        llm = ChatOllama(model=model_name, temperature=0.2)
        chain = prompt | llm
        
        response = chain.invoke({"text": text, "count": count})
        flashcards = extract_json_from_response(response.content)
        
        # Veri doğrulaması
        valid_cards = []
        for card in flashcards:
            if isinstance(card, dict) and 'question' in card and 'answer' in card:
                valid_cards.append({
                    'question': card['question'],
                    'answer': card['answer'],
                    'difficulty': card.get('difficulty', 'orta')
                })
        
        return valid_cards
    
    except Exception as e:
        print(f"Flashcard oluşturma hatası: {e}")
        return []

def generate_quiz(text, count=10, model_name="llama3"):
    """
    Verilen metinden sınav soruları oluşturur.
    
    Args:
        text: Kaynak metin
        count: Oluşturulacak soru sayısı
        model_name: Kullanılacak Ollama modeli
    
    Returns:
        list: Soru sözlükleri listesi
    """
    try:
        # Metin çok uzunsa parçala
        if len(text) > 5000:
            text = text[:5000]
        
        prompt = ChatPromptTemplate.from_template(QUIZ_PROMPT)
        llm = ChatOllama(model=model_name, temperature=0.2)
        chain = prompt | llm
        
        response = chain.invoke({"text": text, "count": count})
        questions = extract_json_from_response(response.content)
        
        # Veri doğrulaması
        valid_questions = []
        for q in questions:
            if isinstance(q, dict) and 'question' in q and 'answer' in q:
                valid_questions.append({
                    'type': q.get('type', 'açık_uçlu'),
                    'question': q['question'],
                    'options': q.get('options', []),
                    'answer': q['answer'],
                    'explanation': q.get('explanation', '')
                })
        
        return valid_questions
    
    except Exception as e:
        print(f"Sınav sorusu oluşturma hatası: {e}")
        return []

def generate_study_material(text, document_id, model_name="llama3", 
                           generate_summary_=True, 
                           flashcard_count=10, 
                           quiz_count=10,
                           user_id=None):
    """
    Tek seferde tüm çalışma materyallerini oluşturur.
    
    Args:
        text: Kaynak metin
        document_id: Veritabanındaki doküman ID'si
        model_name: Kullanılacak Ollama modeli
        generate_summary_: Özet oluşturulsun mu?
        flashcard_count: Flashcard sayısı
        quiz_count: Sınav sorusu sayısı
        user_id: Kullanıcı ID (multi-tenant izolasyonu için zorunlu)
    
    Returns:
        dict: Oluşturulan materyaller
    """
    if user_id is None:
        raise ValueError("Security Error: generate_study_material requires user_id parameter")
    
    from modules.repo_documents import (
        create_summary, create_flashcards_bulk, create_quiz_questions_bulk, mark_document_processed
    )
    
    results = {
        'summary': None,
        'flashcards': [],
        'quiz_questions': []
    }
    
    try:
        # Özet oluştur
        if generate_summary_:
            summary = generate_summary(text, model_name)
            if summary and not summary.startswith("Özet oluşturulurken hata"):
                create_summary(document_id, summary, user_id=user_id)
                results['summary'] = summary
        
        # Flashcard'lar oluştur
        if flashcard_count > 0:
            flashcards = generate_flashcards(text, flashcard_count, model_name)
            if flashcards:
                create_flashcards_bulk(flashcards, user_id=user_id, document_id=document_id)
                results['flashcards'] = flashcards
        
        # Sınav soruları oluştur
        if quiz_count > 0:
            questions = generate_quiz(text, quiz_count, model_name)
            if questions:
                create_quiz_questions_bulk(questions, user_id=user_id, document_id=document_id)
                results['quiz_questions'] = questions
        
        # Dokümanı işlenmiş olarak işaretle
        mark_document_processed(document_id, user_id=user_id)
        
    except Exception as e:
        print(f"Materyal oluşturma hatası: {e}")
    
    return results

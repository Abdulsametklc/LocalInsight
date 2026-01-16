import sqlite3
from datetime import datetime

DB_NAME = "LocalInsights.db"

def get_connection():
    """Veritabanı bağlantısı oluşturur."""
    return sqlite3.connect(DB_NAME)

def init_db():
    """Veri tabanı tablolarını oluşturur."""
    conn = get_connection()
    c = conn.cursor()
    
    # Mevcut tablolar
    c.execute('''CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY, 
        content TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS chat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        role TEXT, 
        message TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Yeni tablolar - Dokümanlar
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        content TEXT,
        doc_type TEXT,
        upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_processed INTEGER DEFAULT 0
    )''')
    
    # Özetler
    c.execute('''CREATE TABLE IF NOT EXISTS summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        summary_text TEXT,
        created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )''')
    
    # Bilgi Kartları (Flashcards)
    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        difficulty TEXT DEFAULT 'orta',
        times_reviewed INTEGER DEFAULT 0,
        times_correct INTEGER DEFAULT 0,
        last_reviewed DATETIME,
        next_review DATETIME,
        created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )''')
    
    # Sınav Soruları
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        question_type TEXT,
        question_text TEXT NOT NULL,
        options TEXT,
        correct_answer TEXT NOT NULL,
        explanation TEXT,
        created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )''')
    
    # Öğrenme Geçmişi
    c.execute('''CREATE TABLE IF NOT EXISTS learning_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flashcard_id INTEGER,
        quiz_question_id INTEGER,
        result TEXT,
        review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (flashcard_id) REFERENCES flashcards(id),
        FOREIGN KEY (quiz_question_id) REFERENCES quiz_questions(id)
    )''')
    
    # Kullanıcı Tercihleri
    c.execute('''CREATE TABLE IF NOT EXISTS user_preferences (
        id INTEGER PRIMARY KEY,
        learning_style TEXT DEFAULT 'görsel',
        difficulty_preference TEXT DEFAULT 'orta',
        daily_goal INTEGER DEFAULT 10,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

# ============== PROFİL FONKSİYONLARI ==============

def save_profile_db(text):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM profile")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO profile (content) VALUES (?)", (text,))
    else:
        c.execute("UPDATE profile SET content = ? WHERE id = 1", (text,))
    conn.commit()
    conn.close()

def get_profile_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT content FROM profile WHERE id = 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else ""

def log_message_db(role, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO chat_logs (role, message) VALUES (?, ?)", (role, message))
    conn.commit()
    conn.close()

# ============== DOKÜMAN FONKSİYONLARI ==============

def save_document(filename, content, doc_type):
    """Yeni doküman kaydeder."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO documents (filename, content, doc_type) VALUES (?, ?, ?)",
        (filename, content, doc_type)
    )
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def get_all_documents():
    """Tüm dokümanları getirir."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, filename, doc_type, upload_date, is_processed FROM documents ORDER BY upload_date DESC")
    results = c.fetchall()
    conn.close()
    return results

def get_document_by_id(doc_id):
    """ID'ye göre doküman getirir."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    result = c.fetchone()
    conn.close()
    return result

def mark_document_processed(doc_id):
    """Dokümanı işlenmiş olarak işaretler."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE documents SET is_processed = 1 WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

# ============== ÖZET FONKSİYONLARI ==============

def save_summary(document_id, summary_text):
    """Özet kaydeder."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO summaries (document_id, summary_text) VALUES (?, ?)",
        (document_id, summary_text)
    )
    conn.commit()
    conn.close()

def get_summaries_by_document(document_id):
    """Dokümana ait özetleri getirir."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM summaries WHERE document_id = ? ORDER BY created_date DESC", (document_id,))
    results = c.fetchall()
    conn.close()
    return results

def get_all_summaries():
    """Tüm özetleri getirir."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT s.id, d.filename, s.summary_text, s.created_date 
        FROM summaries s 
        JOIN documents d ON s.document_id = d.id 
        ORDER BY s.created_date DESC
    """)
    results = c.fetchall()
    conn.close()
    return results

# ============== FLASHCARD FONKSİYONLARI ==============

def save_flashcard(document_id, question, answer, difficulty='orta'):
    """Yeni flashcard kaydeder."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO flashcards (document_id, question, answer, difficulty) VALUES (?, ?, ?, ?)",
        (document_id, question, answer, difficulty)
    )
    conn.commit()
    conn.close()

def save_flashcards_bulk(document_id, flashcards_list):
    """Birden fazla flashcard kaydeder."""
    conn = get_connection()
    c = conn.cursor()
    for card in flashcards_list:
        c.execute(
            "INSERT INTO flashcards (document_id, question, answer, difficulty) VALUES (?, ?, ?, ?)",
            (document_id, card['question'], card['answer'], card.get('difficulty', 'orta'))
        )
    conn.commit()
    conn.close()

def get_flashcards_by_document(document_id):
    """Dokümana ait flashcard'ları getirir."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM flashcards WHERE document_id = ?", (document_id,))
    results = c.fetchall()
    conn.close()
    return results

def get_all_flashcards():
    """Tüm flashcard'ları getirir."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT f.id, d.filename, f.question, f.answer, f.difficulty, f.times_reviewed, f.times_correct
        FROM flashcards f 
        JOIN documents d ON f.document_id = d.id 
        ORDER BY f.created_date DESC
    """)
    results = c.fetchall()
    conn.close()
    return results

def get_flashcards_for_review(limit=10):
    """Tekrar edilmesi gereken kartları getirir (spaced repetition)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT f.id, d.filename, f.question, f.answer, f.difficulty, f.times_reviewed
        FROM flashcards f 
        JOIN documents d ON f.document_id = d.id 
        WHERE f.next_review IS NULL OR f.next_review <= datetime('now')
        ORDER BY f.times_reviewed ASC, RANDOM()
        LIMIT ?
    """, (limit,))
    results = c.fetchall()
    conn.close()
    return results

def update_flashcard_review(flashcard_id, is_correct):
    """Flashcard tekrar sonucunu günceller."""
    conn = get_connection()
    c = conn.cursor()
    
    # Mevcut değerleri al
    c.execute("SELECT times_reviewed, times_correct FROM flashcards WHERE id = ?", (flashcard_id,))
    result = c.fetchone()
    times_reviewed = result[0] + 1
    times_correct = result[1] + (1 if is_correct else 0)
    
    # Spaced repetition - doğru cevaplara göre sonraki tekrar zamanını ayarla
    if is_correct:
        # Başarı oranına göre gün hesapla (1, 3, 7, 14, 30 gün)
        success_rate = times_correct / times_reviewed if times_reviewed > 0 else 0
        if success_rate >= 0.8:
            days = 30
        elif success_rate >= 0.6:
            days = 14
        elif success_rate >= 0.4:
            days = 7
        else:
            days = 3
    else:
        days = 1  # Yanlış cevaplarda ertesi gün tekrar
    
    c.execute("""
        UPDATE flashcards 
        SET times_reviewed = ?, times_correct = ?, last_reviewed = datetime('now'), 
            next_review = datetime('now', '+' || ? || ' days')
        WHERE id = ?
    """, (times_reviewed, times_correct, days, flashcard_id))
    
    # Öğrenme geçmişine kaydet
    c.execute(
        "INSERT INTO learning_history (flashcard_id, result) VALUES (?, ?)",
        (flashcard_id, 'correct' if is_correct else 'incorrect')
    )
    
    conn.commit()
    conn.close()

# ============== SINAV SORUSU FONKSİYONLARI ==============

def save_quiz_question(document_id, question_type, question_text, options, correct_answer, explanation=''):
    """Yeni sınav sorusu kaydeder."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO quiz_questions 
           (document_id, question_type, question_text, options, correct_answer, explanation) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (document_id, question_type, question_text, options, correct_answer, explanation)
    )
    conn.commit()
    conn.close()

def save_quiz_questions_bulk(document_id, questions_list):
    """Birden fazla sınav sorusu kaydeder."""
    conn = get_connection()
    c = conn.cursor()
    for q in questions_list:
        options = '|||'.join(q.get('options', [])) if q.get('options') else ''
        c.execute(
            """INSERT INTO quiz_questions 
               (document_id, question_type, question_text, options, correct_answer, explanation) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (document_id, q['type'], q['question'], options, q['answer'], q.get('explanation', ''))
        )
    conn.commit()
    conn.close()

def get_quiz_questions_by_document(document_id):
    """Dokümana ait sınav sorularını getirir."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM quiz_questions WHERE document_id = ?", (document_id,))
    results = c.fetchall()
    conn.close()
    return results

def get_all_quiz_questions():
    """Tüm sınav sorularını getirir."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT q.id, d.filename, q.question_type, q.question_text, q.options, q.correct_answer, q.explanation
        FROM quiz_questions q 
        JOIN documents d ON q.document_id = d.id 
        ORDER BY q.created_date DESC
    """)
    results = c.fetchall()
    conn.close()
    return results

def get_random_quiz(document_id=None, count=10):
    """Rastgele sınav soruları getirir."""
    conn = get_connection()
    c = conn.cursor()
    if document_id:
        c.execute("""
            SELECT q.id, q.question_type, q.question_text, q.options, q.correct_answer, q.explanation
            FROM quiz_questions q 
            WHERE q.document_id = ?
            ORDER BY RANDOM()
            LIMIT ?
        """, (document_id, count))
    else:
        c.execute("""
            SELECT q.id, q.question_type, q.question_text, q.options, q.correct_answer, q.explanation
            FROM quiz_questions q 
            ORDER BY RANDOM()
            LIMIT ?
        """, (count,))
    results = c.fetchall()
    conn.close()
    return results

def log_quiz_result(quiz_question_id, is_correct):
    """Sınav sonucunu kaydeder."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO learning_history (quiz_question_id, result) VALUES (?, ?)",
        (quiz_question_id, 'correct' if is_correct else 'incorrect')
    )
    conn.commit()
    conn.close()

# ============== İSTATİSTİK FONKSİYONLARI ==============

def get_learning_stats():
    """Öğrenme istatistiklerini getirir."""
    conn = get_connection()
    c = conn.cursor()
    
    stats = {}
    
    # Toplam doküman sayısı
    c.execute("SELECT COUNT(*) FROM documents")
    stats['total_documents'] = c.fetchone()[0]
    
    # Toplam flashcard sayısı
    c.execute("SELECT COUNT(*) FROM flashcards")
    stats['total_flashcards'] = c.fetchone()[0]
    
    # Toplam soru sayısı
    c.execute("SELECT COUNT(*) FROM quiz_questions")
    stats['total_questions'] = c.fetchone()[0]
    
    # Bugün tekrar edilen kart sayısı
    c.execute("""
        SELECT COUNT(*) FROM learning_history 
        WHERE flashcard_id IS NOT NULL AND date(review_date) = date('now')
    """)
    stats['cards_reviewed_today'] = c.fetchone()[0]
    
    # Genel başarı oranı
    c.execute("""
        SELECT 
            COUNT(CASE WHEN result = 'correct' THEN 1 END) * 100.0 / COUNT(*) 
        FROM learning_history 
        WHERE result IS NOT NULL
    """)
    result = c.fetchone()[0]
    stats['success_rate'] = round(result, 1) if result else 0
    
    conn.close()
    return stats
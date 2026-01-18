"""
Documents Repository - Multi-Tenant Ready
==========================================
Document, Summary, Flashcard ve Quiz CRUD islemleri.
Her fonksiyon user_id ile calisir - veri izolasyonu garanti.
"""

from typing import Optional
from .db import get_db, require_user_id, execute_query, execute_many


# ============== DOCUMENT FONKSIYONLARI ==============

@require_user_id
def create_document(filename: str, content: str, doc_type: str, *, user_id: int, checksum: str = None) -> int:
    """Yeni dokuman kaydeder.
    
    Args:
        filename: Dosya adi
        content: Dokuman icerigi
        doc_type: Dosya tipi (pdf, docx, etc.)
        user_id: Kullanici ID (zorunlu keyword arg)
        checksum: Dosya hash (duplicate kontrolu icin)
        
    Returns:
        Yeni document_id
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO documents (user_id, filename, content, doc_type, checksum) 
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, filename, content, doc_type, checksum)
        )
        conn.commit()
        return cursor.lastrowid


@require_user_id
def get_documents(*, user_id: int, limit: int = 100) -> list:
    """Kullanicinin tum dokumanlarini listeler.
    
    Args:
        user_id: Kullanici ID (zorunlu keyword arg)
        limit: Maksimum kayit sayisi
        
    Returns:
        Document listesi
    """
    return execute_query(
        """SELECT id, filename, doc_type, upload_date, is_processed 
           FROM documents 
           WHERE user_id = ? 
           ORDER BY upload_date DESC 
           LIMIT ?""",
        (user_id, limit),
        fetch='all'
    )


@require_user_id
def get_document(document_id: int, *, user_id: int) -> Optional[dict]:
    """Belirli bir dokumani getirir - user_id kontrolu ile.
    
    Args:
        document_id: Dokuman ID
        user_id: Kullanici ID (zorunlu keyword arg)
        
    Returns:
        Document dict veya None
    """
    return execute_query(
        "SELECT * FROM documents WHERE id = ? AND user_id = ?",
        (document_id, user_id),
        fetch='one'
    )


@require_user_id
def delete_document(document_id: int, *, user_id: int) -> bool:
    """Dokumani ve iliskili verileri siler.
    
    Args:
        document_id: Dokuman ID
        user_id: Kullanici ID (zorunlu keyword arg)
        
    Returns:
        True eger silme basarili ise
    """
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM documents WHERE id = ? AND user_id = ?",
            (document_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


@require_user_id
def mark_document_processed(document_id: int, *, user_id: int) -> bool:
    """Dokumani islenmis olarak isaretler.
    
    Args:
        document_id: Dokuman ID
        user_id: Kullanici ID (zorunlu keyword arg)
        
    Returns:
        True eger guncelleme basarili ise
    """
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE documents SET is_processed = 1 WHERE id = ? AND user_id = ?",
            (document_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ============== SUMMARY FONKSIYONLARI ==============

@require_user_id
def create_summary(document_id: int, summary_text: str, *, user_id: int) -> int:
    """Yeni ozet kaydeder.
    
    Args:
        document_id: Ilgili dokuman ID
        summary_text: Ozet metni
        user_id: Kullanici ID (zorunlu keyword arg)
        
    Returns:
        Yeni summary_id
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO summaries (user_id, document_id, summary_text) 
               VALUES (?, ?, ?)""",
            (user_id, document_id, summary_text)
        )
        conn.commit()
        return cursor.lastrowid


@require_user_id
def get_summaries(*, user_id: int, document_id: int = None, limit: int = 50) -> list:
    """Kullanicinin ozetlerini listeler.
    
    Args:
        user_id: Kullanici ID (zorunlu keyword arg)
        document_id: Belirli dokumana ait ozetler (opsiyonel)
        limit: Maksimum kayit sayisi
        
    Returns:
        Summary listesi
    """
    if document_id:
        return execute_query(
            """SELECT s.id, d.filename, s.summary_text, s.created_at 
               FROM summaries s 
               JOIN documents d ON s.document_id = d.id 
               WHERE s.user_id = ? AND s.document_id = ?
               ORDER BY s.created_at DESC LIMIT ?""",
            (user_id, document_id, limit),
            fetch='all'
        )
    else:
        return execute_query(
            """SELECT s.id, d.filename, s.summary_text, s.created_at 
               FROM summaries s 
               JOIN documents d ON s.document_id = d.id 
               WHERE s.user_id = ?
               ORDER BY s.created_at DESC LIMIT ?""",
            (user_id, limit),
            fetch='all'
        )


# ============== FLASHCARD FONKSIYONLARI ==============

@require_user_id
def create_flashcard(question: str, answer: str, *, user_id: int, document_id: int = None, difficulty: str = 'orta') -> int:
    """Yeni flashcard kaydeder.
    
    Args:
        question: Soru
        answer: Cevap
        user_id: Kullanici ID (zorunlu keyword arg)
        document_id: Ilgili dokuman (opsiyonel)
        difficulty: Zorluk seviyesi
        
    Returns:
        Yeni flashcard_id
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO flashcards (user_id, document_id, question, answer, difficulty) 
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, document_id, question, answer, difficulty)
        )
        conn.commit()
        return cursor.lastrowid


@require_user_id
def create_flashcards_bulk(flashcards_list: list, *, user_id: int, document_id: int = None) -> int:
    """Birden fazla flashcard kaydeder.
    
    Args:
        flashcards_list: [{'question': '...', 'answer': '...', 'difficulty': '...'}, ...]
        user_id: Kullanici ID (zorunlu keyword arg)
        document_id: Ilgili dokuman (opsiyonel)
        
    Returns:
        Eklenen kayit sayisi
    """
    params_list = [
        (user_id, document_id, card['question'], card['answer'], card.get('difficulty', 'orta'))
        for card in flashcards_list
    ]
    return execute_many(
        "INSERT INTO flashcards (user_id, document_id, question, answer, difficulty) VALUES (?, ?, ?, ?, ?)",
        params_list
    )


@require_user_id
def get_flashcards(*, user_id: int, document_id: int = None, limit: int = 100) -> list:
    """Kullanicinin flashcard'larini listeler.
    
    Args:
        user_id: Kullanici ID (zorunlu keyword arg)
        document_id: Belirli dokumana ait kartlar (opsiyonel)
        limit: Maksimum kayit sayisi
        
    Returns:
        Flashcard listesi
    """
    if document_id:
        return execute_query(
            """SELECT f.id, d.filename, f.question, f.answer, f.difficulty, 
                      f.times_reviewed, f.times_correct, f.next_review
               FROM flashcards f 
               LEFT JOIN documents d ON f.document_id = d.id 
               WHERE f.user_id = ? AND f.document_id = ?
               ORDER BY f.created_at DESC LIMIT ?""",
            (user_id, document_id, limit),
            fetch='all'
        )
    else:
        return execute_query(
            """SELECT f.id, d.filename, f.question, f.answer, f.difficulty,
                      f.times_reviewed, f.times_correct, f.next_review
               FROM flashcards f 
               LEFT JOIN documents d ON f.document_id = d.id 
               WHERE f.user_id = ?
               ORDER BY f.created_at DESC LIMIT ?""",
            (user_id, limit),
            fetch='all'
        )


@require_user_id
def get_flashcards_for_review(*, user_id: int, limit: int = 10) -> list:
    """Tekrar edilmesi gereken kartlari getirir (spaced repetition).
    
    Args:
        user_id: Kullanici ID (zorunlu keyword arg)
        limit: Maksimum kart sayisi
        
    Returns:
        Review edilecek flashcard listesi
    """
    return execute_query(
        """SELECT f.id, d.filename, f.question, f.answer, f.difficulty, f.times_reviewed
           FROM flashcards f 
           LEFT JOIN documents d ON f.document_id = d.id 
           WHERE f.user_id = ? AND (f.next_review IS NULL OR f.next_review <= datetime('now'))
           ORDER BY f.times_reviewed ASC, RANDOM()
           LIMIT ?""",
        (user_id, limit),
        fetch='all'
    )


@require_user_id
def update_flashcard_review(flashcard_id: int, is_correct: bool, *, user_id: int) -> bool:
    """Flashcard tekrar sonucunu gunceller.
    
    Args:
        flashcard_id: Flashcard ID
        is_correct: Dogru mu yanlıs mi
        user_id: Kullanici ID (zorunlu keyword arg)
        
    Returns:
        True eger guncelleme basarili ise
    """
    # Once flashcard'in bu user'a ait oldugunu kontrol et
    card = execute_query(
        "SELECT times_reviewed, times_correct FROM flashcards WHERE id = ? AND user_id = ?",
        (flashcard_id, user_id),
        fetch='one'
    )
    
    if not card:
        return False
    
    times_reviewed = card['times_reviewed'] + 1
    times_correct = card['times_correct'] + (1 if is_correct else 0)
    
    # Spaced repetition - basari oranina gore sonraki tekrar
    if is_correct:
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
        days = 1
    
    with get_db() as conn:
        conn.execute(
            """UPDATE flashcards 
               SET times_reviewed = ?, times_correct = ?, 
                   last_reviewed = datetime('now'), 
                   next_review = datetime('now', '+' || ? || ' days')
               WHERE id = ? AND user_id = ?""",
            (times_reviewed, times_correct, days, flashcard_id, user_id)
        )
        
        # Learning history'e kaydet
        conn.execute(
            "INSERT INTO learning_history (user_id, flashcard_id, result) VALUES (?, ?, ?)",
            (user_id, flashcard_id, 'correct' if is_correct else 'incorrect')
        )
        
        conn.commit()
        return True


# ============== QUIZ FONKSIYONLARI ==============

@require_user_id
def create_quiz_question(
    question_text: str, 
    correct_answer: str, 
    *, 
    user_id: int,
    document_id: int = None,
    question_type: str = 'multiple_choice',
    options: str = '',
    explanation: str = ''
) -> int:
    """Yeni quiz sorusu kaydeder.
    
    Args:
        question_text: Soru metni
        correct_answer: Dogru cevap
        user_id: Kullanici ID (zorunlu keyword arg)
        document_id: Ilgili dokuman (opsiyonel)
        question_type: Soru tipi
        options: Secenekler (||| ile ayrilmis)
        explanation: Aciklama
        
    Returns:
        Yeni question_id
    """
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO quiz_questions 
               (user_id, document_id, question_type, question_text, options, correct_answer, explanation) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, document_id, question_type, question_text, options, correct_answer, explanation)
        )
        conn.commit()
        return cursor.lastrowid


@require_user_id
def create_quiz_questions_bulk(questions_list: list, *, user_id: int, document_id: int = None) -> int:
    """Birden fazla quiz sorusu kaydeder.
    
    Args:
        questions_list: [{'question': '...', 'answer': '...', 'type': '...', 'options': [...], 'explanation': '...'}, ...]
        user_id: Kullanici ID (zorunlu keyword arg)
        document_id: Ilgili dokuman (opsiyonel)
        
    Returns:
        Eklenen kayit sayisi
    """
    params_list = [
        (
            user_id, 
            document_id, 
            q.get('type', 'multiple_choice'),
            q['question'], 
            '|||'.join(q.get('options', [])) if q.get('options') else '',
            q['answer'],
            q.get('explanation', '')
        )
        for q in questions_list
    ]
    return execute_many(
        """INSERT INTO quiz_questions 
           (user_id, document_id, question_type, question_text, options, correct_answer, explanation) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        params_list
    )


@require_user_id
def get_quiz_questions(*, user_id: int, document_id: int = None, limit: int = 100) -> list:
    """Kullanicinin quiz sorularini listeler.
    
    Args:
        user_id: Kullanici ID (zorunlu keyword arg)
        document_id: Belirli dokumana ait sorular (opsiyonel)
        limit: Maksimum kayit sayisi
        
    Returns:
        Quiz question listesi
    """
    if document_id:
        return execute_query(
            """SELECT q.id, d.filename, q.question_type, q.question_text, 
                      q.options, q.correct_answer, q.explanation
               FROM quiz_questions q 
               LEFT JOIN documents d ON q.document_id = d.id 
               WHERE q.user_id = ? AND q.document_id = ?
               ORDER BY q.created_at DESC LIMIT ?""",
            (user_id, document_id, limit),
            fetch='all'
        )
    else:
        return execute_query(
            """SELECT q.id, d.filename, q.question_type, q.question_text,
                      q.options, q.correct_answer, q.explanation
               FROM quiz_questions q 
               LEFT JOIN documents d ON q.document_id = d.id 
               WHERE q.user_id = ?
               ORDER BY q.created_at DESC LIMIT ?""",
            (user_id, limit),
            fetch='all'
        )


@require_user_id
def get_random_quiz(*, user_id: int, document_id: int = None, count: int = 10) -> list:
    """Rastgele quiz sorulari getirir.
    
    Args:
        user_id: Kullanici ID (zorunlu keyword arg)
        document_id: Belirli dokumandan sorular (opsiyonel)
        count: Soru sayisi
        
    Returns:
        Rastgele quiz soruları
    """
    if document_id:
        return execute_query(
            """SELECT id, question_type, question_text, options, correct_answer, explanation
               FROM quiz_questions 
               WHERE user_id = ? AND document_id = ?
               ORDER BY RANDOM() LIMIT ?""",
            (user_id, document_id, count),
            fetch='all'
        )
    else:
        return execute_query(
            """SELECT id, question_type, question_text, options, correct_answer, explanation
               FROM quiz_questions 
               WHERE user_id = ?
               ORDER BY RANDOM() LIMIT ?""",
            (user_id, count),
            fetch='all'
        )


@require_user_id
def log_quiz_result(quiz_question_id: int, is_correct: bool, *, user_id: int) -> int:
    """Quiz sonucunu kaydeder.
    
    Args:
        quiz_question_id: Soru ID
        is_correct: Dogru mu yanlis mi
        user_id: Kullanici ID (zorunlu keyword arg)
        
    Returns:
        Log ID
    """
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO learning_history (user_id, quiz_question_id, result) VALUES (?, ?, ?)",
            (user_id, quiz_question_id, 'correct' if is_correct else 'incorrect')
        )
        conn.commit()
        return cursor.lastrowid


# ============== ISTATISTIK FONKSIYONLARI ==============

@require_user_id
def get_learning_stats(*, user_id: int) -> dict:
    """Kullanicinin ogrenme istatistiklerini getirir.
    
    Args:
        user_id: Kullanici ID (zorunlu keyword arg)
        
    Returns:
        Istatistik dict
    """
    with get_db() as conn:
        stats = {}
        
        # Toplam dokuman sayisi
        cursor = conn.execute("SELECT COUNT(*) FROM documents WHERE user_id = ?", (user_id,))
        stats['total_documents'] = cursor.fetchone()[0]
        
        # Toplam flashcard sayisi
        cursor = conn.execute("SELECT COUNT(*) FROM flashcards WHERE user_id = ?", (user_id,))
        stats['total_flashcards'] = cursor.fetchone()[0]
        
        # Toplam soru sayisi
        cursor = conn.execute("SELECT COUNT(*) FROM quiz_questions WHERE user_id = ?", (user_id,))
        stats['total_questions'] = cursor.fetchone()[0]
        
        # Bugun tekrar edilen kart sayisi
        cursor = conn.execute(
            """SELECT COUNT(*) FROM learning_history 
               WHERE user_id = ? AND flashcard_id IS NOT NULL AND date(review_date) = date('now')""",
            (user_id,)
        )
        stats['cards_reviewed_today'] = cursor.fetchone()[0]
        
        # Genel basari orani
        cursor = conn.execute(
            """SELECT COUNT(CASE WHEN result = 'correct' THEN 1 END) * 100.0 / COUNT(*) 
               FROM learning_history 
               WHERE user_id = ? AND result IS NOT NULL""",
            (user_id,)
        )
        result = cursor.fetchone()[0]
        stats['success_rate'] = round(result, 1) if result else 0
        
        return stats

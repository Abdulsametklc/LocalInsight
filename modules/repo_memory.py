"""
Memory Repository Module
========================
Kullanıcıya özel kişiselleştirilmiş hafıza CRUD işlemleri.
Tüm fonksiyonlar @require_user_id ile korunur - multi-tenant izolasyon garantili.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from .db import get_db, require_user_id, execute_query, execute_many


# ============== MEMORY ITEMS CRUD ==============

@require_user_id
def upsert_memory(
    category: str, 
    key: str, 
    value: str, 
    *, 
    user_id: int,
    confidence: float = 0.5, 
    importance: float = 0.5,
    source_message_id: int = None
) -> int:
    """Hafıza öğesi ekler veya günceller.
    
    Args:
        category: Kategori (profile, preferences, goals, context, constraints)
        key: Anahtar
        value: Değer
        user_id: Kullanıcı ID
        confidence: Güven skoru (0-1)
        importance: Önem skoru (0-1)
        source_message_id: Kaynak mesaj ID
    
    Returns:
        Memory item ID
    """
    with get_db() as conn:
        # Önce var mı kontrol et
        cursor = conn.execute(
            "SELECT id FROM memory_items WHERE user_id = ? AND category = ? AND key = ?",
            (user_id, category, key)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Güncelle
            conn.execute('''
                UPDATE memory_items 
                SET value = ?, confidence = ?, importance = ?, 
                    source_message_id = ?, updated_at = CURRENT_TIMESTAMP, is_active = 1
                WHERE id = ?
            ''', (value, confidence, importance, source_message_id, existing[0]))
            conn.commit()
            return existing[0]
        else:
            # Yeni ekle
            cursor = conn.execute('''
                INSERT INTO memory_items 
                (user_id, category, key, value, confidence, importance, source_message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, category, key, value, confidence, importance, source_message_id))
            conn.commit()
            return cursor.lastrowid


@require_user_id
def list_memory(
    *, 
    user_id: int, 
    category: str = None, 
    active_only: bool = True
) -> List[Dict[str, Any]]:
    """Kullanıcının hafızasını listeler.
    
    Args:
        user_id: Kullanıcı ID
        category: Filtrelenecek kategori (opsiyonel)
        active_only: Sadece aktif öğeler
    
    Returns:
        Hafıza öğeleri listesi
    """
    sql = "SELECT * FROM memory_items WHERE user_id = ?"
    params = [user_id]
    
    if active_only:
        sql += " AND is_active = 1"
    
    if category:
        sql += " AND category = ?"
        params.append(category)
    
    sql += " ORDER BY importance DESC, updated_at DESC"
    
    return execute_query(sql, tuple(params), fetch='all')


@require_user_id
def get_memory(key: str, *, user_id: int, category: str = None) -> Optional[Dict[str, Any]]:
    """Belirli bir hafıza öğesini döner.
    
    Args:
        key: Anahtar
        user_id: Kullanıcı ID
        category: Kategori (opsiyonel)
    
    Returns:
        Hafıza öğesi veya None
    """
    if category:
        return execute_query(
            "SELECT * FROM memory_items WHERE user_id = ? AND category = ? AND key = ? AND is_active = 1",
            (user_id, category, key),
            fetch='one'
        )
    else:
        return execute_query(
            "SELECT * FROM memory_items WHERE user_id = ? AND key = ? AND is_active = 1",
            (user_id, key),
            fetch='one'
        )


@require_user_id
def delete_memory(key: str, *, user_id: int, category: str = None, hard_delete: bool = False) -> bool:
    """Hafıza öğesini siler veya pasifleştirir.
    
    Args:
        key: Anahtar
        user_id: Kullanıcı ID
        category: Kategori (opsiyonel)
        hard_delete: True ise tamamen sil, False ise pasifleştir
    
    Returns:
        Başarılı mı
    """
    with get_db() as conn:
        if hard_delete:
            if category:
                cursor = conn.execute(
                    "DELETE FROM memory_items WHERE user_id = ? AND category = ? AND key = ?",
                    (user_id, category, key)
                )
            else:
                cursor = conn.execute(
                    "DELETE FROM memory_items WHERE user_id = ? AND key = ?",
                    (user_id, key)
                )
        else:
            if category:
                cursor = conn.execute(
                    "UPDATE memory_items SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND category = ? AND key = ?",
                    (user_id, category, key)
                )
            else:
                cursor = conn.execute(
                    "UPDATE memory_items SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND key = ?",
                    (user_id, key)
                )
        conn.commit()
        return cursor.rowcount > 0


@require_user_id
def clear_all_memory(*, user_id: int, hard_delete: bool = False) -> int:
    """Kullanıcının tüm hafızasını temizler.
    
    Args:
        user_id: Kullanıcı ID
        hard_delete: True ise tamamen sil
    
    Returns:
        Etkilenen satır sayısı
    """
    with get_db() as conn:
        if hard_delete:
            cursor = conn.execute("DELETE FROM memory_items WHERE user_id = ?", (user_id,))
        else:
            cursor = conn.execute(
                "UPDATE memory_items SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
        conn.commit()
        return cursor.rowcount


# ============== PROFILE SUMMARY ==============

@require_user_id
def get_profile_summary(*, user_id: int) -> Optional[str]:
    """Kullanıcı profil özetini döner.
    
    Args:
        user_id: Kullanıcı ID
    
    Returns:
        Profil özeti veya None
    """
    result = execute_query(
        "SELECT summary_text FROM user_profile_summary WHERE user_id = ?",
        (user_id,),
        fetch='one'
    )
    return result['summary_text'] if result else None


@require_user_id
def update_profile_summary(summary: str, *, user_id: int) -> bool:
    """Profil özetini günceller (upsert).
    
    Args:
        summary: Yeni özet
        user_id: Kullanıcı ID
    
    Returns:
        Başarılı mı
    """
    with get_db() as conn:
        cursor = conn.execute("SELECT id FROM user_profile_summary WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.execute(
                "UPDATE user_profile_summary SET summary_text = ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?",
                (summary, user_id)
            )
        else:
            conn.execute(
                "INSERT INTO user_profile_summary (user_id, summary_text) VALUES (?, ?)",
                (user_id, summary)
            )
        conn.commit()
        return True


# ============== MEMORY SETTINGS ==============

def is_memory_enabled(user_id: int) -> bool:
    """Kullanıcının hafıza özelliği açık mı?
    
    Args:
        user_id: Kullanıcı ID
    
    Returns:
        True ise açık
    """
    if not user_id or user_id <= 0:
        return False
    
    result = execute_query(
        "SELECT memory_enabled FROM user_preferences WHERE user_id = ?",
        (user_id,),
        fetch='one'
    )
    # Varsayılan: açık
    return result['memory_enabled'] == 1 if result else True


def set_memory_enabled(user_id: int, enabled: bool) -> bool:
    """Hafıza özelliğini aç/kapat.
    
    Args:
        user_id: Kullanıcı ID
        enabled: True ise aç
    
    Returns:
        Başarılı mı
    """
    if not user_id or user_id <= 0:
        return False
    
    with get_db() as conn:
        cursor = conn.execute("SELECT id FROM user_preferences WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.execute(
                "UPDATE user_preferences SET memory_enabled = ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ?",
                (1 if enabled else 0, user_id)
            )
        else:
            conn.execute(
                "INSERT INTO user_preferences (user_id, memory_enabled) VALUES (?, ?)",
                (user_id, 1 if enabled else 0)
            )
        conn.commit()
        return True


# ============== MEMORY EVENTS ==============

@require_user_id
def log_memory_event(event_type: str, content: str, *, user_id: int) -> int:
    """Hafıza olayı loglar.
    
    Args:
        event_type: Olay tipi (extract, update, delete, command)
        content: Olay içeriği (maskelenmiş)
        user_id: Kullanıcı ID
    
    Returns:
        Event ID
    """
    return execute_query(
        "INSERT INTO memory_events (user_id, event_type, content) VALUES (?, ?, ?)",
        (user_id, event_type, content),
        fetch='none'
    )


# ============== MEMORY FORMATTING ==============

@require_user_id
def get_memory_as_text(*, user_id: int, max_items: int = 20) -> str:
    """Hafızayı metin formatında döner (LLM context için).
    
    Args:
        user_id: Kullanıcı ID
        max_items: Maksimum öğe sayısı
    
    Returns:
        Formatlanmış hafıza metni
    """
    if not is_memory_enabled(user_id):
        return ""
    
    items = list_memory(user_id=user_id, active_only=True)[:max_items]
    profile = get_profile_summary(user_id=user_id)
    
    if not items and not profile:
        return ""
    
    lines = ["USER_MEMORY:"]
    
    if profile:
        lines.append(f"Profil: {profile}")
    
    # Kategoriye göre grupla
    by_category = {}
    for item in items:
        cat = item.get('category', 'general')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    for cat, cat_items in by_category.items():
        for item in cat_items:
            lines.append(f"- [{cat}] {item['key']}: {item['value']}")
    
    return "\n".join(lines)

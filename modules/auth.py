"""
Authentication Module - Multi-Tenant Ready
===========================================
Login, register, password hashing ve session yonetimi.
"""

import bcrypt
import streamlit as st
from typing import Optional
from .db import get_db, execute_query


def hash_password(password: str) -> str:
    """Sifreyi bcrypt ile hashler.
    
    Args:
        password: Plain text sifre
        
    Returns:
        Hashlenmiş sifre (string)
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Sifreyi hash ile dogrular.
    
    Args:
        password: Plain text sifre
        password_hash: Veritabanindaki hash
        
    Returns:
        True eger sifre dogru ise
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            password_hash.encode('utf-8')
        )
    except Exception:
        return False


def get_user_by_email(email: str) -> Optional[dict]:
    """Email ile kullanici bilgilerini getirir.
    
    Args:
        email: Kullanici email adresi
        
    Returns:
        User dict veya None
    """
    return execute_query(
        "SELECT id, email, password_hash, name, is_active FROM users WHERE email = ?",
        (email.lower().strip(),),
        fetch='one'
    )


def get_user_by_id(user_id: int) -> Optional[dict]:
    """ID ile kullanici bilgilerini getirir.
    
    Args:
        user_id: Kullanici ID
        
    Returns:
        User dict veya None
    """
    return execute_query(
        "SELECT id, email, name, is_active, created_at FROM users WHERE id = ?",
        (user_id,),
        fetch='one'
    )


def login(email: str, password: str) -> Optional[dict]:
    """Kullanici girisi yapar.
    
    GUVENLIK: Basarisiz durumda None doner - generic mesaj icin.
    Hata mesajinda email'in var olup olmadigi belli olmamali.
    
    Args:
        email: Kullanici email adresi
        password: Plain text sifre
        
    Returns:
        User dict (id, email, name) veya None
    """
    email = email.lower().strip()
    user = get_user_by_email(email)
    
    if not user:
        return None  # Generic - enumeration korumasi
    
    if not user.get('is_active', True):
        return None  # Deaktif kullanici
    
    if not verify_password(password, user['password_hash']):
        return None  # Yanlis sifre
    
    # Update last login
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user['id'],)
        )
        conn.commit()
    
    return {
        'id': user['id'],
        'email': user['email'],
        'name': user['name']
    }


def register(email: str, password: str, name: str) -> Optional[int]:
    """Yeni kullanici kaydeder.
    
    Args:
        email: Kullanici email adresi
        password: Plain text sifre
        name: Kullanici adi
        
    Returns:
        Yeni user_id veya None (email zaten varsa)
    """
    email = email.lower().strip()
    
    # Email kontrolu
    existing = get_user_by_email(email)
    if existing:
        return None
    
    # Sifre validasyonu
    if len(password) < 6:
        raise ValueError("Sifre en az 6 karakter olmali")
    
    # Kullanici olustur
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            (email, hash_password(password), name.strip())
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        # Default preferences olustur
        conn.execute(
            "INSERT INTO user_preferences (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()
        
        return user_id


def get_current_user_id() -> Optional[int]:
    """Session'dan aktif user_id'yi doner.
    
    Returns:
        user_id veya None (login olmamis ise)
    """
    return st.session_state.get('user_id')


def get_current_user() -> Optional[dict]:
    """Session'dan aktif kullanici bilgilerini doner.
    
    Returns:
        User dict veya None
    """
    return st.session_state.get('user')


def is_logged_in() -> bool:
    """Kullanici giris yapmis mi kontrol eder."""
    return st.session_state.get('logged_in', False) and get_current_user_id() is not None


def set_session(user: dict):
    """Login sonrasi session'u ayarlar.
    
    Args:
        user: login() fonksiyonundan donen user dict
    """
    st.session_state['user_id'] = user['id']
    st.session_state['user'] = user
    st.session_state['logged_in'] = True
    st.session_state['messages'] = []  # Yeni sohbet


def clear_session():
    """Logout - tum kullanici verilerini temizler.
    
    GUVENLIK: Session fixation ve veri sizintisi onlemi.
    """
    keys_to_clear = [
        'user_id', 'user', 'logged_in', 'messages',
        'vectorstore', 'current_model_id', 'conversation_id',
        'selected_model', 'uploaded_files'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Cache temizligi
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
    except Exception:
        pass  # Cache clear bazi durumlarda hata verebilir


def require_login(func):
    """Decorator: Login olmadan erisimi engeller.
    
    Usage:
        @require_login
        def protected_page():
            ...
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            st.warning("Bu sayfayi goruntulemek icin giris yapin.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def update_password(user_id: int, old_password: str, new_password: str) -> bool:
    """Kullanici sifresini gunceller.
    
    Args:
        user_id: Kullanici ID
        old_password: Mevcut sifre
        new_password: Yeni sifre
        
    Returns:
        True eger guncelleme basarili ise
    """
    user = execute_query(
        "SELECT password_hash FROM users WHERE id = ?",
        (user_id,),
        fetch='one'
    )
    
    if not user or not verify_password(old_password, user['password_hash']):
        return False
    
    if len(new_password) < 6:
        return False
    
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user_id)
        )
        conn.commit()
    
    return True

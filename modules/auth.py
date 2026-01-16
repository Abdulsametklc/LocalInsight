"""
Authentication Module
Kullanıcı kimlik doğrulama ve oturum yönetimi.
"""

import sqlite3
import hashlib
import os
from datetime import datetime

DB_NAME = "LocalInsights.db"

def get_connection():
    """Veritabanı bağlantısı oluşturur."""
    return sqlite3.connect(DB_NAME)

def init_auth_db():
    """Kimlik doğrulama tablolarını oluşturur."""
    conn = get_connection()
    c = conn.cursor()
    
    # Kullanıcılar tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME
    )''')
    
    # Mevcut tabloya full_name kolonu ekle (varsa geç)
    try:
        c.execute('ALTER TABLE users ADD COLUMN full_name TEXT')
    except:
        pass
    
    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    """Şifreyi güvenli şekilde hashler."""
    if salt is None:
        salt = os.urandom(32).hex()
    
    # PBKDF2 benzeri basit hash (production'da bcrypt kullanılmalı)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    
    return password_hash, salt

def register_user(email, password, full_name=""):
    """
    Yeni kullanıcı kaydı yapar.
    
    Returns:
        tuple: (success: bool, message: str, user_id: int or None)
    """
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # Email kontrolü
        c.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
        if c.fetchone():
            conn.close()
            return False, "Bu email adresi zaten kayıtlı.", None
        
        # Şifre hash'le
        password_hash, salt = hash_password(password)
        
        # Kullanıcı ekle
        c.execute(
            "INSERT INTO users (email, full_name, password_hash, salt) VALUES (?, ?, ?, ?)",
            (email.lower(), full_name.strip(), password_hash, salt)
        )
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return True, "Kayıt başarılı!", user_id
    
    except Exception as e:
        conn.close()
        return False, f"Kayıt hatası: {e}", None

def login_user(email, password):
    """
    Kullanıcı girişi yapar.
    
    Returns:
        tuple: (success: bool, message: str, user_data: dict or None)
    """
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # Kullanıcıyı bul
        c.execute(
            "SELECT id, email, full_name, password_hash, salt FROM users WHERE email = ?",
            (email.lower(),)
        )
        user = c.fetchone()
        
        if not user:
            conn.close()
            return False, "Bu email adresi kayıtlı değil.", None
        
        user_id, user_email, full_name, stored_hash, salt = user
        
        # Şifre kontrolü
        password_hash, _ = hash_password(password, salt)
        
        if password_hash != stored_hash:
            conn.close()
            return False, "Şifre hatalı.", None
        
        # Son giriş zamanını güncelle
        c.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now(), user_id)
        )
        conn.commit()
        conn.close()
        
        return True, "Giriş başarılı!", {
            'id': user_id,
            'email': user_email,
            'name': full_name if full_name else user_email.split('@')[0]
        }
    
    except Exception as e:
        conn.close()
        return False, f"Giriş hatası: {e}", None

def get_user_by_id(user_id):
    """Kullanıcı bilgilerini getirir."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, email, created_date, last_login FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'email': user[1],
            'created_date': user[2],
            'last_login': user[3]
        }
    return None

def change_password(user_id, old_password, new_password):
    """Şifre değiştirir."""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # Mevcut kullanıcıyı al
        c.execute("SELECT password_hash, salt FROM users WHERE id = ?", (user_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return False, "Kullanıcı bulunamadı."
        
        stored_hash, salt = result
        
        # Eski şifre kontrolü
        old_hash, _ = hash_password(old_password, salt)
        if old_hash != stored_hash:
            conn.close()
            return False, "Mevcut şifre hatalı."
        
        # Yeni şifre hash'le
        new_hash, new_salt = hash_password(new_password)
        
        # Güncelle
        c.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
            (new_hash, new_salt, user_id)
        )
        conn.commit()
        conn.close()
        
        return True, "Şifre başarıyla değiştirildi."
    
    except Exception as e:
        conn.close()
        return False, f"Şifre değiştirme hatası: {e}"

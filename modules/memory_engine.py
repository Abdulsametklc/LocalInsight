"""
Memory Engine Module
=====================
LLM tabanlı hafıza çıkarımı, policy filter ve context oluşturma.
Güvenlik: Hassas veri filtreleme, user izolasyonu garantili.
"""

import json
import re
from typing import Dict, List, Any, Optional
from langchain_ollama import ChatOllama


# ============== HASSAS VERİ PATTERN'LERİ ==============

BLOCKED_PATTERNS = [
    r'\b\d{11}\b',                    # TC kimlik numarası
    r'\b\d{16}\b',                    # Kredi kartı numarası
    r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Kredi kartı formatlı
    r'TR\d{24}',                      # IBAN
    r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b',  # Genel IBAN
    r'password|şifre|parola|sifre',   # Şifre kelimeleri
    r'api[_-]?key|token|secret|bearer',  # API anahtarları
    r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Telefon numarası
    r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}\b',  # TR telefon
    r'\b[05]\d{9}\b',                 # TR cep telefonu
    r'cvv|cvc|güvenlik.kodu',         # Kart güvenlik kodu
]

BLOCKED_CATEGORIES = [
    'password', 'credit_card', 'bank_account', 'ssn', 'tc_kimlik',
    'address', 'phone_number', 'medical', 'health'
]


# ============== MEMORY EXTRACTION PROMPT ==============

MEMORY_EXTRACTION_PROMPT = """Sen bir hafıza çıkarım asistanısın.
Kullanıcı mesajından kişisel bilgileri tespit edip JSON formatında çıkar.

MESAJ:
{message}

GÖREV:
1. Mesajda saklanabilecek kişisel bilgi var mı tespit et
2. Varsa kategorize et ve key-value olarak çıkar
3. Kullanıcı komutlarını tespit et

KATEGORİLER:
- profile: isim, yaş, meslek, okul, uzmanlık
- preferences: yanıt tarzı, dil, format tercihi  
- goals: hedefler, planlar, öğrenmek istediği konular
- context: mevcut projeler, dersler, çalışma alanı
- constraints: kısıtlamalar, yapmak istemediği şeyler

YASAKLAR (ASLA SAKLAMA):
- Şifre, TC kimlik, kredi kartı, IBAN
- Telefon numarası, adres, sağlık bilgisi

KULLANICI KOMUTLARI:
- "hafızamda ne var" -> show_memory: true
- "bunu unut: X" -> forget_keys: ["X"]
- "şunu güncelle: X=Y" -> update_pairs: {{"X": "Y"}}
- "hafızamı kapat/kaldır" -> disable_memory: true

JSON FORMATI:
{{
  "should_write": true/false,
  "items": [
    {{"category": "...", "key": "...", "value": "...", "confidence": 0.0-1.0, "importance": 0.0-1.0}}
  ],
  "user_commands": {{
    "show_memory": false,
    "forget_keys": [],
    "update_pairs": {{}},
    "disable_memory": false
  }}
}}

SADECE JSON döndür, başka açıklama yazma:"""


# ============== MEMORY EXTRACTION ==============

def extract_memory(model_name: str, user_message: str, chat_history: list = None) -> Dict[str, Any]:
    """Mesajdan hafıza bilgisi çıkarır.
    
    Args:
        model_name: Kullanılacak LLM modeli
        user_message: Kullanıcı mesajı
        chat_history: Sohbet geçmişi (opsiyonel)
    
    Returns:
        Parsed memory JSON
    """
    try:
        llm = ChatOllama(model=model_name, temperature=0.1)
        prompt = MEMORY_EXTRACTION_PROMPT.format(message=user_message)
        
        response = llm.invoke(prompt)
        return _parse_memory_json(response.content)
    except Exception as e:
        print(f"Memory extraction error: {e}")
        return _empty_memory_result()


def _parse_memory_json(response_text: str) -> Dict[str, Any]:
    """LLM yanıtından JSON parse eder.
    
    Args:
        response_text: LLM yanıtı
    
    Returns:
        Parsed dict veya boş sonuç
    """
    try:
        # JSON bloğunu bul
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            return json.loads(json_match.group())
        return _empty_memory_result()
    except json.JSONDecodeError:
        return _empty_memory_result()


def _empty_memory_result() -> Dict[str, Any]:
    """Boş hafıza sonucu döner."""
    return {
        "should_write": False,
        "items": [],
        "user_commands": {
            "show_memory": False,
            "forget_keys": [],
            "update_pairs": {},
            "disable_memory": False
        }
    }


# ============== POLICY FILTER ==============

def apply_policy_filter(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Hassas verileri filtreler.
    
    Args:
        items: Hafıza öğeleri listesi
    
    Returns:
        Temizlenmiş liste
    """
    filtered = []
    for item in items:
        # Kategori kontrolü
        if item.get('category', '').lower() in BLOCKED_CATEGORIES:
            continue
        
        # Key kontrolü
        if item.get('key', '').lower() in BLOCKED_CATEGORIES:
            continue
        
        # Value kontrolü
        value = str(item.get('value', ''))
        if _contains_sensitive(value):
            continue
        
        # Key'de hassas kelime kontrolü
        if _contains_sensitive(item.get('key', '')):
            continue
        
        filtered.append(item)
    
    return filtered


def _contains_sensitive(text: str) -> bool:
    """Hassas veri içeriyor mu?
    
    Args:
        text: Kontrol edilecek metin
    
    Returns:
        True ise hassas veri içeriyor
    """
    if not text:
        return False
    
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# ============== MEMORY CONTEXT ==============

def build_memory_context(user_id: int) -> str:
    """Kullanıcı hafızasından LLM context oluşturur.
    
    Args:
        user_id: Kullanıcı ID
    
    Returns:
        Formatlanmış memory context
    """
    from .repo_memory import get_memory_as_text, is_memory_enabled
    
    if not user_id or user_id <= 0:
        return ""
    
    if not is_memory_enabled(user_id):
        return ""
    
    return get_memory_as_text(user_id=user_id, max_items=20)


def get_memory_system_prompt(user_id: int) -> str:
    """Kişiselleştirilmiş system prompt oluşturur.
    
    Args:
        user_id: Kullanıcı ID
    
    Returns:
        System prompt eki
    """
    memory_context = build_memory_context(user_id)
    
    if not memory_context:
        return ""
    
    return f"""
=== KİŞİSELLEŞTİRME TALİMATLARI ===
Aşağıdaki USER_MEMORY SADECE bu kullanıcıya aittir.
- Bu bilgileri yanıtlarını kişiselleştirmek için kullan.
- Başka kullanıcılarla ilgili hiçbir bilgiyi çıkarma veya paylaşma.
- Memory sadece bağlam ve tercih içindir, kimlik doğrulama DEĞİLDİR.
- Hassas bilgi (şifre, TC no, kart no) içeren istekleri REDDET.

{memory_context}
"""


# ============== MEMORY PROCESSING ==============

def process_memory_extraction(
    model_name: str, 
    user_message: str, 
    user_id: int,
    auto_save: bool = True
) -> Dict[str, Any]:
    """Tam hafıza işleme pipeline'ı.
    
    Args:
        model_name: LLM modeli
        user_message: Kullanıcı mesajı
        user_id: Kullanıcı ID
        auto_save: Otomatik kaydet
    
    Returns:
        İşleme sonucu
    """
    from .repo_memory import (
        upsert_memory, delete_memory, list_memory, 
        set_memory_enabled, is_memory_enabled, log_memory_event
    )
    
    result = {
        "extracted": False,
        "saved_count": 0,
        "command_responses": []
    }
    
    # Hafıza kapalıysa sadece komutları işle
    memory_enabled = is_memory_enabled(user_id)
    
    # Hafıza çıkar
    extraction = extract_memory(model_name, user_message)
    
    # Kullanıcı komutlarını işle
    commands = extraction.get('user_commands', {})
    
    if commands.get('show_memory'):
        items = list_memory(user_id=user_id, active_only=True)
        result["command_responses"].append({
            "type": "show_memory",
            "data": items
        })
    
    if commands.get('forget_keys'):
        for key in commands['forget_keys']:
            delete_memory(key, user_id=user_id)
        result["command_responses"].append({
            "type": "forget",
            "keys": commands['forget_keys']
        })
    
    if commands.get('update_pairs'):
        for key, value in commands['update_pairs'].items():
            upsert_memory('general', key, value, user_id=user_id)
        result["command_responses"].append({
            "type": "update",
            "pairs": commands['update_pairs']
        })
    
    if commands.get('disable_memory'):
        set_memory_enabled(user_id, False)
        result["command_responses"].append({
            "type": "disable_memory"
        })
    
    # Hafıza kapalıysa veya yazma gerekli değilse çık
    if not memory_enabled or not extraction.get('should_write'):
        return result
    
    # Policy filter uygula
    items = extraction.get('items', [])
    filtered_items = apply_policy_filter(items)
    
    # Kaydet
    if auto_save and filtered_items:
        for item in filtered_items:
            try:
                upsert_memory(
                    category=item.get('category', 'general'),
                    key=item.get('key', 'unknown'),
                    value=item.get('value', ''),
                    user_id=user_id,
                    confidence=item.get('confidence', 0.5),
                    importance=item.get('importance', 0.5)
                )
                result["saved_count"] += 1
            except Exception as e:
                print(f"Memory save error: {e}")
        
        # Log event (maskeli)
        log_memory_event(
            'extract',
            f"Saved {result['saved_count']} items",
            user_id=user_id
        )
    
    result["extracted"] = True
    return result


# ============== USER COMMAND DETECTION ==============

def detect_memory_command(message: str) -> Optional[str]:
    """Mesajda hafıza komutu var mı tespit eder.
    
    Args:
        message: Kullanıcı mesajı
    
    Returns:
        Komut tipi veya None
    """
    message_lower = message.lower()
    
    if any(phrase in message_lower for phrase in ["hafızamda ne var", "ne biliyorsun", "hafızamı göster"]):
        return "show_memory"
    
    if any(phrase in message_lower for phrase in ["bunu unut", "sil:", "kaldır:"]):
        return "forget"
    
    if any(phrase in message_lower for phrase in ["güncelle:", "değiştir:"]):
        return "update"
    
    if any(phrase in message_lower for phrase in ["hafızamı kapat", "hafızamı kaldır", "beni unutma"]):
        return "disable"
    
    if any(phrase in message_lower for phrase in ["hafızamı aç", "hatırla"]):
        return "enable"
    
    return None


def format_memory_response(command_responses: List[Dict]) -> str:
    """Hafıza komut yanıtlarını formatlı metin olarak döner.
    
    Args:
        command_responses: Komut yanıtları listesi
    
    Returns:
        Formatlı yanıt
    """
    if not command_responses:
        return ""
    
    lines = []
    
    for resp in command_responses:
        if resp["type"] == "show_memory":
            items = resp.get("data", [])
            if items:
                lines.append("📝 **Hafızamdaki Bilgiler:**")
                for item in items:
                    lines.append(f"- [{item.get('category', 'general')}] **{item['key']}**: {item['value']}")
            else:
                lines.append("📝 Hafızamda henüz kayıtlı bilgi yok.")
        
        elif resp["type"] == "forget":
            keys = resp.get("keys", [])
            lines.append(f"🗑️ Silinen bilgiler: {', '.join(keys)}")
        
        elif resp["type"] == "update":
            pairs = resp.get("pairs", {})
            for k, v in pairs.items():
                lines.append(f"✏️ Güncellendi: {k} = {v}")
        
        elif resp["type"] == "disable_memory":
            lines.append("🔒 Hafıza özelliği kapatıldı. Bundan sonra bilgilerinizi saklamayacağım.")
    
    return "\n".join(lines)

# 📋 HAZIR KOD - DOĞRUDANKOPYALAYABİLİRSİNİZ

import re
from difflib import SequenceMatcher

def tokenize_string(text):
    """String'i kelime ve özel karakterlere ayır"""
    if not text:
        return []
    tokens = re.findall(r'\b\w+\b|[^\w\s]', str(text).lower())
    return [token for token in tokens if token.strip()]

def is_number(text):
    """String'in sayı olup olmadığını kontrol et"""
    try:
        float(text)
        return True
    except ValueError:
        return False

def word_similarity(word1, word2):
    """İki kelime arasındaki benzerliği hesapla"""
    if not word1 or not word2:
        return 0.0
    
    word1, word2 = word1.lower(), word2.lower()
    
    # Tam eşleşme
    if word1 == word2:
        return 1.0
    
    # Sayılar için özel handling
    if is_number(word1) and is_number(word2):
        return 0.1 if abs(float(word1) - float(word2)) < 10 else 0.0
    
    # Biri sayı diğeri değilse benzerlik yok
    if is_number(word1) != is_number(word2):
        return 0.0
    
    # String'ler için fuzzy + substring
    fuzzy_score = SequenceMatcher(None, word1, word2).ratio()
    
    shorter, longer = (word1, word2) if len(word1) < len(word2) else (word2, word1)
    if shorter in longer and len(shorter) >= 3:
        substring_bonus = 0.3
    else:
        substring_bonus = 0.0
    
    return min(1.0, fuzzy_score + substring_bonus)

def improved_similarity_score(strings1, strings2):
    """
    GELİŞTİRİLMİŞ SİMİLARİTY SCORE - Kelime bazında
    ESKİ similarity_score FONKSIYONUNUN YERİNE KULLANIN
    """
    if not strings1 or not strings2:
        return 0.0
    
    # String'leri listeye çevir
    if isinstance(strings1, str):
        strings1 = [strings1]
    if isinstance(strings2, str):
        strings2 = [strings2]
    
    # Tüm stringleri tokenize et
    all_tokens1 = []
    all_tokens2 = []
    
    for s in strings1:
        all_tokens1.extend(tokenize_string(s))
    
    for s in strings2:
        all_tokens2.extend(tokenize_string(s))
    
    if not all_tokens1 or not all_tokens2:
        return 0.0
    
    # Kelime bazında en iyi eşleşmeleri bul
    total_score = 0.0
    used_indices = set()
    
    for token1 in all_tokens1:
        best_score = 0.0
        best_idx = -1
        
        for i, token2 in enumerate(all_tokens2):
            if i in used_indices:
                continue
                
            similarity = word_similarity(token1, token2)
            if similarity > best_score:
                best_score = similarity
                best_idx = i
        
        if best_idx != -1:
            used_indices.add(best_idx)
            total_score += best_score
    
    max_tokens = max(len(all_tokens1), len(all_tokens2))
    return total_score / max_tokens

# ===================================================================
# 🚀 KULLANIM ÖRNEĞİ - ESKİ KODUNUZU BU ŞEKİLDE DEĞİŞTİRİN:
# ===================================================================

def example_usage():
    """Nasıl kullanacağınızın örneği"""
    
    # ESKİ KODUNUZ:
    # sim = similarity_score(str(yval), str(mval))
    
    # YENİ KODUNUZ:
    sim = improved_similarity_score(str("yval"), str("mval"))
    
    return sim

# ===================================================================
# 🧪 TEST - ÇALIŞTIĞINI GÖRMEK İÇİN
# ===================================================================

if __name__ == "__main__":
    print("🔧 GELİŞTİRİLMİŞ SİMİLARİTY SCORE TESTİ")
    print("=" * 50)
    
    # Probleminizi test et
    result1 = improved_similarity_score("4105", "1450")
    print(f"❌ Eski problem: '4105' vs '1450' = {result1:.3f} (artık 0.0)")
    
    result2 = improved_similarity_score("4688", "4688")
    print(f"✅ Aynı sayılar: '4688' vs '4688' = {result2:.3f}")
    
    result3 = improved_similarity_score("TruffleScout.exe", "Truffle.exe")
    print(f"✅ Substring: 'TruffleScout.exe' vs 'Truffle.exe' = {result3:.3f}")
    
    result4 = improved_similarity_score("powershell.exe", "pwsh.exe")
    print(f"✅ Abbreviation: 'powershell.exe' vs 'pwsh.exe' = {result4:.3f}")
    
    print(f"\n🎯 BAŞARI! Artık sayılar yanlış eşleşmiyor.")
    print(f"💡 Bu fonksiyonu kodunuzda kullanın!")
import yaml
import pymongo
import re
from difflib import SequenceMatcher

class YourUpdatedClass:
    def __init__(self, mongo_connection_string):
        self.client = pymongo.MongoClient(mongo_connection_string)
        self.collection = self.client["sigmaDB"]["rules"]
    
    def tokenize_string(self, text):
        """String'i kelime ve özel karakterlere ayır"""
        if not text:
            return []
        
        # Kelimeler, sayılar, özel karakterleri ayrı ayrı yakala
        tokens = re.findall(r'\b\w+\b|[^\w\s]', str(text).lower())
        return [token for token in tokens if token.strip()]
    
    def is_number(self, text):
        """String'in sayı olup olmadığını kontrol et"""
        try:
            float(text)
            return True
        except ValueError:
            return False
    
    def word_similarity(self, word1, word2):
        """İki kelime arasındaki benzerliği hesapla"""
        if not word1 or not word2:
            return 0.0
        
        word1, word2 = word1.lower(), word2.lower()
        
        # Tam eşleşme
        if word1 == word2:
            return 1.0
        
        # Sayılar için özel handling
        if self.is_number(word1) and self.is_number(word2):
            # Sayılarda tam eşleşme yoksa benzerlik çok düşük
            return 0.1 if abs(float(word1) - float(word2)) < 10 else 0.0
        
        # Biri sayı diğeri değilse benzerlik yok
        if self.is_number(word1) != self.is_number(word2):
            return 0.0
        
        # String'ler için fuzzy + substring
        fuzzy_score = SequenceMatcher(None, word1, word2).ratio()
        
        # Substring bonus (kelime seviyesinde)
        shorter, longer = (word1, word2) if len(word1) < len(word2) else (word2, word1)
        if shorter in longer and len(shorter) >= 3:  # En az 3 harf olsun
            substring_bonus = 0.3
        else:
            substring_bonus = 0.0
        
        return min(1.0, fuzzy_score + substring_bonus)
    
    def fuzzy_similarity(self, strings1, strings2):
        """
        GELİŞTİRİLMİŞ FUZZY SİMİLARİTY - Kelime bazında karşılaştırma
        *** BU FONKSİYONU ESKİ FONKSİYONUNUZUN YERİNE KULLANIN ***
        """
        if not strings1 or not strings2:
            return 0.0
        
        # Tüm stringleri tokenize et
        all_tokens1 = []
        all_tokens2 = []
        
        for s in strings1:
            all_tokens1.extend(self.tokenize_string(s))
        
        for s in strings2:
            all_tokens2.extend(self.tokenize_string(s))
        
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
                    
                similarity = self.word_similarity(token1, token2)
                if similarity > best_score:
                    best_score = similarity
                    best_idx = i
            
            if best_idx != -1:
                used_indices.add(best_idx)
                total_score += best_score
        
        # Ortalama hesapla
        max_tokens = max(len(all_tokens1), len(all_tokens2))
        return total_score / max_tokens
    
    # ESKİ KODUNUZUN GLANLI - sadece fuzzy_similarity fonksiyonunu değiştirin
    def get_all_strings_from_detection(self, detection):
        """Detection'dan tüm string değerleri çıkar - DEĞİŞTİRMEYİN"""
        all_strings = []
        
        def extract_strings(obj):
            if isinstance(obj, str):
                all_strings.append(obj)
            elif isinstance(obj, (int, float)):
                all_strings.append(str(obj))
            elif isinstance(obj, list):
                for item in obj:
                    extract_strings(item)
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    if key != 'condition':
                        extract_strings(value)
        
        extract_strings(detection)
        return all_strings

# KULLANIM ÖRNEĞİ - ESKİ KODUNUZU NASIL GÜNCELLEYECEĞİNİZ
def show_integration_example():
    print("💡 ESKİ KODUNUZU GÜNCELLEME ÖRNEĞİ:")
    print("=" * 50)
    
    print("""
# ESKİ KODUNUZ BU ŞEKİLDEYDİ:
def similarity_score(str1, str2):
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

# YENİ KODUNUZ BU ŞEKİLDE OLACAK:
class YourClass:
    def __init__(self, mongo_connection):
        # ... mevcut kodunuz ...
        pass
    
    # Bu 4 fonksiyonu sınıfınıza ekleyin:
    def tokenize_string(self, text): ...
    def is_number(self, text): ...  
    def word_similarity(self, word1, word2): ...
    def fuzzy_similarity(self, strings1, strings2): ...  # ESKİ FONKSİYONU DEĞİŞTİRİN
    
    # Ana kodunuzda değişiklik:
    def calculate_similarity(self, yaml_values, mongo_values):
        # ESKİ: 
        # sim = similarity_score(str(yval), str(mval))
        
        # YENİ:
        sim = self.fuzzy_similarity([str(yval)], [str(mval)])
        
        return sim
""")

if __name__ == "__main__":
    show_integration_example()
    
    # Test
    print("\n🧪 TEST:")
    test_class = YourUpdatedClass("dummy_connection")
    
    # Probleminizi test et
    result = test_class.fuzzy_similarity(["4105"], ["1450"])
    print(f"4105 vs 1450: {result:.3f} ✅ (artık 0.0)")
    
    result2 = test_class.fuzzy_similarity(["TruffleScout.exe"], ["Truffle.exe"]) 
    print(f"TruffleScout vs Truffle: {result2:.3f} ✅ (substring detection)")
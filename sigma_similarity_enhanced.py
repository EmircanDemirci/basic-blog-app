from collections import Counter
import math
import re
import yaml
from typing import Dict, List, Any, Union
from difflib import SequenceMatcher

class SigmaSimilarity:
    def __init__(self, sigma_rule1: Union[str, Dict], sigma_rule2: Union[str, Dict]):
        """
        Sigma kuralları arasındaki benzerliği hesaplar
        
        Args:
            sigma_rule1: İlk sigma kuralı (YAML string veya dict)
            sigma_rule2: İkinci sigma kuralı (YAML string veya dict)
        """
        self.rule1 = self._parse_sigma_rule(sigma_rule1)
        self.rule2 = self._parse_sigma_rule(sigma_rule2)
        
        # Detection bölümlerini çıkar
        self.detection1 = self.rule1.get('detection', {})
        self.detection2 = self.rule2.get('detection', {})
        
        # String içeriklerini ve field'ları ayır
        self.strings1, self.fields1 = self._extract_detection_components(self.detection1)
        self.strings2, self.fields2 = self._extract_detection_components(self.detection2)
        
    def _parse_sigma_rule(self, rule: Union[str, Dict]) -> Dict:
        """Sigma kuralını parse et"""
        if isinstance(rule, str):
            try:
                return yaml.safe_load(rule)
            except:
                # Eğer YAML parse edilemezse, sadece string olarak kabul et
                return {'detection': {'selection': rule}}
        return rule
    
    def _extract_detection_components(self, detection: Dict) -> tuple:
        """Detection bölümünden string içerikleri ve field isimlerini ayır"""
        strings = []
        fields = set()
        
        def extract_from_dict(obj, parent_key=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ['condition']:  # condition'ı field olarak sayma
                        continue
                        
                    fields.add(key)  # Field ismini ekle
                    
                    if isinstance(value, (str, int, float)):
                        strings.append(str(value))
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, (str, int, float)):
                                strings.append(str(item))
                            elif isinstance(item, dict):
                                extract_from_dict(item, key)
                    elif isinstance(value, dict):
                        extract_from_dict(value, key)
            elif isinstance(obj, list):
                for item in obj:
                    extract_from_dict(item, parent_key)
                    
        extract_from_dict(detection)
        
        return strings, fields
    
    def _tokenize(self, text: str) -> List[str]:
        """Metni tokenize et - sigma kuralları için optimize edilmiş"""
        if not text:
            return []
        
        # Özel karakterleri koruyarak tokenize et
        # Sigma kurallarında *, ?, |, \, / gibi karakterler önemli
        tokens = []
        
        # Önce kelime bazında ayır
        words = re.findall(r'\S+', text.lower())
        
        for word in words:
            # Özel karakterleri ayrı tokenlar olarak ekle
            parts = re.split(r'([*?|\\/.:-])', word)
            tokens.extend([p for p in parts if p.strip()])
            
        return tokens
    
    def _compute_character_ngram_similarity(self, str1: str, str2: str, n: int = 3) -> float:
        """
        Karakter bazında n-gram benzerliği hesapla
        TruffleScout vs Truffle gibi substring eşleşmeleri için
        """
        if not str1 or not str2:
            return 0.0
        
        if str1 == str2:
            return 1.0
            
        # N-gramları oluştur
        def get_ngrams(text, n):
            text = text.lower()
            if len(text) < n:
                return [text]
            return [text[i:i+n] for i in range(len(text) - n + 1)]
        
        ngrams1 = get_ngrams(str1, n)
        ngrams2 = get_ngrams(str2, n)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        # Jaccard similarity for n-grams
        set1 = set(ngrams1)
        set2 = set(ngrams2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _compute_substring_similarity(self, str1: str, str2: str) -> float:
        """
        Substring benzerliği hesapla
        Bir string diğerinin parçası mı kontrol et
        """
        if not str1 or not str2:
            return 0.0
            
        str1, str2 = str1.lower(), str2.lower()
        
        if str1 == str2:
            return 1.0
        
        # Dosya uzantılarını temizle (.exe, .dll vb.)
        def clean_extension(s):
            return re.sub(r'\.(exe|dll|bat|cmd|ps1|vbs|js)$', '', s)
        
        clean_str1 = clean_extension(str1)
        clean_str2 = clean_extension(str2)
        
        # Kısa olan uzun olanın substring'i mi?
        shorter, longer = (clean_str1, clean_str2) if len(clean_str1) < len(clean_str2) else (clean_str2, clean_str1)
        
        if shorter in longer:
            # Substring oranı = kısa stringin uzunluğu / uzun stringin uzunluğu
            return len(shorter) / len(longer)
        
        return 0.0
    
    def _compute_fuzzy_similarity(self, str1: str, str2: str) -> float:
        """
        Fuzzy string matching (SequenceMatcher kullanarak)
        Karakter düzeyinde benzerlik
        """
        if not str1 or not str2:
            return 0.0
            
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _compute_pairwise_string_similarity(self, strings1: List[str], strings2: List[str]) -> float:
        """
        İki string listesi arasında pairwise benzerlik hesapla
        Her string çifti için en iyi eşleşmeyi bul
        """
        if not strings1 or not strings2:
            return 0.0
        
        total_similarity = 0.0
        max_pairs = max(len(strings1), len(strings2))
        
        # Her string için en iyi eşleşmeyi bul
        used_indices = set()
        
        for str1 in strings1:
            best_sim = 0.0
            best_idx = -1
            
            for i, str2 in enumerate(strings2):
                if i in used_indices:
                    continue
                    
                # Çoklu benzerlik metriği
                char_ngram_sim = self._compute_character_ngram_similarity(str1, str2, n=3)
                substring_sim = self._compute_substring_similarity(str1, str2)
                fuzzy_sim = self._compute_fuzzy_similarity(str1, str2)
                
                # Ağırlıklı birleştirme
                combined_sim = (
                    char_ngram_sim * 0.4 +     # %40 n-gram
                    substring_sim * 0.3 +      # %30 substring
                    fuzzy_sim * 0.3            # %30 fuzzy
                )
                
                if combined_sim > best_sim:
                    best_sim = combined_sim
                    best_idx = i
            
            if best_idx != -1:
                used_indices.add(best_idx)
                total_similarity += best_sim
        
        return total_similarity / max_pairs
    
    def _compute_string_similarity(self) -> float:
        """
        GELİŞTİRİLMİŞ String içerikleri arasındaki benzerliği hesapla
        Hem word-level hem character-level benzerlik kullanır
        """
        if not self.strings1 and not self.strings2:
            return 1.0
        if not self.strings1 or not self.strings2:
            return 0.0
            
        # 1. WORD-LEVEL BENZERLIK (TF-based cosine similarity)
        text1 = " ".join(self.strings1)
        text2 = " ".join(self.strings2)
        
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        
        word_similarity = 0.0
        if tokens1 and tokens2:
            vocab = sorted(set(tokens1 + tokens2))
            
            def compute_tf(tokens):
                if not tokens:
                    return [0] * len(vocab)
                counts = Counter(tokens)
                return [counts[word] / len(tokens) for word in vocab]
            
            tf1 = compute_tf(tokens1)
            tf2 = compute_tf(tokens2)
            
            # Cosine similarity
            dot = sum(a * b for a, b in zip(tf1, tf2))
            mag1 = math.sqrt(sum(a * a for a in tf1))
            mag2 = math.sqrt(sum(b * b for b in tf2))
            
            word_similarity = dot / (mag1 * mag2) if mag1 and mag2 else 0.0
        
        # 2. CHARACTER-LEVEL BENZERLIK (pairwise string matching)
        char_similarity = self._compute_pairwise_string_similarity(self.strings1, self.strings2)
        
        # 3. BİRLEŞTİRİLMİŞ SKOR
        # %70 word-level, %30 character-level
        combined_similarity = (word_similarity * 0.7) + (char_similarity * 0.3)
        
        return combined_similarity
    
    def _compute_field_similarity(self) -> float:
        """Field yapıları arasındaki benzerliği hesapla (%20 ağırlık)"""
        if not self.fields1 and not self.fields2:
            return 1.0
        if not self.fields1 or not self.fields2:
            return 0.0
            
        # Jaccard similarity for fields
        intersection = len(self.fields1.intersection(self.fields2))
        union = len(self.fields1.union(self.fields2))
        
        return intersection / union if union > 0 else 0.0
    
    def compute_weighted_similarity(self, string_weight: float = 0.8, field_weight: float = 0.2) -> Dict[str, float]:
        """
        Ağırlıklı benzerlik skoru hesapla
        
        Args:
            string_weight: String benzerliği ağırlığı (default: 0.8)
            field_weight: Field benzerliği ağırlığı (default: 0.2)
            
        Returns:
            Dict with detailed scores
        """
        string_sim = self._compute_string_similarity()
        field_sim = self._compute_field_similarity()
        
        # Ağırlıklı toplam
        weighted_score = (string_sim * string_weight) + (field_sim * field_weight)
        
        return {
            'string_similarity': string_sim,
            'field_similarity': field_sim,
            'weighted_score': weighted_score,
            'weights': {
                'string_weight': string_weight,
                'field_weight': field_weight
            },
            'details': {
                'strings1': self.strings1,
                'strings2': self.strings2,
                'fields1': list(self.fields1),
                'fields2': list(self.fields2)
            }
        }
    
    def get_sigma_similarity(self) -> float:
        """Ana benzerlik skorunu döndür (basit kullanım için)"""
        return self.compute_weighted_similarity()['weighted_score']

# Test fonksiyonu - geliştirilmiş string matching'i test et
def test_enhanced_string_matching():
    """Geliştirilmiş string matching'i test et"""
    
    print("🧪 GELİŞTİRİLMİŞ STRING MATCHING TESTİ")
    print("=" * 60)
    
    test_cases = [
        # Substring test cases
        {
            'rule1': {
                'detection': {
                    'selection': {
                        'ProcessName': 'TruffleScout.exe',
                        'CommandLine': 'ExecutionPolicy'
                    }
                }
            },
            'rule2': {
                'detection': {
                    'selection': {
                        'ProcessName': 'Truffle.exe',
                        'CommandLine': 'ExecPolicy'
                    }
                }
            },
            'description': 'Substring Match Test (TruffleScout vs Truffle)'
        },
        
        # Character similarity test
        {
            'rule1': {
                'detection': {
                    'selection': {
                        'Image': 'powershell.exe',
                        'CommandLine': 'DownloadString'
                    }
                }
            },
            'rule2': {
                'detection': {
                    'selection': {
                        'Image': 'pwsh.exe',
                        'CommandLine': 'downloadstring'
                    }
                }
            },
            'description': 'Case Sensitivity & Abbreviation Test'
        },
        
        # Fuzzy matching test
        {
            'rule1': {
                'detection': {
                    'selection': {
                        'ProcessName': 'malware_sample.exe',
                        'CommandLine': 'persistence_mechanism'
                    }
                }
            },
            'rule2': {
                'detection': {
                    'selection': {
                        'ProcessName': 'malware_smpl.exe',
                        'CommandLine': 'persistance_mech'
                    }
                }
            },
            'description': 'Fuzzy Matching Test (typos & abbreviations)'
        },
        
        # Traditional exact match
        {
            'rule1': {
                'detection': {
                    'selection': {
                        'EventID': 4688,
                        'Image': 'cmd.exe'
                    }
                }
            },
            'rule2': {
                'detection': {
                    'selection': {
                        'EventID': 4688,
                        'Image': 'cmd.exe'
                    }
                }
            },
            'description': 'Exact Match Test (should be 100%)'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['description']}")
        print("-" * 50)
        
        sim = SigmaSimilarity(test['rule1'], test['rule2'])
        result = sim.compute_weighted_similarity()
        
        print(f"📊 TOPLAM SKOR:      {result['weighted_score']:.1%}")
        print(f"🔤 String Benzerlik: {result['string_similarity']:.1%}")
        print(f"🏷️  Field Benzerlik:  {result['field_similarity']:.1%}")
        
        # String detayları göster
        details = result['details']
        print(f"🔍 Strings1: {details['strings1']}")
        print(f"🔍 Strings2: {details['strings2']}")
        
        # Pairwise string karşılaştırması demo
        print("🔬 STRING PAIR ANALYSIS:")
        sim_obj = SigmaSimilarity(test['rule1'], test['rule2'])
        for s1 in details['strings1']:
            for s2 in details['strings2']:
                char_sim = sim_obj._compute_character_ngram_similarity(s1, s2, 3)
                substr_sim = sim_obj._compute_substring_similarity(s1, s2)
                fuzzy_sim = sim_obj._compute_fuzzy_similarity(s1, s2)
                
                if char_sim > 0.1 or substr_sim > 0.1 or fuzzy_sim > 0.1:  # Sadece anlamlı skorları göster
                    print(f"   '{s1}' ↔ '{s2}':")
                    print(f"     N-gram: {char_sim:.2f}, Substring: {substr_sim:.2f}, Fuzzy: {fuzzy_sim:.2f}")

if __name__ == "__main__":
    test_enhanced_string_matching()
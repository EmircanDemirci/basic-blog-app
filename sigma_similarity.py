from collections import Counter
import math
import re
import yaml
from typing import Dict, List, Any, Union

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
    
    def _compute_string_similarity(self) -> float:
        """String içerikleri arasındaki benzerliği hesapla (%80 ağırlık)"""
        if not self.strings1 and not self.strings2:
            return 1.0
        if not self.strings1 or not self.strings2:
            return 0.0
            
        # Tüm stringleri birleştir
        text1 = " ".join(self.strings1)
        text2 = " ".join(self.strings2)
        
        # Tokenize et
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        
        if not tokens1 and not tokens2:
            return 1.0
        if not tokens1 or not tokens2:
            return 0.0
        
        # TF-based cosine similarity (IDF'siz, 2 doküman için daha iyi)
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
        
        return dot / (mag1 * mag2) if mag1 and mag2 else 0.0
    
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

# Test fonksiyonu
def test_sigma_similarity():
    """Sigma kuralları için test örnekleri"""
    
    # Test Case 1: Benzer process creation rules
    sigma1 = {
        'detection': {
            'selection': {
                'EventID': 4688,
                'CommandLine|contains': ['powershell', '-enc', '-exec'],
                'Image|endswith': '\\powershell.exe'
            },
            'condition': 'selection'
        }
    }
    
    sigma2 = {
        'detection': {
            'selection': {
                'EventID': 4688,
                'CommandLine|contains': ['powershell', '-encoded', '-execution'],
                'Image|endswith': '\\powershell.exe'
            },
            'condition': 'selection'
        }
    }
    
    # Test Case 2: Farklı field'lar ama benzer içerik
    sigma3 = {
        'detection': {
            'selection': {
                'ProcessName': 'cmd.exe',
                'Arguments|contains': 'whoami'
            },
            'condition': 'selection'
        }
    }
    
    sigma4 = {
        'detection': {
            'selection': {
                'Image': 'cmd.exe',
                'CommandLine|contains': 'whoami'
            },
            'condition': 'selection'
        }
    }
    
    test_cases = [
        (sigma1, sigma2, "Benzer PowerShell kuralları"),
        (sigma3, sigma4, "Farklı field isimleri, benzer içerik"),
        (sigma1, sigma3, "Tamamen farklı kurallar")
    ]
    
    for rule1, rule2, description in test_cases:
        print(f"\n=== {description} ===")
        
        sim = SigmaSimilarity(rule1, rule2)
        result = sim.compute_weighted_similarity()
        
        print(f"String Similarity: {result['string_similarity']:.4f}")
        print(f"Field Similarity:  {result['field_similarity']:.4f}")
        print(f"Weighted Score:    {result['weighted_score']:.4f}")
        print(f"Fields1: {result['details']['fields1']}")
        print(f"Fields2: {result['details']['fields2']}")

if __name__ == "__main__":
    test_sigma_similarity()
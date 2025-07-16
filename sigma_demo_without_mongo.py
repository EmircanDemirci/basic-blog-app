from sigma_similarity_enhanced import SigmaSimilarity
from typing import Dict, List, Any, Union, Optional
from datetime import datetime
import json

class SigmaMemoryMatcher:
    """
    MongoDB olmadan çalışan in-memory Sigma matcher demo
    Gerçek projede MongoDB versiyonunu kullanın
    """
    def __init__(self):
        self.rules_db = []  # In-memory rule storage
        self.next_id = 1
        
    def insert_sigma_rule(self, rule: Dict, rule_id: Optional[str] = None) -> str:
        """Sigma kuralını memory'ye ekle"""
        document = {
            '_id': rule_id or str(self.next_id),
            'sigma_rule': rule,
            'title': rule.get('title', 'Untitled Rule'),
            'author': rule.get('author', 'Unknown'),
            'date': rule.get('date', datetime.now().strftime('%Y-%m-%d')),
            'level': rule.get('level', 'medium'),
            'logsource': rule.get('logsource', {}),
            'detection': rule.get('detection', {}),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        self.rules_db.append(document)
        self.next_id += 1
        
        print(f"✅ Kural eklendi: {document['_id']}")
        return str(document['_id'])
    
    def find_similar_rules(self, 
                          target_rule: Union[Dict, str],
                          similarity_threshold: float = 0.5,
                          max_results: int = 10,
                          string_weight: float = 0.8,
                          field_weight: float = 0.2) -> List[Dict]:
        """Benzer kuralları memory'den bul"""
        
        print(f"🔍 Benzer kurallar aranıyor (threshold: {similarity_threshold})")
        
        if not self.rules_db:
            print("⚠️ Memory'de kural bulunamadı")
            return []
        
        similarities = []
        
        for rule_doc in self.rules_db:
            try:
                stored_rule = rule_doc.get('sigma_rule', {})
                
                # Benzerlik hesapla
                sim = SigmaSimilarity(target_rule, stored_rule)
                result = sim.compute_weighted_similarity(string_weight, field_weight)
                
                score = result['weighted_score']
                
                # Eşik değerini kontrol et
                if score >= similarity_threshold:
                    similarity_data = {
                        'rule_id': str(rule_doc.get('_id')),
                        'title': rule_doc.get('title', 'Untitled'),
                        'author': rule_doc.get('author', 'Unknown'),
                        'level': rule_doc.get('level', 'medium'),
                        'similarity_score': score,
                        'string_similarity': result['string_similarity'],
                        'field_similarity': result['field_similarity'],
                        'sigma_rule': stored_rule,
                        'created_at': rule_doc.get('created_at'),
                        'details': result['details']
                    }
                    similarities.append(similarity_data)
                    
            except Exception as e:
                print(f"❌ Kural karşılaştırma hatası: {e}")
                continue
        
        # Benzerlik skoruna göre sırala
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Sonuç sayısını sınırla
        results = similarities[:max_results]
        
        print(f"✅ {len(results)} benzer kural bulundu")
        return results
    
    def get_best_match(self, target_rule: Union[Dict, str]) -> Optional[Dict]:
        """En benzer kuralı bul"""
        similar_rules = self.find_similar_rules(target_rule, similarity_threshold=0.0, max_results=1)
        return similar_rules[0] if similar_rules else None
    
    def check_duplicate(self, target_rule: Union[Dict, str], threshold: float = 0.9) -> Optional[Dict]:
        """Duplicate kural kontrolü"""
        duplicates = self.find_similar_rules(target_rule, similarity_threshold=threshold, max_results=1)
        return duplicates[0] if duplicates else None
    
    def bulk_insert_rules(self, rules: List[Dict]) -> List[str]:
        """Çoklu kural ekleme"""
        ids = []
        for rule in rules:
            id = self.insert_sigma_rule(rule)
            ids.append(id)
        return ids
    
    def get_all_rules(self) -> List[Dict]:
        """Tüm kuralları döndür"""
        return self.rules_db
    
    def search_by_title(self, search_term: str) -> List[Dict]:
        """Title'da arama yap"""
        results = []
        for rule in self.rules_db:
            if search_term.lower() in rule.get('title', '').lower():
                results.append(rule)
        return results

def demo_sigma_memory_matcher():
    """Memory matcher demo'su"""
    
    print("🚀 Sigma Memory Matcher Demo Başlıyor...")
    print("=" * 60)
    
    # Matcher'ı başlat
    matcher = SigmaMemoryMatcher()
    
    # Test kuralları hazırla (SigmaHQ benzeri)
    sigmahq_like_rules = [
        {
            'title': 'Suspicious PowerShell Execution',
            'author': 'Sigma Community',
            'level': 'high',
            'logsource': {'product': 'windows', 'service': 'security'},
            'detection': {
                'selection': {
                    'EventID': 4688,
                    'Image|endswith': '\\powershell.exe',
                    'CommandLine|contains': ['-ExecutionPolicy', '-enc', 'IEX', 'DownloadString']
                },
                'condition': 'selection'
            }
        },
        {
            'title': 'PowerShell Base64 Encoded Command',
            'author': 'Threat Hunter Team',
            'level': 'high',
            'logsource': {'product': 'windows', 'service': 'security'},
            'detection': {
                'selection': {
                    'EventID': 4688,
                    'Image|endswith': '\\powershell.exe',
                    'CommandLine|contains': ['-EncodedCommand', '-enc', 'FromBase64String']
                },
                'condition': 'selection'
            }
        },
        {
            'title': 'Malicious CMD Commands',
            'author': 'Security Team',
            'level': 'medium',
            'logsource': {'product': 'windows', 'service': 'security'},
            'detection': {
                'selection': {
                    'EventID': 4688,
                    'Image|endswith': '\\cmd.exe',
                    'CommandLine|contains': ['whoami', 'systeminfo', 'net user']
                },
                'condition': 'selection'
            }
        },
        {
            'title': 'PowerShell Web Download',
            'author': 'Malware Analyst',
            'level': 'high',
            'logsource': {'product': 'windows', 'service': 'security'},
            'detection': {
                'selection': {
                    'EventID': 4688,
                    'ProcessName': 'powershell.exe',  # Farklı field ismi
                    'CommandLine|contains': ['Invoke-WebRequest', 'wget', 'curl', 'DownloadFile']
                },
                'condition': 'selection'
            }
        },
        {
            'title': 'Registry Persistence Mechanism',
            'author': 'Persistence Hunter',
            'level': 'medium',
            'logsource': {'product': 'windows', 'service': 'security'},
            'detection': {
                'selection': {
                    'EventID': 4688,
                    'Image|endswith': '\\reg.exe',
                    'CommandLine|contains': ['HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run']
                },
                'condition': 'selection'
            }
        }
    ]
    
    # Kuralları "veritabanına" ekle
    print("📥 SigmaHQ benzeri kurallar ekleniyor...")
    matcher.bulk_insert_rules(sigmahq_like_rules)
    
    print(f"✅ {len(sigmahq_like_rules)} kural eklendi")
    print("=" * 60)
    
    # Yeni bir kural geldi, benzerlerini arayalım
    new_incoming_rule = {
        'title': 'Suspicious PowerShell Activity',
        'detection': {
            'selection': {
                'EventID': 4688,
                'Image|endswith': '\\powershell.exe',
                'CommandLine|contains': ['-ExecutionPolicy', 'bypass', '-enc', 'Invoke-Expression']
            },
            'condition': 'selection'
        }
    }
    
    print("🔍 YENİ KURAL İÇİN BENZERLİK TARAMASI")
    print(f"📋 Yeni Kural: {new_incoming_rule['title']}")
    print("=" * 60)
    
    # Benzer kuralları ara (düşük threshold ile)
    similar_rules = matcher.find_similar_rules(
        new_incoming_rule, 
        similarity_threshold=0.3,
        max_results=5
    )
    
    print(f"\n📊 BULUNAN {len(similar_rules)} BENZERLİK:")
    print("=" * 60)
    
    for i, rule in enumerate(similar_rules, 1):
        print(f"\n{i}. 📋 {rule['title']}")
        print(f"   👤 Yazar: {rule['author']}")
        print(f"   📊 TOPLAM SKOR: {rule['similarity_score']:.1%}")
        print(f"   🔤 String Benzerliği: {rule['string_similarity']:.1%}")
        print(f"   🏷️  Field Benzerliği: {rule['field_similarity']:.1%}")
        print(f"   ⚠️  Risk Level: {rule['level']}")
        print(f"   🔍 Rule ID: {rule['rule_id']}")
        
        # Ortak elementleri göster
        details = rule['details']
        common_strings = set(details['strings1']).intersection(set(details['strings2']))
        common_fields = set(details['fields1']).intersection(set(details['fields2']))
        
        if common_strings:
            print(f"   🔤 Ortak stringler: {common_strings}")
        if common_fields:
            print(f"   🏷️  Ortak field'lar: {common_fields}")
        
        print("-" * 50)
    
    # En iyi eşleşme
    if similar_rules:
        best = similar_rules[0]
        print(f"\n🏆 EN İYİ EŞLEŞME:")
        print(f"   📋 {best['title']}")
        print(f"   📊 Skor: {best['similarity_score']:.1%}")
        
        # Benzerlik analizi
        if best['similarity_score'] >= 0.9:
            print("   🚨 UYARI: Çok yüksek benzerlik! Duplicate olabilir")
        elif best['similarity_score'] >= 0.7:
            print("   ⚠️  DİKKAT: Yüksek benzerlik, incelenmeli")
        elif best['similarity_score'] >= 0.5:
            print("   📝 BİLGİ: Orta düzey benzerlik")
        else:
            print("   ✅ TAMAM: Düşük benzerlik, benzersiz kural")
    
    # Duplicate kontrolü demo
    print(f"\n🔍 DUPLICATE KONTROLÜ (Threshold: 90%)")
    print("=" * 60)
    
    duplicate = matcher.check_duplicate(new_incoming_rule, threshold=0.9)
    if duplicate:
        print(f"   🚨 DUPLICATE BULUNDU:")
        print(f"   📋 {duplicate['title']}")
        print(f"   📊 Benzerlik: {duplicate['similarity_score']:.1%}")
        print(f"   💡 ÖNERİ: Bu kural zaten mevcut, eklemeyebilirsiniz")
    else:
        print("   ✅ DUPLICATE YOK: Kural benzersiz, eklenebilir")
    
    # Farklı ağırlık deneme
    print(f"\n🎛️  FARKLI AĞIRLIK DENEMESİ")
    print("=" * 60)
    
    # String odaklı (%90 string, %10 field)
    string_focused = matcher.find_similar_rules(
        new_incoming_rule,
        similarity_threshold=0.3,
        max_results=1,
        string_weight=0.9,
        field_weight=0.1
    )
    
    # Field odaklı (%30 string, %70 field)
    field_focused = matcher.find_similar_rules(
        new_incoming_rule,
        similarity_threshold=0.3,
        max_results=1,
        string_weight=0.3,
        field_weight=0.7
    )
    
    if string_focused and field_focused:
        print(f"String Odaklı (%90-%10): {string_focused[0]['similarity_score']:.1%}")
        print(f"Field Odaklı (%30-%70):  {field_focused[0]['similarity_score']:.1%}")
        print(f"Standart (%80-%20):      {similar_rules[0]['similarity_score']:.1%}")
    
    print(f"\n🎯 DEMO TAMAMLANDI!")
    print("=" * 60)
    print("💡 Gerçek kullanımda MongoDB versiyonunu tercih edin:")
    print("   - SigmaMongoMatcher sınıfını kullanın")
    print("   - pip install -r requirements.txt")
    print("   - MongoDB sunucusunu çalıştırın")

if __name__ == "__main__":
    demo_sigma_memory_matcher()
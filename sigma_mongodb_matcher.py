from sigma_similarity_enhanced import SigmaSimilarity
from pymongo import MongoClient
from typing import Dict, List, Any, Union, Optional
import logging
from datetime import datetime

class SigmaMongoMatcher:
    def __init__(self, 
                 mongodb_uri: str = "mongodb://localhost:27017/",
                 database_name: str = "sigma_rules", 
                 collection_name: str = "rules"):
        """
        MongoDB entegreli Sigma kural eşleştirici
        
        Args:
            mongodb_uri: MongoDB bağlantı URI'si
            database_name: Veritabanı adı
            collection_name: Collection adı
        """
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        
        # Logging setup
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def test_connection(self) -> bool:
        """MongoDB bağlantısını test et"""
        try:
            self.client.admin.command('ping')
            self.logger.info("✅ MongoDB bağlantısı başarılı")
            return True
        except Exception as e:
            self.logger.error(f"❌ MongoDB bağlantı hatası: {e}")
            return False
    
    def insert_sigma_rule(self, rule: Dict, rule_id: Optional[str] = None) -> str:
        """
        Sigma kuralını MongoDB'ye ekle
        
        Args:
            rule: Sigma kural dict'i
            rule_id: Opsiyonel özel ID
            
        Returns:
            Eklenen dokümanın ID'si
        """
        document = {
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
        
        if rule_id:
            document['_id'] = rule_id
            
        try:
            result = self.collection.insert_one(document)
            self.logger.info(f"✅ Kural eklendi: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"❌ Kural ekleme hatası: {e}")
            raise
    
    def find_similar_rules(self, 
                          target_rule: Union[Dict, str],
                          similarity_threshold: float = 0.5,
                          max_results: int = 10,
                          string_weight: float = 0.8,
                          field_weight: float = 0.2) -> List[Dict]:
        """
        Benzer kuralları MongoDB'den bul
        
        Args:
            target_rule: Karşılaştırılacak Sigma kuralı
            similarity_threshold: Minimum benzerlik eşiği (0.0-1.0)
            max_results: Maksimum sonuç sayısı
            string_weight: String benzerliği ağırlığı
            field_weight: Field benzerliği ağırlığı
            
        Returns:
            Benzer kuralların listesi (skor ile sıralı)
        """
        self.logger.info(f"🔍 Benzer kurallar aranıyor (threshold: {similarity_threshold})")
        
        # Tüm kuralları al (büyük veri setleri için iyileştirilebilir)
        all_rules = list(self.collection.find())
        
        if not all_rules:
            self.logger.warning("⚠️ MongoDB'de kural bulunamadı")
            return []
        
        similarities = []
        
        for rule_doc in all_rules:
            try:
                # MongoDB dokümanından sigma kuralını çıkar
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
                self.logger.error(f"❌ Kural karşılaştırma hatası: {e}")
                continue
        
        # Benzerlik skoruna göre sırala (yüksekten düşüğe)
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Sonuç sayısını sınırla
        results = similarities[:max_results]
        
        self.logger.info(f"✅ {len(results)} benzer kural bulundu")
        return results
    
    def get_best_match(self, target_rule: Union[Dict, str]) -> Optional[Dict]:
        """
        En benzer kuralı bul
        
        Args:
            target_rule: Karşılaştırılacak kural
            
        Returns:
            En benzer kural veya None
        """
        similar_rules = self.find_similar_rules(target_rule, similarity_threshold=0.0, max_results=1)
        return similar_rules[0] if similar_rules else None
    
    def check_duplicate(self, target_rule: Union[Dict, str], threshold: float = 0.9) -> Optional[Dict]:
        """
        Duplicate kural kontrolü
        
        Args:
            target_rule: Kontrol edilecek kural
            threshold: Duplicate eşiği (default: 0.9)
            
        Returns:
            Duplicate kural varsa döndür, yoksa None
        """
        duplicates = self.find_similar_rules(target_rule, similarity_threshold=threshold, max_results=1)
        return duplicates[0] if duplicates else None
    
    def bulk_insert_rules(self, rules: List[Dict]) -> List[str]:
        """
        Çoklu kural ekleme
        
        Args:
            rules: Sigma kuralları listesi
            
        Returns:
            Eklenen doküman ID'leri
        """
        documents = []
        for rule in rules:
            doc = {
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
            documents.append(doc)
        
        try:
            result = self.collection.insert_many(documents)
            self.logger.info(f"✅ {len(result.inserted_ids)} kural toplu eklendi")
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            self.logger.error(f"❌ Toplu ekleme hatası: {e}")
            raise
    
    def create_indexes(self):
        """Performans için indeksler oluştur"""
        try:
            # Text index for search
            self.collection.create_index([
                ('title', 'text'),
                ('sigma_rule.detection', 'text')
            ])
            
            # Regular indexes
            self.collection.create_index('level')
            self.collection.create_index('author')
            self.collection.create_index('created_at')
            
            self.logger.info("✅ Indeksler oluşturuldu")
        except Exception as e:
            self.logger.error(f"❌ İndeks oluşturma hatası: {e}")
    
    def search_by_content(self, search_term: str, max_results: int = 10) -> List[Dict]:
        """
        İçerik bazlı arama
        
        Args:
            search_term: Aranacak terim
            max_results: Maksimum sonuç sayısı
            
        Returns:
            Bulunan kurallar
        """
        try:
            results = list(self.collection.find(
                {'$text': {'$search': search_term}},
                {'score': {'$meta': 'textScore'}}
            ).sort([('score', {'$meta': 'textScore'})]).limit(max_results))
            
            self.logger.info(f"✅ '{search_term}' için {len(results)} sonuç bulundu")
            return results
        except Exception as e:
            self.logger.error(f"❌ Arama hatası: {e}")
            return []
    
    def close_connection(self):
        """MongoDB bağlantısını kapat"""
        self.client.close()
        self.logger.info("✅ MongoDB bağlantısı kapatıldı")

# Test ve örnek kullanım
def test_sigma_mongo_matcher():
    """MongoDB matcher'ın test edilmesi"""
    
    # MongoDB matcher'ı başlat
    matcher = SigmaMongoMatcher()
    
    # Bağlantıyı test et
    if not matcher.test_connection():
        print("❌ MongoDB bağlantısı kurulamadı!")
        return
    
    # Test kuralları ekle
    test_rules = [
        {
            'title': 'Suspicious PowerShell Execution',
            'author': 'Test Author',
            'level': 'high',
            'detection': {
                'selection': {
                    'EventID': 4688,
                    'Image|endswith': '\\powershell.exe',
                    'CommandLine|contains': ['-ExecutionPolicy', '-enc', 'IEX']
                },
                'condition': 'selection'
            }
        },
        {
            'title': 'Malicious CMD Commands',
            'author': 'Security Team',
            'level': 'medium',
            'detection': {
                'selection': {
                    'EventID': 4688,
                    'Image|endswith': '\\cmd.exe',
                    'CommandLine|contains': ['whoami', 'systeminfo']
                },
                'condition': 'selection'
            }
        },
        {
            'title': 'PowerShell Download Activity',
            'author': 'Threat Hunter',
            'level': 'high',
            'detection': {
                'selection': {
                    'EventID': 4688,
                    'Image|endswith': '\\powershell.exe',
                    'CommandLine|contains': ['-ExecutionPolicy', '-encoded', 'Invoke-WebRequest']
                },
                'condition': 'selection'
            }
        }
    ]
    
    # Kuralları MongoDB'ye ekle
    print("📥 Test kuralları ekleniyor...")
    matcher.bulk_insert_rules(test_rules)
    
    # İndeksler oluştur
    matcher.create_indexes()
    
    # Test kuralı ile benzer kuralları ara
    test_query_rule = {
        'detection': {
            'selection': {
                'EventID': 4688,
                'Image|endswith': '\\powershell.exe',
                'CommandLine|contains': ['-exec', '-enc', 'Invoke-Expression']
            },
            'condition': 'selection'
        }
    }
    
    print("\n🔍 Benzer kurallar aranıyor...")
    similar_rules = matcher.find_similar_rules(
        test_query_rule, 
        similarity_threshold=0.3,
        max_results=5
    )
    
    print(f"\n📊 {len(similar_rules)} benzer kural bulundu:")
    for i, rule in enumerate(similar_rules, 1):
        print(f"\n{i}. {rule['title']}")
        print(f"   👤 Yazar: {rule['author']}")
        print(f"   📊 Benzerlik: {rule['similarity_score']:.1%}")
        print(f"   🔤 String: {rule['string_similarity']:.1%}")
        print(f"   🏷️  Field: {rule['field_similarity']:.1%}")
        print(f"   ⚠️  Level: {rule['level']}")
    
    # En iyi eşleşmeyi bul
    print("\n🏆 EN İYİ EŞLEŞME:")
    best_match = matcher.get_best_match(test_query_rule)
    if best_match:
        print(f"   📋 {best_match['title']}")
        print(f"   📊 Skor: {best_match['similarity_score']:.1%}")
    
    # Duplicate kontrolü
    print("\n🔍 DUPLICATE KONTROLÜ:")
    duplicate = matcher.check_duplicate(test_rules[0], threshold=0.8)
    if duplicate:
        print(f"   ⚠️ Duplicate bulundu: {duplicate['title']}")
    else:
        print("   ✅ Duplicate yok")
    
    # Bağlantıyı kapat
    matcher.close_connection()

if __name__ == "__main__":
    test_sigma_mongo_matcher()
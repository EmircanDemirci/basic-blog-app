import yaml
import pymongo
import re
from difflib import SequenceMatcher
from collections import Counter

class SigmaRuleComparator:
    def __init__(self, mongo_connection_string):
        self.client = pymongo.MongoClient(mongo_connection_string)
        self.collection = self.client["sigmaDB"]["rules"]
    
    def extract_detection_components(self, detection_dict):
        """Detection bölümünden field'ları ve değerleri ayrı ayrı çıkar"""
        fields = set()
        values = []
        
        def recursive_extract(obj, parent_key=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'condition':  # condition'ı skip et
                        continue
                    
                    # Field ismini ekle
                    fields.add(key)
                    
                    if isinstance(value, (str, int, float)):
                        values.append(str(value))
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, (str, int, float)):
                                values.append(str(item))
                            elif isinstance(item, dict):
                                recursive_extract(item, key)
                    elif isinstance(value, dict):
                        recursive_extract(value, key)
            elif isinstance(obj, list):
                for item in obj:
                    recursive_extract(item, parent_key)
        
        recursive_extract(detection_dict)
        return list(fields), values
    
    def fuzzy_similarity(self, str1, str2):
        """Fuzzy string matching"""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def substring_similarity(self, str1, str2):
        """Substring benzerliği"""
        if not str1 or not str2:
            return 0.0
        
        str1, str2 = str1.lower(), str2.lower()
        if str1 == str2:
            return 1.0
        
        shorter, longer = (str1, str2) if len(str1) < len(str2) else (str2, str1)
        if shorter in longer:
            return len(shorter) / len(longer)
        return 0.0
    
    def combined_string_similarity(self, str1, str2):
        """Birleşik string benzerliği"""
        fuzzy = self.fuzzy_similarity(str1, str2)
        substring = self.substring_similarity(str1, str2)
        return max(fuzzy, substring)  # En iyisini al
    
    def calculate_field_similarity(self, fields1, fields2):
        """Field isimlerinin benzerliği (Jaccard)"""
        if not fields1 or not fields2:
            return 0.0
        
        set1, set2 = set(fields1), set(fields2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0
    
    def calculate_value_similarity(self, values1, values2):
        """Value'ların benzerliği (pairwise matching)"""
        if not values1 or not values2:
            return 0.0
        
        total_similarity = 0.0
        used_indices = set()
        
        # Her value1 için en iyi eşleşen value2'yi bul
        for val1 in values1:
            best_sim = 0.0
            best_idx = -1
            
            for i, val2 in enumerate(values2):
                if i in used_indices:
                    continue
                    
                sim = self.combined_string_similarity(str(val1), str(val2))
                if sim > best_sim:
                    best_sim = sim
                    best_idx = i
            
            if best_idx != -1:
                used_indices.add(best_idx)
                total_similarity += best_sim
        
        # Ortalama hesapla
        max_pairs = max(len(values1), len(values2))
        return total_similarity / max_pairs
    
    def compare_with_mongodb(self, yaml_file_path, top_n=10):
        """YAML dosyasını MongoDB'deki kurallarla karşılaştır"""
        
        # YAML dosyasını oku
        print("📄 YAML dosyası okunuyor...")
        with open(yaml_file_path, "r", encoding='utf-8') as f:
            yaml_rule = yaml.safe_load(f)
        
        yaml_detection = yaml_rule.get("detection", {})
        yaml_fields, yaml_values = self.extract_detection_components(yaml_detection)
        
        print(f"🔍 YAML'dan çıkarılan:")
        print(f"   Fields: {yaml_fields}")
        print(f"   Values: {yaml_values}")
        print("-" * 60)
        
        # MongoDB'den tüm kuralları al
        print("🔍 MongoDB'den kurallar getiriliyor...")
        documents = list(self.collection.find())
        print(f"📊 Toplam {len(documents)} kural bulundu")
        
        similarity_results = []
        
        for idx, doc in enumerate(documents, start=1):
            try:
                # MongoDB dokümanından detection bilgilerini çıkar
                mongo_detection = doc.get("detection", {})
                mongo_fields, mongo_values = self.extract_detection_components(mongo_detection)
                
                # Benzerlik hesapla
                field_sim = self.calculate_field_similarity(yaml_fields, mongo_fields)
                value_sim = self.calculate_value_similarity(yaml_values, mongo_values)
                
                # Ağırlıklı toplam (%80 value, %20 field)
                weighted_similarity = (value_sim * 0.8) + (field_sim * 0.2)
                
                similarity_results.append({
                    "index": idx,
                    "rule_id": str(doc.get("_id")),
                    "title": doc.get("title", "Untitled"),
                    "field_similarity": field_sim,
                    "value_similarity": value_sim,
                    "weighted_similarity": weighted_similarity,
                    "mongo_fields": mongo_fields,
                    "mongo_values": mongo_values
                })
                
            except Exception as e:
                print(f"❌ Kural {idx} işlenirken hata: {e}")
                continue
        
        # En yüksek benzerliği sırala
        top_matches = sorted(similarity_results, key=lambda x: x['weighted_similarity'], reverse=True)[:top_n]
        
        print(f"\n🏆 EN BENZERLİK GÖSTEREN {top_n} KURAL:")
        print("=" * 80)
        
        for i, match in enumerate(top_matches, 1):
            print(f"\n{i}. 📋 {match['title']}")
            print(f"   🆔 Rule ID: {match['rule_id']}")
            print(f"   📊 TOPLAM BENZERLİK: {match['weighted_similarity']:.1%}")
            print(f"   🔤 Value Benzerliği:  {match['value_similarity']:.1%}")
            print(f"   🏷️  Field Benzerliği:  {match['field_similarity']:.1%}")
            
            # Detayları göster
            print(f"   🔍 MongoDB Fields: {match['mongo_fields']}")
            print(f"   🔍 MongoDB Values: {match['mongo_values'][:5]}...")  # İlk 5'ini göster
            
            # En iyi value eşleşmelerini göster
            if match['value_similarity'] > 0.3:  # Anlamlı benzerlik varsa
                print("   🎯 En İyi Value Eşleşmeleri:")
                for yaml_val in yaml_values[:3]:  # İlk 3 YAML value
                    best_match = ""
                    best_score = 0.0
                    for mongo_val in match['mongo_values']:
                        score = self.combined_string_similarity(str(yaml_val), str(mongo_val))
                        if score > best_score:
                            best_score = score
                            best_match = mongo_val
                    
                    if best_score > 0.3:
                        print(f"      '{yaml_val}' ↔ '{best_match}' ({best_score:.1%})")
            
            print("-" * 60)
        
        return top_matches

# Kullanım
def main():
    # MongoDB bağlantı string'ini buraya girin
    mongo_connection = "mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/"
    
    # Comparator'ı başlat
    comparator = SigmaRuleComparator(mongo_connection)
    
    # YAML dosyasını karşılaştır
    try:
        results = comparator.compare_with_mongodb("deneme_kural.yml", top_n=10)
        
        # Özet istatistikler
        if results:
            print(f"\n📈 ÖZETİ:")
            print(f"   En yüksek benzerlik: {results[0]['weighted_similarity']:.1%}")
            print(f"   En düşük (top 10): {results[-1]['weighted_similarity']:.1%}")
            print(f"   Ortalama benzerlik: {sum(r['weighted_similarity'] for r in results) / len(results):.1%}")
            
    except FileNotFoundError:
        print("❌ 'deneme_kural.yml' dosyası bulunamadı!")
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    main()
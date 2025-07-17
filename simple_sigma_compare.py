import yaml
import pymongo
from difflib import SequenceMatcher

def get_all_strings_from_detection(detection):
    """Detection'dan tüm string değerleri çıkar"""
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
                if key != 'condition':  # condition'ı skip et
                    extract_strings(value)
    
    extract_strings(detection)
    return all_strings

def calculate_similarity(strings1, strings2):
    """İki string listesi arasındaki benzerliği hesapla"""
    if not strings1 or not strings2:
        return 0.0
    
    total_score = 0.0
    comparisons = 0
    
    # Her string1 için en iyi eşleşen string2'yi bul
    for s1 in strings1:
        best_score = 0.0
        for s2 in strings2:
            # Fuzzy matching + substring checking
            fuzzy_score = SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
            
            # Substring bonus
            if s1.lower() in s2.lower() or s2.lower() in s1.lower():
                substring_bonus = 0.2
            else:
                substring_bonus = 0.0
            
            combined_score = min(1.0, fuzzy_score + substring_bonus)
            
            if combined_score > best_score:
                best_score = combined_score
        
        total_score += best_score
        comparisons += 1
    
    return total_score / comparisons

def main():
    print("🔍 Basit Sigma Kural Karşılaştırıcısı")
    print("=" * 50)
    
    # YAML dosyasını oku
    try:
        with open("deneme_kural.yml", "r", encoding='utf-8') as f:
            yaml_rule = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ deneme_kural.yml dosyası bulunamadı!")
        return
    
    # YAML'dan stringleri çıkar
    yaml_detection = yaml_rule.get("detection", {})
    yaml_strings = get_all_strings_from_detection(yaml_detection)
    
    print(f"📄 YAML'dan çıkarılan stringler:")
    for i, s in enumerate(yaml_strings, 1):
        print(f"   {i}. {s}")
    print()
    
    # MongoDB bağlantısı
    client = pymongo.MongoClient("mongodb+srv://emircandemirci:m#n#m#n1135@cluster0.gntn5zk.mongodb.net/")
    collection = client["sigmaDB"]["rules"]
    
    print("🔍 MongoDB'den kurallar getiriliyor...")
    documents = list(collection.find())
    print(f"📊 Toplam {len(documents)} kural bulundu\n")
    
    results = []
    
    # Her MongoDB kuralı için benzerlik hesapla
    for idx, doc in enumerate(documents, 1):
        try:
            mongo_detection = doc.get("detection", {})
            mongo_strings = get_all_strings_from_detection(mongo_detection)
            
            # Benzerlik hesapla
            similarity = calculate_similarity(yaml_strings, mongo_strings)
            
            results.append({
                'index': idx,
                'rule_id': str(doc.get('_id')),
                'title': doc.get('title', 'Untitled'),
                'similarity': similarity,
                'mongo_strings': mongo_strings
            })
            
            # İlerleme göster
            if idx % 100 == 0:
                print(f"   İşlenen: {idx}/{len(documents)}")
                
        except Exception as e:
            print(f"❌ Kural {idx} işlenirken hata: {e}")
    
    # En iyi 10'u sırala
    top_results = sorted(results, key=lambda x: x['similarity'], reverse=True)[:10]
    
    print(f"\n🏆 EN BENZERLİK GÖSTEREN 10 KURAL:")
    print("=" * 60)
    
    for i, result in enumerate(top_results, 1):
        print(f"\n{i}. 📋 {result['title']}")
        print(f"   🆔 Rule ID: {result['rule_id']}")
        print(f"   📊 Benzerlik: {result['similarity']:.1%}")
        
        # En iyi eşleşmeleri göster
        if result['similarity'] > 0.3:
            print("   🎯 En İyi String Eşleşmeleri:")
            for yaml_str in yaml_strings[:3]:  # İlk 3'ü
                best_match = ""
                best_score = 0.0
                
                for mongo_str in result['mongo_strings']:
                    score = SequenceMatcher(None, yaml_str.lower(), mongo_str.lower()).ratio()
                    if score > best_score:
                        best_score = score
                        best_match = mongo_str
                
                if best_score > 0.3:
                    print(f"      '{yaml_str}' ↔ '{best_match}' ({best_score:.1%})")
        
        print(f"   📝 MongoDB'daki stringler: {result['mongo_strings'][:3]}...")
        print("-" * 40)
    
    # Özet
    if top_results:
        print(f"\n📈 ÖZET:")
        print(f"   En yüksek benzerlik: {top_results[0]['similarity']:.1%}")
        print(f"   Ortalama (top 10): {sum(r['similarity'] for r in top_results)/len(top_results):.1%}")

if __name__ == "__main__":
    main()
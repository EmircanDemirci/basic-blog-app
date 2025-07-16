# Sigma MongoDB Entegrasyonu Kullanım Rehberi

## 🎯 Özellikler

✅ **MongoDB'den benzer kural arama** (%80 string, %20 field ağırlığı)  
✅ **Otomatik duplicate tespiti** (90%+ benzerlik)  
✅ **Toplu kural ekleme** ve yönetimi  
✅ **Performans indeksleri** oluşturma  
✅ **Ağırlık ayarlama** (string/field oranları)  
✅ **En iyi eşleşme** bulma  

## 🚀 Hızlı Başlangıç

### 1. Kurulum
```bash
# Gereksinim yükle
pip install -r requirements.txt

# MongoDB'yi başlat (Docker ile)
docker run -d -p 27017:27017 --name sigma-mongo mongo:latest
```

### 2. Temel Kullanım
```python
from sigma_mongodb_matcher import SigmaMongoMatcher

# MongoDB matcher'ı başlat
matcher = SigmaMongoMatcher(
    mongodb_uri="mongodb://localhost:27017/",
    database_name="sigma_rules",
    collection_name="rules"
)

# Bağlantıyı test et
if matcher.test_connection():
    print("✅ MongoDB hazır!")
```

### 3. Kural Ekleme
```python
# Tek kural ekle
sigma_rule = {
    'title': 'Suspicious PowerShell Execution',
    'author': 'Security Team',
    'level': 'high',
    'detection': {
        'selection': {
            'EventID': 4688,
            'Image|endswith': '\\powershell.exe',
            'CommandLine|contains': ['-ExecutionPolicy', '-enc']
        },
        'condition': 'selection'
    }
}

rule_id = matcher.insert_sigma_rule(sigma_rule)
print(f"Kural eklendi: {rule_id}")

# Toplu kural ekleme
rules_list = [rule1, rule2, rule3, ...]
ids = matcher.bulk_insert_rules(rules_list)
```

### 4. Benzer Kural Arama
```python
# Yeni gelen kural
new_rule = {
    'detection': {
        'selection': {
            'EventID': 4688,
            'Image|endswith': '\\powershell.exe',
            'CommandLine|contains': ['-exec', '-encoded']
        }
    }
}

# Benzer kuralları bul
similar_rules = matcher.find_similar_rules(
    target_rule=new_rule,
    similarity_threshold=0.5,  # %50+ benzerlik
    max_results=10,
    string_weight=0.8,         # %80 string ağırlığı
    field_weight=0.2           # %20 field ağırlığı
)

# Sonuçları işle
for rule in similar_rules:
    print(f"📋 {rule['title']}")
    print(f"📊 Benzerlik: {rule['similarity_score']:.1%}")
    print(f"🔍 Rule ID: {rule['rule_id']}")
```

## 📊 Demo Sonuçları

Demo'dan çıkan gerçek sonuçlar:

### 🏆 En İyi Eşleşme: 86.2%
```
📋 Suspicious PowerShell Execution
🔤 String Benzerliği: 82.7%
🏷️ Field Benzerliği: 100.0%
🔤 Ortak stringler: {'-enc', '-ExecutionPolicy', '4688', '\\powershell.exe'}
🏷️ Ortak field'lar: {'EventID', 'CommandLine|contains', 'Image|endswith'}
```

### 📈 Ağırlık Karşılaştırması:
- **String Odaklı** (%90-%10): 84.4%
- **Standart** (%80-%20): 86.2%
- **Field Odaklı** (%30-%70): 94.8%

## 🔧 Gelişmiş Özellikler

### 1. Duplicate Kontrolü
```python
# %90+ benzerlik varsa duplicate say
duplicate = matcher.check_duplicate(new_rule, threshold=0.9)

if duplicate:
    print(f"🚨 DUPLICATE: {duplicate['title']}")
    print("💡 Bu kural zaten mevcut!")
else:
    print("✅ Benzersiz kural, eklenebilir")
```

### 2. En İyi Eşleşme
```python
# Tek en iyi sonuç
best_match = matcher.get_best_match(new_rule)

if best_match:
    print(f"🏆 En benzer: {best_match['title']}")
    print(f"📊 Skor: {best_match['similarity_score']:.1%}")
```

### 3. Özel Ağırlık Senaryoları
```python
# Senaryo 1: İçerik önemli (malware analizi)
content_focused = matcher.find_similar_rules(
    new_rule,
    string_weight=0.9,
    field_weight=0.1
)

# Senaryo 2: Yapı önemli (log source mapping)
structure_focused = matcher.find_similar_rules(
    new_rule,
    string_weight=0.3,
    field_weight=0.7
)
```

### 4. Performans İyileştirme
```python
# İndeksler oluştur (bir kez çalıştır)
matcher.create_indexes()

# Text-based arama (hızlı pre-filtering)
quick_results = matcher.search_by_content("powershell")
```

## 💡 Gerçek Dünya Kullanım Örnekleri

### 1. SigmaHQ Rule Validation
```python
# Local rule'ınızı SigmaHQ database'i ile karşılaştırın
def check_against_sigmahq(local_rule):
    similar = matcher.find_similar_rules(
        local_rule,
        similarity_threshold=0.7,
        max_results=5
    )
    
    if similar:
        print("⚠️ Benzer kurallar mevcut:")
        for rule in similar:
            print(f"  - {rule['title']} ({rule['similarity_score']:.1%})")
    else:
        print("✅ Benzersiz kural!")
```

### 2. Rule Deduplication Pipeline
```python
def deduplicate_rules(new_rules_batch):
    duplicates = []
    unique_rules = []
    
    for rule in new_rules_batch:
        duplicate = matcher.check_duplicate(rule, threshold=0.85)
        
        if duplicate:
            duplicates.append((rule, duplicate))
        else:
            unique_rules.append(rule)
            matcher.insert_sigma_rule(rule)
    
    return unique_rules, duplicates
```

### 3. Rule Evolution Tracking
```python
def track_rule_evolution(old_rule, new_rule):
    sim = SigmaSimilarity(old_rule, new_rule)
    result = sim.compute_weighted_similarity()
    
    evolution_score = result['weighted_score']
    
    if evolution_score > 0.9:
        return "Minor update"
    elif evolution_score > 0.7:
        return "Moderate changes"
    elif evolution_score > 0.5:
        return "Significant changes"
    else:
        return "Major rewrite"
```

## 📋 MongoDB Şema

Kurallar şu formatta saklanır:

```json
{
  "_id": "ObjectId(...)",
  "sigma_rule": { /* Original Sigma rule */ },
  "title": "Rule Title",
  "author": "Author Name",
  "date": "2024-01-15",
  "level": "high",
  "logsource": { "product": "windows", "service": "security" },
  "detection": { /* Detection logic */ },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## ⚡ Performans Notları

### Büyük Veri Setleri İçin:
1. **İndeks kullanın**: `create_indexes()` çağırın
2. **Filtering**: İlk önce text search ile filtreleyin
3. **Batch processing**: Toplu işlemler için `bulk_insert_rules()`
4. **Connection pooling**: Production'da connection pool kullanın

### Bellek Optimizasyonu:
- Büyük result setleri için `max_results` sınırlayın
- `similarity_threshold` yükselterek irrelevant sonuçları filtreleyin

## 🔍 Troubleshooting

### MongoDB Bağlantı Hatası:
```python
if not matcher.test_connection():
    print("❌ MongoDB bağlantısı başarısız")
    # Alternatif: In-memory matcher kullan
    from sigma_demo_without_mongo import SigmaMemoryMatcher
    matcher = SigmaMemoryMatcher()
```

### Düşük Benzerlik Skorları:
- `string_weight` artırın (0.9, 0.1)
- `similarity_threshold` düşürün (0.3)
- Field normalizasyonu yapın (Image vs ProcessName)

### Performans Sorunları:
- İndeksleri kontrol edin
- Query optimization yapın
- Caching ekleyin

## 🎯 Sonuç

Bu sistem Sigma kurallarını etkili şekilde organize eder:
- **%80-86%** benzerlik: Muhtemelen aynı tehdit
- **%60-80%** benzerlik: İncelenmesi gereken varyant
- **%90%+** benzerlik: Duplicate olarak işaretle

Gerçek dünyada SigmaHQ, MITRE ATT&CK mapping ve SOC rule management için ideal!
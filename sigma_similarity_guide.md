# Sigma Kuralları Benzerlik Algoritması

## 📋 Özet

Sigma kuralları arasındaki benzerliği hesaplayan gelişmiş algoritma:
- **%80 String benzerliği**: Detection içeriklerinin anlamsal benzerliği
- **%20 Field benzerliği**: Kullanılan field yapılarının benzerliği
- **Ağırlıklı skor**: İki bileşenin kombinasyonu

## 🚀 Temel Kullanım

```python
from sigma_similarity import SigmaSimilarity

# İki Sigma kuralını karşılaştır
sim = SigmaSimilarity(sigma_rule1, sigma_rule2)

# Basit skor al
score = sim.get_sigma_similarity()
print(f"Benzerlik: {score:.1%}")

# Detaylı analiz
result = sim.compute_weighted_similarity()
print(f"String: {result['string_similarity']:.1%}")
print(f"Field: {result['field_similarity']:.1%}")
print(f"Toplam: {result['weighted_score']:.1%}")
```

## 📊 Test Sonuçları Analizi

### ✅ Başarılı Örnekler:

**1. Benzer PowerShell Kuralları** (83.8% benzerlik):
```
String: 79.7% (powershell, ExecutionPolicy, enc vs encoded)
Field: 100.0% (aynı field yapısı)
→ Muhtemelen aynı tehdidi tespit eden kurallar
```

**2. Farklı Field İsimleri** (84.0% benzerlik):
```
String: 100.0% (aynı komutlar: cmd.exe, whoami)
Field: 20.0% (ProcessName vs Image farklı)
→ Aynı içerik, farklı log source'u
```

**3. YAML Format Desteği** (80.0% benzerlik):
```
String: 75.0% (persistence vs persistence mechanism)
Field: 100.0% (aynı yapı)
→ YAML string'lerini otomatik parse ediyor
```

## 🎛️ Özel Ağırlık Senaryoları

### String Odaklı (%90 string, %10 field):
- **Ne zaman**: İçerik benzerliği field isimlerinden önemli
- **Örnek**: Farklı log source'lardan aynı komutlar

### Field Odaklı (%30 string, %70 field):
- **Ne zaman**: Yapısal benzerlik önemli
- **Örnek**: Aynı detection pattern'i, farklı payload'lar

### Eşit Ağırlık (%50, %50):
- **Ne zaman**: Hem içerik hem yapı eşit önemde
- **Örnek**: Genel benzerlik taraması

## 🔧 Algoritma Özellikleri

### String Benzerliği:
- **Tokenizasyon**: Sigma-specific (özel karakterleri korur: `*`, `?`, `|`, `\`)
- **TF-based Cosine**: IDF kullanmaz (2 doküman problemi çözülü)
- **Case-insensitive**: Büyük/küçük harf duyarsız

### Field Benzerliği:
- **Jaccard Similarity**: Field isimlerinin kesişimi/birleşimi
- **Modifier-aware**: `contains`, `endswith` modifierları ayrı field olarak değerlendirilir
- **Condition-safe**: `condition` field'ı benzerlik hesaplamasına dahil edilmez

## 📈 Eşleşme Kriterleri

| Skor Aralığı | Değerlendirme | Açıklama |
|--------------|---------------|----------|
| **80%+** | ✅ Çok Yüksek | Muhtemelen aynı tehdit/teknik |
| **60-80%** | ⚠️ Orta | Benzer ama farklı varyant |
| **40-60%** | 📝 Düşük | İlgili ama farklı kural |
| **40%-** | ❌ Farklı | Benzerlik yok |

## 💡 Kullanım Senaryoları

### 1. SigmaHQ Rule Matching:
```python
# Local rule'ınızı SigmaHQ repo'suyla karşılaştırın
local_rule = {...}
for sigmahq_rule in sigmahq_database:
    similarity = SigmaSimilarity(local_rule, sigmahq_rule).get_sigma_similarity()
    if similarity > 0.8:
        print(f"Duplicate found: {sigmahq_rule['title']}")
```

### 2. Rule Deduplication:
```python
# Aynı rule'ların tespiti
rules = [rule1, rule2, rule3, ...]
for i, rule_a in enumerate(rules):
    for rule_b in rules[i+1:]:
        if SigmaSimilarity(rule_a, rule_b).get_sigma_similarity() > 0.9:
            print("Duplicate rules detected!")
```

### 3. Rule Evolution Tracking:
```python
# Rule'ın zaman içindeki değişimini takip et
old_version = {...}
new_version = {...}
sim = SigmaSimilarity(old_version, new_version)
print(f"Rule evolution: {sim.get_sigma_similarity():.1%}")
```

## 🔍 Gerçek Dünya Testi

Test sonuçlarından görülen başarılar:
- **PowerShell kuralları**: 83.8% (çok başarılı)
- **Field varyasyonları**: 84.0% (mükemmel)
- **Farklı kurallar**: 24.7% (doğru düşük skor)

## 📋 Avantajlar

1. **Sigma-Specific**: Sigma kurallarının yapısına optimize
2. **Weighted Scoring**: İçerik ve yapı ayrı değerlendirilir
3. **Format Flexible**: Dict veya YAML string kabul eder
4. **Edge Case Handling**: Boş detection'lar, eksik field'lar güvenli
5. **Performance**: Hızlı algoritma, büyük rule setleri için uygun

## 🎯 Sonuç

Bu algoritma **Sigma kurallarının semantik benzerliğini** etkili şekilde hesaplıyor:
- String içeriği %80 etkiyle dominant rol
- Field yapısı %20 etkiyle destekleyici rol
- Sonuç: Gerçek dünya kullanımında güvenilir eşleşme skorları
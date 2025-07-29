# 🛍️ Product API - Kullanım Kılavuzu

## 📋 İçindekiler
- [Kurulum](#kurulum)
- [API Endpoints](#api-endpoints)
- [Postman ile Test Etme](#postman-ile-test-etme)
- [Token Alma](#token-alma)
- [Örnek İstekler](#örnek-istekler)

## 🚀 Kurulum

```bash
npm install
npm start
```

Server: `http://localhost:3000`

## 📡 API Endpoints

| Method | Endpoint | Auth | Açıklama |
|--------|----------|------|----------|
| GET | `/api/products` | ❌ | Tüm ürünleri listele |
| GET | `/api/products/:id` | ❌ | Tek ürün getir |
| POST | `/api/products` | ✅ | Yeni ürün oluştur |
| PUT | `/api/products/:id` | ✅ | Ürün güncelle |
| DELETE | `/api/products/:id` | ✅ | Ürün sil |
| GET | `/api/products/user/my-products` | ✅ | Kendi ürünlerimi getir |

## 🔧 Postman ile Test Etme

### 1️⃣ Postman'ı İndirin ve Açın
- [Postman'ı indirin](https://www.postman.com/downloads/)
- Postman'ı açın ve yeni bir Collection oluşturun

### 2️⃣ Base URL Ayarlayın
- Collection'a sağ tıklayın → "Edit"
- Variables sekmesine gidin
- `baseUrl` = `http://localhost:3000`

---

## 🔐 Token Alma (Önce Bu İşlemi Yapın!)

### ⚡ Test Token Al (Hızlı Yol)
```
Method: POST
URL: {{baseUrl}}/api/auth/get-test-token
Headers:
  Content-Type: application/json
Body: (Boş bırakın)
```

### 🔑 Normal Login
```
Method: POST
URL: {{baseUrl}}/api/auth/login
Headers:
  Content-Type: application/json

Body (raw - JSON):
{
  "email": "test@example.com",
  "password": "testpassword"
}
```

**Response'dan token'ı kopyalayın!**

---

## 📝 POSTMAN İSTEK ÖRNEKLERİ

### 🔍 1. TÜM ÜRÜNLERİ GETIR
```
Method: GET
URL: {{baseUrl}}/api/products
Headers: (Boş bırakın)
Body: (Boş bırakın)
```

### 🔍 2. TEK ÜRÜN GETIR
```
Method: GET
URL: {{baseUrl}}/api/products/ÜRÜN_ID_BURAYA
Headers: (Boş bırakın)
Body: (Boş bırakın)
```

### ➕ 3. YENİ ÜRÜN OLUŞTUR (TOKEN GEREKLİ!)
```
Method: POST
URL: {{baseUrl}}/api/products

Headers:
  Content-Type: application/json
  Authorization: Bearer YOUR_JWT_TOKEN_BURAYA

Body (raw - JSON):
{
  "name": "iPhone 15 Pro",
  "image": "https://example.com/iphone15.jpg",
  "description": "Yeni nesil iPhone, harika kamera",
  "price": 55000,
  "stock": 25
}
```

### ✏️ 4. ÜRÜN GÜNCELLE (TOKEN GEREKLİ!)
```
Method: PUT
URL: {{baseUrl}}/api/products/ÜRÜN_ID_BURAYA

Headers:
  Content-Type: application/json
  Authorization: Bearer YOUR_JWT_TOKEN_BURAYA

Body (raw - JSON):
{
  "name": "iPhone 15 Pro - Güncellenmiş",
  "price": 52000,
  "stock": 30
}
```

### ❌ 5. ÜRÜN SİL (TOKEN GEREKLİ!)
```
Method: DELETE
URL: {{baseUrl}}/api/products/ÜRÜN_ID_BURAYA

Headers:
  Authorization: Bearer YOUR_JWT_TOKEN_BURAYA

Body: (Boş bırakın)
```

### 👤 6. KENDİ ÜRÜNLERİMİ GETIR (TOKEN GEREKLİ!)
```
Method: GET
URL: {{baseUrl}}/api/products/user/my-products

Headers:
  Authorization: Bearer YOUR_JWT_TOKEN_BURAYA

Body: (Boş bırakın)
```

---

## 🎯 POSTMAN ADIM ADIM KULLANIMI

### Adım 1: Yeni Request Oluştur
1. Postman'da **"New"** butonuna tıklayın
2. **"HTTP Request"** seçin
3. Request'e isim verin (örn: "Create Product")

### Adım 2: Method ve URL Ayarla
1. Sol üstteki dropdown'dan **POST** seçin
2. URL kısmına: `http://localhost:3000/api/products` yazın

### Adım 3: Headers Ayarla
1. **Headers** sekmesine tıklayın
2. **Key**: `Content-Type` → **Value**: `application/json`
3. **Key**: `Authorization` → **Value**: `Bearer YOUR_TOKEN_HERE`

### Adım 4: Body Ayarla
1. **Body** sekmesine tıklayın
2. **raw** seçin
3. Sağ taraftan **JSON** seçin
4. JSON verinizi yazın:

```json
{
  "name": "Test Ürünü",
  "image": "https://example.com/test.jpg",
  "description": "Bu bir test ürünüdür",
  "price": 100,
  "stock": 5
}
```

### Adım 5: İsteği Gönder
1. **Send** butonuna tıklayın
2. Alt kısımda response'ı göreceksiniz

---

## ⚠️ Önemli Notlar

### Token Nasıl Alınır?
1. Önce login API'nize istek atın
2. Response'dan `token` değerini kopyalayın
3. `Bearer TOKEN_DEĞERÄ` formatında Authorization header'ına ekleyin

### Hata Durumları
- **401**: Token eksik
- **403**: Token geçersiz veya yetki yok
- **400**: Geçersiz veri formatı
- **404**: Ürün bulunamadı
- **500**: Sunucu hatası

### Gerekli Alanlar (POST/PUT)
- `name`: String (zorunlu)
- `image`: String (zorunlu) 
- `description`: String (zorunlu)
- `price`: Number (zorunlu, ≥0)
- `stock`: Number (zorunlu, ≥0)

---

## 🔗 Postman Collection İmport

Aşağıdaki JSON'ı kopyalayıp Postman'da **Import** → **Raw Text** ile içe aktarabilirsiniz:

```json
{
  "info": {
    "name": "Product API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:3000"
    }
  ],
  "item": [
    {
      "name": "Get All Products",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/api/products"
      }
    },
    {
      "name": "Create Product",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "Authorization",
            "value": "Bearer YOUR_TOKEN_HERE"
          }
        ],
        "url": "{{baseUrl}}/api/products",
        "body": {
          "mode": "raw",
          "raw": "{\n  \"name\": \"Test Product\",\n  \"image\": \"https://example.com/image.jpg\",\n  \"description\": \"Test description\",\n  \"price\": 100,\n  \"stock\": 10\n}"
        }
      }
    }
  ]
}
```

---

## 🚨 Troubleshooting

### Token ile ilgili "createdBy gereklidir" hatası:
1. **Önce token alın**: `/api/test/get-test-token` endpoint'inden
2. **Authorization header'ını doğru ekleyin**: `Bearer YOUR_TOKEN`
3. **Token'ın expire olmadığından emin olun**

### MongoDB Bağlantı Sorunları:
- MongoDB Atlas'ta IP whitelist kontrolü yapın
- Doğru database credentials kullandığınızdan emin olun
- MongoDB bağlantı hatası olursa server yine de çalışır (test için)

### Postman Kullanımı:
1. İlk olarak test token alın
2. Token'ı Authorization header'ına ekleyin
3. Body'yi raw JSON olarak ayarlayın
4. Gerekli tüm alanları doldurun

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. Server'ın çalıştığından emin olun (`npm start`)
2. Token'ınızın geçerli olduğunu kontrol edin
3. JSON formatının doğru olduğunu kontrol edin
4. Console'da hata mesajlarını kontrol edin

**Başarılı testler! 🎉**

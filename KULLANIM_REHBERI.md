# 🔐 Güvenli User Modeli Kullanım Rehberi

Bu rehber, oluşturulan güvenli user modelinin nasıl kullanılacağını açıklar.

## 📦 Kurulum

Gerekli bağımlılıkları yükleyin:

```bash
npm install
```

## 🚀 Hızlı Başlangıç

### 1. Server'ı Başlatın

```bash
npm start
```

### 2. API Endpoint'leri

#### 👤 Kullanıcı Kayıt

```http
POST /api/users/register

{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123",
    "tel": "5551234567",
    "country": "Türkiye"
}
```

#### 🔐 Kullanıcı Giriş

```http
POST /api/users/login

{
    "email": "test@example.com",
    "password": "Test123"
}
```

#### ✅ Email Doğrulama

```http
GET /api/users/verify-email/{token}
```

#### 📋 Profil Görüntüleme

```http
GET /api/users/profile
```
*Authentication gereklidir*

#### ✏️ Profil Güncelleme

```http
PUT /api/users/profile

{
    "username": "yeniusername",
    "tel": "5559876543",
    "country": "Türkiye",
    "profilePicture": "https://example.com/photo.jpg"
}
```
*Authentication gereklidir*

#### 🔄 Şifre Değiştirme

```http
PUT /api/users/change-password

{
    "currentPassword": "Test123",
    "newPassword": "NewPassword123"
}
```
*Authentication gereklidir*

#### 🚪 Çıkış Yapma

```http
POST /api/users/logout
```
*Authentication gereklidir*

## 🛡️ Admin İşlemleri

#### 👥 Tüm Kullanıcıları Listele

```http
GET /api/users/admin/users?page=1&limit=10&role=user&accountStatus=active
```
*Admin yetkisi gereklidir*

#### 🔧 Kullanıcı Rolünü Değiştir

```http
PUT /api/users/admin/users/{userId}/role

{
    "role": "admin"
}
```
*Admin yetkisi gereklidir*

## 🎭 Rol Sistemi

### Mevcut Roller:
- **`user`**: Normal kullanıcı (varsayılan)
- **`moderator`**: Moderatör
- **`admin`**: Administrator

### Hesap Durumları:
- **`pending_verification`**: Email doğrulaması bekliyor (varsayılan)
- **`active`**: Aktif hesap
- **`inactive`**: Pasif hesap
- **`suspended`**: Askıya alınmış hesap

## 🔒 Güvenlik Özellikleri

### 1. **Şifre Hashleme**
- bcrypt kullanarak salt rounds: 12
- Şifreler veritabanında hashlenmiş olarak saklanır

### 2. **Şifre Güçlülük Kontrolü**
- Minimum 8 karakter
- En az 1 büyük harf, 1 küçük harf, 1 sayı gerekli

### 3. **Hesap Kilitleme**
- 5 başarısız giriş denemesinden sonra hesap 2 saat kilitlenir
- Kilitli hesaplar giriş yapamaz

### 4. **Email Doğrulama**
- Yeni hesaplar email doğrulaması gerektirir
- Random token ile doğrulama sistemi

### 5. **Validasyon**
- Email format kontrolü
- Türkiye telefon numarası formatı (5XXXXXXXXX)
- Username benzersizlik kontrolü

## 📱 Model Kullanımı

### Kullanıcı Oluşturma

```javascript
const User = require('./models/user');

const newUser = new User({
    username: 'testuser',
    email: 'test@example.com',
    password: 'Test123', // Otomatik hashlenecek
    tel: '5551234567',
    country: 'Türkiye'
});

await newUser.save();
```

### Şifre Kontrolü

```javascript
const user = await User.findOne({ email: 'test@example.com' });
const isPasswordCorrect = await user.comparePassword('Test123');
```

### Rol Kontrolü

```javascript
const user = await User.findById(userId);

if (user.isAdmin()) {
    // Admin işlemleri
}

if (user.hasRole('moderator')) {
    // Moderator işlemleri
}
```

### Login Denemesi Başarısız

```javascript
const user = await User.findOne({ email });

if (!await user.comparePassword(password)) {
    await user.incLoginAttempts(); // Deneme sayısını artır
}
```

### Başarılı Login

```javascript
await user.resetLoginAttempts(); // Deneme sayısını sıfırla
```

## 🛠️ Middleware Kullanımı

### Authentication Kontrolü

```javascript
const { authenticateUser } = require('./middleware/auth');

router.get('/protected', authenticateUser, (req, res) => {
    // req.user ile kullanıcı bilgilerine erişim
    res.json({ user: req.user });
});
```

### Rol Kontrolü

```javascript
const { requireAdmin, requireModerator } = require('./middleware/auth');

// Sadece admin
router.get('/admin-only', authenticateUser, requireAdmin, handler);

// Moderator veya admin
router.get('/mod-or-admin', authenticateUser, requireModerator, handler);
```

## 🔧 Özelleştirme

### Session Secret'ını Değiştirin

`app.js` dosyasında:

```javascript
app.use(session({
    secret: 'your-very-secure-secret-key-here',
    // ...
}));
```

### Production için Session Ayarları

```javascript
app.use(session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: true, // HTTPS için
        httpOnly: true,
        maxAge: 24 * 60 * 60 * 1000
    }
}));
```

## 📧 Email Sistemi Entegrasyonu

Email doğrulama ve şifre sıfırlama için bir email servis sağlayıcısı (örn. SendGrid, Nodemailer) entegre etmeniz gerekir.

### Örnek Implementation:

```javascript
const nodemailer = require('nodemailer');

const sendVerificationEmail = async (email, token) => {
    const verificationUrl = `http://yourdomain.com/api/users/verify-email/${token}`;
    
    // Email gönderme kodu...
};
```

## 🚨 Güvenlik Notları

1. **Production'da**:
   - Session secret'ını environment variable olarak kullanın
   - HTTPS kullanın
   - CORS ayarlarını yapın
   - Rate limiting ekleyin

2. **Veritabanı**:
   - MongoDB Atlas kullanıyorsanız IP whitelist ayarlayın
   - Güçlü veritabanı şifresi kullanın

3. **Şifreler**:
   - Asla şifreleri loglamayın
   - Password reset token'larını kısa süreliğine ayarlayın

## 🎯 Sonraki Adımlar

1. JWT token sistemi ekleyebilirsiniz
2. OAuth (Google, Facebook) entegrasyonu
3. Two-factor authentication (2FA)
4. Email template sistemi
5. User activity logging

Bu kullanım rehberi, güvenli user modelinizi etkili bir şekilde kullanmanıza yardımcı olacaktır. 🚀
const express = require('express');
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const router = express.Router();

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-here-change-in-production';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '7d';

// Token oluşturma fonksiyonu
const generateToken = (userId) => {
    return jwt.sign({ userId }, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });
};

// ✅ KULLANICI KAYIT
router.post('/register', async (req, res) => {
    try {
        const { username, email, password } = req.body;

        // Validation
        if (!username || !email || !password) {
            return res.status(400).json({ 
                error: 'Kullanıcı adı, email ve şifre gereklidir' 
            });
        }

        if (password.length < 6) {
            return res.status(400).json({ 
                error: 'Şifre en az 6 karakter olmalıdır' 
            });
        }

        // Kullanıcı zaten var mı kontrol et
        const existingUser = await User.findOne({ 
            $or: [{ email }, { username }] 
        });

        if (existingUser) {
            return res.status(409).json({ 
                error: 'Bu email veya kullanıcı adı zaten kullanılıyor' 
            });
        }

        // Yeni kullanıcı oluştur
        const newUser = new User({
            username,
            email,
            password
        });

        await newUser.save();

        // Token oluştur
        const token = generateToken(newUser._id);

        console.log("🟢 Yeni kullanıcı kaydedildi:", newUser.username);

        res.status(201).json({
            message: 'Kullanıcı başarıyla kaydedildi',
            token,
            user: {
                id: newUser._id,
                username: newUser.username,
                email: newUser.email,
                isAdmin: newUser.isAdmin
            }
        });

    } catch (error) {
        console.error('❌ Kayıt hatası:', error);
        
        if (error.name === 'ValidationError') {
            const errors = Object.values(error.errors).map(e => e.message);
            return res.status(400).json({ error: errors.join(', ') });
        }
        
        res.status(500).json({ error: 'Sunucu hatası' });
    }
});

// ✅ KULLANICI GİRİŞ
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        // Validation
        if (!email || !password) {
            return res.status(400).json({ 
                error: 'Email ve şifre gereklidir' 
            });
        }

        // Kullanıcıyı bul
        const user = await User.findOne({ email });
        
        if (!user) {
            return res.status(401).json({ 
                error: 'Geçersiz email veya şifre' 
            });
        }

        // Şifreyi kontrol et
        const isPasswordValid = await user.comparePassword(password);
        
        if (!isPasswordValid) {
            return res.status(401).json({ 
                error: 'Geçersiz email veya şifre' 
            });
        }

        // Token oluştur
        const token = generateToken(user._id);

        console.log("🟢 Kullanıcı giriş yaptı:", user.username);

        res.json({
            message: 'Giriş başarılı',
            token,
            user: {
                id: user._id,
                username: user.username,
                email: user.email,
                isAdmin: user.isAdmin
            }
        });

    } catch (error) {
        console.error('❌ Giriş hatası:', error);
        res.status(500).json({ error: 'Sunucu hatası' });
    }
});

// ✅ KULLANICI PROFİLİ (token gerekli)
router.get('/profile', require('../middleware/verifyToken')(), async (req, res) => {
    try {
        res.json({
            message: 'Profil bilgileri başarıyla getirildi',
            user: {
                id: req.user._id,
                username: req.user.username,
                email: req.user.email,
                isAdmin: req.user.isAdmin,
                createdAt: req.user.createdAt
            }
        });
    } catch (error) {
        console.error('❌ Profil getirme hatası:', error);
        res.status(500).json({ error: 'Sunucu hatası' });
    }
});

module.exports = router;
const express = require('express');
const jwt = require('jsonwebtoken');
const router = express.Router();
const User = require('../models/User');
require('dotenv').config();

// 🔐 TEST İÇİN DUMMY TOKEN OLUŞTUR
router.post('/get-test-token', async (req, res) => {
  try {
    // Test kullanıcısı oluştur veya bul
    let testUser = await User.findOne({ email: 'test@example.com' });
    
    if (!testUser) {
      testUser = new User({
        username: 'testuser',
        email: 'test@example.com',
        password: 'testpassword',
        isAdmin: false
      });
      await testUser.save();
      console.log('🟢 Test kullanıcısı oluşturuldu');
    }

    // JWT token oluştur
    const token = jwt.sign(
      { 
        _id: testUser._id,
        email: testUser.email,
        username: testUser.username,
        isAdmin: testUser.isAdmin
      },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.json({
      message: 'Test token oluşturuldu',
      token: token,
      user: {
        id: testUser._id,
        username: testUser.username,
        email: testUser.email,
        isAdmin: testUser.isAdmin
      }
    });

  } catch (err) {
    console.error('❌ Token oluşturma hatası:', err);
    res.status(500).json({ error: 'Token oluşturulamadı' });
  }
});

// 🔐 BASIT LOGIN (TEST İÇİN)
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    // Kullanıcıyı bul
    const user = await User.findOne({ email });
    
    if (!user || user.password !== password) {
      return res.status(401).json({ message: 'Geçersiz email veya şifre' });
    }

    // JWT token oluştur
    const token = jwt.sign(
      { 
        _id: user._id,
        email: user.email,
        username: user.username,
        isAdmin: user.isAdmin
      },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.json({
      message: 'Giriş başarılı',
      token: token,
      user: {
        id: user._id,
        username: user.username,
        email: user.email,
        isAdmin: user.isAdmin
      }
    });

  } catch (err) {
    console.error('❌ Login hatası:', err);
    res.status(500).json({ error: 'Sunucu hatası' });
  }
});

module.exports = router;
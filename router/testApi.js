const express = require('express');
const jwt = require('jsonwebtoken');
const router = express.Router();
const verifyToken = require('../middleware/verifyToken');
require('dotenv').config();

// 🔐 TEST TOKEN OLUŞTUR (MongoDB olmadan)
router.post('/get-test-token', (req, res) => {
  try {
    // Mock user data
    const testUser = {
      _id: '507f1f77bcf86cd799439011', // Mock ObjectId
      username: 'testuser',
      email: 'test@example.com',
      isAdmin: false
    };

    // JWT token oluştur
    const token = jwt.sign(testUser, process.env.JWT_SECRET, { expiresIn: '7d' });

    res.json({
      message: 'Test token oluşturuldu',
      token: token,
      user: testUser
    });

  } catch (err) {
    console.error('❌ Token oluşturma hatası:', err);
    res.status(500).json({ error: 'Token oluşturulamadı' });
  }
});

// 🧪 TOKEN TEST ET
router.post('/verify-token', verifyToken(), (req, res) => {
  console.log("🔍 Token test - req.user:", req.user);
  
  res.json({
    message: 'Token geçerli!',
    user: req.user
  });
});

// 🧪 MOCK ÜRÜN OLUŞTUR TEST
router.post('/create-product', verifyToken(), (req, res) => {
  try {
    console.log("🔍 POST isteği geldi");
    console.log("🔍 req.user:", req.user);
    console.log("🔍 req.body:", req.body);
    
    const { name, image, description, price, stock } = req.body;

    // req.user kontrolü
    if (!req.user || !req.user._id) {
      console.error("❌ req.user veya req.user._id bulunamadı!");
      return res.status(401).json({ 
        error: 'Token doğrulaması başarısız - kullanıcı bilgisi eksik' 
      });
    }

    // Validation
    if (!name || !image || !description || price === undefined || stock === undefined) {
      return res.status(400).json({ 
        error: 'Tüm alanlar gereklidir: name, image, description, price, stock' 
      });
    }

    console.log("✅ User ID:", req.user._id);

    // Mock product (MongoDB olmadan)
    const mockProduct = {
      _id: '507f1f77bcf86cd799439012',
      name,
      image,
      description,
      price: Number(price),
      stock: Number(stock),
      createdBy: req.user._id,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    console.log("🟢 Mock ürün oluşturuldu:", mockProduct.name);
    res.status(201).json({ 
      message: 'Mock ürün başarıyla oluşturuldu', 
      product: mockProduct 
    });
  } catch (err) {
    console.error("❌ Mock ürün oluşturma hatası:", err);
    res.status(500).json({ error: 'Sunucu hatası' });
  }
});

module.exports = router;
const express = require('express');
const router = express.Router();
const Product = require('../models/Product');
const verifyToken = require('../middleware/verifyToken');

// ✅ TÜM ÜRÜNLERİ GETIR (token olmadan)
router.get('/', async (req, res) => {
  try {
    const products = await Product.find().populate('createdBy', 'username email');
    res.json({ 
      message: 'Ürünler başarıyla getirildi', 
      products,
      count: products.length 
    });
  } catch (err) {
    console.error("❌ Ürünler getirme hatası:", err);
    res.status(500).json({ error: 'Sunucu hatası' });
  }
});

// ✅ TEK ÜRÜN GETIR (token olmadan)
router.get('/:id', async (req, res) => {
  try {
    const product = await Product.findById(req.params.id).populate('createdBy', 'username email');
    
    if (!product) {
      return res.status(404).json({ error: 'Ürün bulunamadı' });
    }

    res.json({ message: 'Ürün başarıyla getirildi', product });
  } catch (err) {
    console.error("❌ Ürün getirme hatası:", err);
    if (err.name === 'CastError') {
      return res.status(400).json({ error: 'Geçersiz ürün ID formatı' });
    }
    res.status(500).json({ error: 'Sunucu hatası' });
  }
});

// ✅ ÜRÜN OLUŞTUR (token gerekli)
router.post('/', verifyToken(), async (req, res) => {
  try {
    const { name, image, description, price, stock } = req.body;

    // Validation
    if (!name || !image || !description || price === undefined || stock === undefined) {
      return res.status(400).json({ 
        error: 'Tüm alanlar gereklidir: name, image, description, price, stock' 
      });
    }

    if (price < 0 || stock < 0) {
      return res.status(400).json({ 
        error: 'Fiyat ve stok negatif olamaz' 
      });
    }

    console.log("User ID:", req.user._id);

    const newProduct = new Product({
      name,
      image,
      description,
      price: Number(price),
      stock: Number(stock),
      createdBy: req.user._id
    });

    await newProduct.save();
    
    // Populate edilerek geri döndür
    await newProduct.populate('createdBy', 'username email');
    
    console.log("🟢 Ürün oluşturuldu:", newProduct.name);
    res.status(201).json({ 
      message: 'Ürün başarıyla oluşturuldu', 
      product: newProduct 
    });
  } catch (err) {
    console.error("❌ Ürün oluşturma hatası:", err);
    
    if (err.name === 'ValidationError') {
      const errors = Object.values(err.errors).map(e => e.message);
      return res.status(400).json({ error: errors.join(', ') });
    }
    
    res.status(500).json({ error: 'Sunucu hatası' });
  }
});

// ✅ ÜRÜN GÜNCELLE (token gerekli, sadece ürün sahibi veya admin)
router.put('/:id', verifyToken(), async (req, res) => {
  try {
    const productId = req.params.id;
    const updates = req.body;

    // Önce ürünü bul
    const product = await Product.findById(productId);
    
    if (!product) {
      return res.status(404).json({ error: 'Ürün bulunamadı' });
    }

    // Yetki kontrolü - sadece ürün sahibi veya admin güncelleyebilir
    if (product.createdBy.toString() !== req.user._id.toString() && !req.user.isAdmin) {
      return res.status(403).json({ 
        error: 'Bu ürünü güncelleme yetkiniz yok' 
      });
    }

    // createdBy alanının güncellenmesini engelle
    delete updates.createdBy;

    // Sayısal alanları kontrol et
    if (updates.price !== undefined && updates.price < 0) {
      return res.status(400).json({ error: 'Fiyat negatif olamaz' });
    }
    if (updates.stock !== undefined && updates.stock < 0) {
      return res.status(400).json({ error: 'Stok negatif olamaz' });
    }

    const updatedProduct = await Product.findByIdAndUpdate(
      productId, 
      updates, 
      { new: true, runValidators: true }
    ).populate('createdBy', 'username email');

    console.log("🟡 Ürün güncellendi:", updatedProduct.name);
    res.json({ 
      message: 'Ürün başarıyla güncellendi', 
      product: updatedProduct 
    });
  } catch (err) {
    console.error("❌ Ürün güncelleme hatası:", err);
    
    if (err.name === 'CastError') {
      return res.status(400).json({ error: 'Geçersiz ürün ID formatı' });
    }
    if (err.name === 'ValidationError') {
      const errors = Object.values(err.errors).map(e => e.message);
      return res.status(400).json({ error: errors.join(', ') });
    }
    
    res.status(500).json({ error: 'Sunucu hatası' });
  }
});

// ✅ ÜRÜN SİL (token gerekli, sadece ürün sahibi veya admin)
router.delete('/:id', verifyToken(), async (req, res) => {
  try {
    const productId = req.params.id;

    // Önce ürünü bul
    const product = await Product.findById(productId);
    
    if (!product) {
      return res.status(404).json({ error: 'Ürün bulunamadı' });
    }

    // Yetki kontrolü - sadece ürün sahibi veya admin silebilir
    if (product.createdBy.toString() !== req.user._id.toString() && !req.user.isAdmin) {
      return res.status(403).json({ 
        error: 'Bu ürünü silme yetkiniz yok' 
      });
    }

    const deletedProduct = await Product.findByIdAndDelete(productId);

    console.log("🔴 Ürün silindi:", deletedProduct.name);
    res.json({ 
      message: 'Ürün başarıyla silindi', 
      product: deletedProduct 
    });
  } catch (err) {
    console.error("❌ Ürün silme hatası:", err);
    
    if (err.name === 'CastError') {
      return res.status(400).json({ error: 'Geçersiz ürün ID formatı' });
    }
    
    res.status(500).json({ error: 'Sunucu hatası' });
  }
});

// ✅ KULLANICININ ÜRÜNLERİNİ GETIR (token gerekli)
router.get('/user/my-products', verifyToken(), async (req, res) => {
  try {
    const products = await Product.find({ createdBy: req.user._id })
      .populate('createdBy', 'username email')
      .sort({ createdAt: -1 });

    res.json({ 
      message: 'Ürünleriniz başarıyla getirildi', 
      products,
      count: products.length 
    });
  } catch (err) {
    console.error("❌ Kullanıcı ürünleri getirme hatası:", err);
    res.status(500).json({ error: 'Sunucu hatası' });
  }
});

module.exports = router;
const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Ürün adı gereklidir'],
    trim: true,
    maxlength: [100, 'Ürün adı 100 karakterden fazla olamaz']
  },
  image: {
    type: String,
    required: [true, 'Ürün resmi gereklidir']
  },
  description: {
    type: String,
    required: [true, 'Ürün açıklaması gereklidir'],
    maxlength: [500, 'Açıklama 500 karakterden fazla olamaz']
  },
  price: {
    type: Number,
    required: [true, 'Fiyat gereklidir'],
    min: [0, 'Fiyat negatif olamaz']
  },
  stock: {
    type: Number,
    required: [true, 'Stok miktarı gereklidir'],
    min: [0, 'Stok negatif olamaz'],
    default: 0
  },
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: [true, 'Ürün oluşturan kullanıcı gereklidir']
  }
}, {
  timestamps: true // createdAt ve updatedAt otomatik ekler
});

module.exports = mongoose.model('Product', productSchema);
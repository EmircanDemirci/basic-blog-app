const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
    name: {
        type: String,
        required: [true, 'Ürün adı gereklidir'],
        trim: true,
        maxlength: [100, 'Ürün adı en fazla 100 karakter olabilir']
    },
    image: {
        type: String,
        required: [true, 'Ürün resmi gereklidir'],
        trim: true
    },
    description: {
        type: String,
        required: [true, 'Ürün açıklaması gereklidir'],
        trim: true,
        maxlength: [1000, 'Açıklama en fazla 1000 karakter olabilir']
    },
    price: {
        type: Number,
        required: [true, 'Ürün fiyatı gereklidir'],
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
    timestamps: true
});

// İndexler
productSchema.index({ name: 'text', description: 'text' });
productSchema.index({ createdBy: 1 });
productSchema.index({ price: 1 });
productSchema.index({ createdAt: -1 });

module.exports = mongoose.model('Product', productSchema);
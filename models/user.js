const mongoose = require("mongoose");
const bcrypt = require("bcrypt");

const Schema = mongoose.Schema;

// 🎭 Kullanıcı rolleri enum
const ROLES = {
    USER: 'user',
    MODERATOR: 'moderator', 
    ADMIN: 'admin'
};

// 📊 Hesap durumu enum
const ACCOUNT_STATUS = {
    ACTIVE: 'active',
    INACTIVE: 'inactive',
    SUSPENDED: 'suspended',
    PENDING_VERIFICATION: 'pending_verification'
};

const userSchema = new Schema({
    // 👤 Temel kullanıcı bilgileri
    username: {
        type: String,
        required: [true, 'Kullanıcı adı gereklidir'],
        unique: true,
        trim: true,
        minlength: [3, 'Kullanıcı adı en az 3 karakter olmalıdır'],
        maxlength: [30, 'Kullanıcı adı en fazla 30 karakter olabilir'],
        match: [/^[a-zA-Z0-9_]+$/, 'Kullanıcı adı sadece harf, sayı ve alt çizgi içerebilir']
    },
    
    // 📧 Email bilgileri
    email: {
        type: String,
        required: [true, 'Email adresi gereklidir'],
        unique: true,
        lowercase: true,
        trim: true,
        match: [/^[^\s@]+@[^\s@]+\.[^\s@]+$/, 'Lütfen geçerli bir email adresi girin']
    },
    
    // 🔐 Şifre bilgileri
    password: {
        type: String,
        required: [true, 'Şifre gereklidir'],
        minlength: [8, 'Şifre en az 8 karakter olmalıdır'],
        validate: {
            validator: function(password) {
                // Şifre gücü kontrolü: en az 1 büyük harf, 1 küçük harf, 1 sayı
                return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password);
            },
            message: 'Şifre en az 1 büyük harf, 1 küçük harf ve 1 sayı içermelidir'
        }
    },
    
    // 📱 İletişim bilgileri
    tel: {
        type: String,
        required: [true, 'Telefon numarası gereklidir'],
        match: [/^(\+90)?5\d{9}$/, 'Geçerli bir Türkiye telefon numarası girin (5XXXXXXXXX)']
    },
    
    country: {
        type: String,
        required: [true, 'Ülke bilgisi gereklidir'],
        trim: true,
        maxlength: [50, 'Ülke adı en fazla 50 karakter olabilir']
    },
    
    // 🖼️ Profil bilgileri
    profilePicture: {
        type: String,
        default: null,
        validate: {
            validator: function(url) {
                if (!url) return true; // null/undefined kabul edilir
                return /^https?:\/\/.+\.(jpg|jpeg|png|gif|webp)$/i.test(url);
            },
            message: 'Geçerli bir resim URL\'si girin (.jpg, .jpeg, .png, .gif, .webp)'
        }
    },
    
    // 👥 Rol ve yetki sistemi
    role: {
        type: String,
        enum: Object.values(ROLES),
        default: ROLES.USER,
        required: true
    },
    
    // 📊 Hesap durumu
    accountStatus: {
        type: String,
        enum: Object.values(ACCOUNT_STATUS),
        default: ACCOUNT_STATUS.PENDING_VERIFICATION,
        required: true
    },
    
    // ✅ Email doğrulama
    emailVerified: {
        type: Boolean,
        default: false
    },
    
    emailVerificationToken: {
        type: String,
        default: null
    },
    
    // 🔄 Şifre sıfırlama
    resetPasswordToken: {
        type: String,
        default: null
    },
    
    resetPasswordExpires: {
        type: Date,
        default: null
    },
    
    // 🕒 Tarih bilgileri
    lastLogin: {
        type: Date,
        default: null
    },
    
    createdAt: {
        type: Date,
        default: Date.now
    },
    
    updatedAt: {
        type: Date,
        default: Date.now
    },
    
    // 🔒 Güvenlik bilgileri
    loginAttempts: {
        type: Number,
        default: 0
    },
    
    lockedUntil: {
        type: Date,
        default: null
    }
}, {
    timestamps: true, // createdAt ve updatedAt otomatik olarak güncellenir
    versionKey: false // __v alanını kaldır
});

// 📚 İndeksler - Performans için
userSchema.index({ email: 1 }, { unique: true });
userSchema.index({ username: 1 }, { unique: true });
userSchema.index({ role: 1 });
userSchema.index({ accountStatus: 1 });
userSchema.index({ emailVerified: 1 });
userSchema.index({ createdAt: -1 });

// 🔐 Şifre hashleme işlemi (save'den önce)
userSchema.pre('save', async function(next) {
    const user = this;

    // Eğer şifre değiştirilmediyse hashleme yapma
    if (!user.isModified('password')) return next();

    try {
        // Salt rounds: 12 (güvenlik için yüksek)
        const salt = await bcrypt.genSalt(12);
        const hashedPassword = await bcrypt.hash(user.password, salt);
        user.password = hashedPassword;
        next();
    } catch (error) {
        return next(error);
    }
});

// 🔍 Şifre karşılaştırma metodu
userSchema.methods.comparePassword = async function(candidatePassword) {
    try {
        return await bcrypt.compare(candidatePassword, this.password);
    } catch (error) {
        throw new Error('Şifre karşılaştırma hatası: ' + error.message);
    }
};

// 🔒 Hesap kilitli mi kontrol et
userSchema.virtual('isLocked').get(function() {
    return !!(this.lockedUntil && this.lockedUntil > Date.now());
});

// 🚫 Login denemesi başarısız olduğunda
userSchema.methods.incLoginAttempts = function() {
    // Eğer hesap kilitli değilse ve deneme sayısı limiti aşmamışsa
    if (this.loginAttempts < 5 && !this.isLocked) {
        this.loginAttempts += 1;
        return this.save();
    }
    
    // 5 başarısız denemeden sonra hesabı 2 saat kilitle
    this.loginAttempts = 5;
    this.lockedUntil = Date.now() + (2 * 60 * 60 * 1000); // 2 saat
    return this.save();
};

// ✅ Başarılı login sonrası temizlik
userSchema.methods.resetLoginAttempts = function() {
    this.loginAttempts = 0;
    this.lockedUntil = null;
    this.lastLogin = new Date();
    return this.save();
};

// 🎭 Rol kontrol metodları
userSchema.methods.isAdmin = function() {
    return this.role === ROLES.ADMIN;
};

userSchema.methods.isModerator = function() {
    return this.role === ROLES.MODERATOR;
};

userSchema.methods.isUser = function() {
    return this.role === ROLES.USER;
};

userSchema.methods.hasRole = function(role) {
    return this.role === role;
};

// 📧 Email doğrulama token oluştur
userSchema.methods.generateEmailVerificationToken = function() {
    const crypto = require('crypto');
    this.emailVerificationToken = crypto.randomBytes(32).toString('hex');
    return this.emailVerificationToken;
};

// 🔄 Şifre sıfırlama token oluştur
userSchema.methods.generatePasswordResetToken = function() {
    const crypto = require('crypto');
    this.resetPasswordToken = crypto.randomBytes(32).toString('hex');
    this.resetPasswordExpires = Date.now() + (1 * 60 * 60 * 1000); // 1 saat
    return this.resetPasswordToken;
};

// 🔍 JSON çıktısında şifreyi gizle
userSchema.methods.toJSON = function() {
    const userObject = this.toObject();
    delete userObject.password;
    delete userObject.emailVerificationToken;
    delete userObject.resetPasswordToken;
    delete userObject.loginAttempts;
    delete userObject.lockedUntil;
    return userObject;
};

// 📤 Export
module.exports = mongoose.model("User", userSchema);

// 📤 Enums'ları da export et
module.exports.ROLES = ROLES;
module.exports.ACCOUNT_STATUS = ACCOUNT_STATUS;
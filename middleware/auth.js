const User = require('../models/user');
const { ROLES } = require('../models/user');

// 🔐 Kullanıcı doğrulama middleware'i
const authenticateUser = async (req, res, next) => {
    try {
        // Burada JWT token kontrolü yapılabilir
        // Şimdilik session tabanlı varsayıyorum
        
        if (!req.session || !req.session.userId) {
            return res.status(401).json({
                success: false,
                message: 'Giriş yapmanız gerekiyor'
            });
        }

        const user = await User.findById(req.session.userId).select('-password');
        
        if (!user) {
            return res.status(401).json({
                success: false,
                message: 'Geçersiz kullanıcı'
            });
        }

        // Hesap durumu kontrolü
        if (user.accountStatus !== 'active') {
            return res.status(403).json({
                success: false,
                message: 'Hesabınız aktif değil. Lütfen email adresinizi doğrulayın.'
            });
        }

        // Hesap kilitli mi kontrol et
        if (user.isLocked) {
            return res.status(423).json({
                success: false,
                message: 'Hesabınız geçici olarak kilitlenmiştir. Lütfen daha sonra tekrar deneyin.'
            });
        }

        req.user = user;
        next();
    } catch (error) {
        return res.status(500).json({
            success: false,
            message: 'Sunucu hatası: ' + error.message
        });
    }
};

// 🎭 Rol kontrolü middleware'i
const requireRole = (roles) => {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({
                success: false,
                message: 'Giriş yapmanız gerekiyor'
            });
        }

        // Tek rol string olarak gelirse array'e çevir
        const allowedRoles = Array.isArray(roles) ? roles : [roles];
        
        if (!allowedRoles.includes(req.user.role)) {
            return res.status(403).json({
                success: false,
                message: 'Bu işlem için yetkiniz bulunmuyor'
            });
        }

        next();
    };
};

// 🛡️ Admin yetkisi gerekli
const requireAdmin = requireRole(ROLES.ADMIN);

// 🛡️ Moderator veya Admin yetkisi gerekli
const requireModerator = requireRole([ROLES.MODERATOR, ROLES.ADMIN]);

module.exports = {
    authenticateUser,
    requireRole,
    requireAdmin,
    requireModerator
};
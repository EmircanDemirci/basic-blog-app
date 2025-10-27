const jwt = require('jsonwebtoken');
const User = require('../models/User');

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-here-change-in-production';

const verifyToken = () => {
    return async (req, res, next) => {
        try {
            const authHeader = req.headers.authorization;
            
            if (!authHeader) {
                return res.status(401).json({ 
                    error: 'Token bulunamadı. Lütfen giriş yapın.' 
                });
            }

            const token = authHeader.split(' ')[1]; // "Bearer TOKEN" formatından TOKEN'ı al
            
            if (!token) {
                return res.status(401).json({ 
                    error: 'Token formatı hatalı. Bearer token bekleniyor.' 
                });
            }

            // Token'ı doğrula
            const decoded = jwt.verify(token, JWT_SECRET);
            
            // Kullanıcıyı veritabanından getir
            const user = await User.findById(decoded.userId).select('-password');
            
            if (!user) {
                return res.status(401).json({ 
                    error: 'Geçersiz token. Kullanıcı bulunamadı.' 
                });
            }

            // req.user'a kullanıcı bilgilerini ekle
            req.user = user;
            next();
            
        } catch (error) {
            console.error('Token doğrulama hatası:', error);
            
            if (error.name === 'JsonWebTokenError') {
                return res.status(401).json({ 
                    error: 'Geçersiz token.' 
                });
            }
            
            if (error.name === 'TokenExpiredError') {
                return res.status(401).json({ 
                    error: 'Token süresi dolmuş. Lütfen tekrar giriş yapın.' 
                });
            }
            
            res.status(500).json({ 
                error: 'Token doğrulama sırasında sunucu hatası oluştu.' 
            });
        }
    };
};

module.exports = verifyToken;
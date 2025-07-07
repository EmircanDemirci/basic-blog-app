const express = require('express');
const router = express.Router();

// Controllers ve middleware'leri import et
const userController = require('../controllers/userController');
const { authenticateUser, requireAdmin, requireModerator } = require('../middleware/auth');

// 🔓 Kimlik doğrulama gerektirmeyen route'lar

// 👤 Kullanıcı kayıt
router.post('/register', userController.register);

// 🔐 Kullanıcı giriş
router.post('/login', userController.login);

// ✅ Email doğrulama
router.get('/verify-email/:token', userController.verifyEmail);

// 🔒 Kimlik doğrulama gerektiren route'lar

// 🚪 Kullanıcı çıkış
router.post('/logout', authenticateUser, userController.logout);

// 📋 Kullanıcı profili görüntüleme
router.get('/profile', authenticateUser, userController.getProfile);

// ✏️ Profil güncelleme
router.put('/profile', authenticateUser, userController.updateProfile);

// 🔄 Şifre değiştirme
router.put('/change-password', authenticateUser, userController.changePassword);

// 🛡️ Admin yetkisi gerektiren route'lar

// 👥 Tüm kullanıcıları listele
router.get('/admin/users', authenticateUser, requireAdmin, userController.getAllUsers);

// 🔧 Kullanıcı rolünü değiştir
router.put('/admin/users/:userId/role', authenticateUser, requireAdmin, userController.changeUserRole);

module.exports = router;
const User = require('../models/user');
const { ROLES, ACCOUNT_STATUS } = require('../models/user');

// 👤 Kullanıcı kayıt işlemi
const register = async (req, res) => {
    try {
        const { username, email, password, tel, country } = req.body;

        // Kullanıcı zaten var mı kontrol et
        const existingUser = await User.findOne({
            $or: [{ email }, { username }]
        });

        if (existingUser) {
            return res.status(400).json({
                success: false,
                message: 'Bu email veya kullanıcı adı zaten kullanılıyor'
            });
        }

        // Yeni kullanıcı oluştur
        const newUser = new User({
            username,
            email,
            password,
            tel,
            country
        });

        // Email doğrulama token'ı oluştur
        newUser.generateEmailVerificationToken();

        await newUser.save();

        // TODO: Email doğrulama maili gönder
        // sendVerificationEmail(newUser.email, newUser.emailVerificationToken);

        res.status(201).json({
            success: true,
            message: 'Hesabınız oluşturuldu. Lütfen email adresinizi doğrulayın.',
            user: {
                id: newUser._id,
                username: newUser.username,
                email: newUser.email,
                accountStatus: newUser.accountStatus
            }
        });

    } catch (error) {
        res.status(400).json({
            success: false,
            message: error.message
        });
    }
};

// 🔐 Kullanıcı giriş işlemi
const login = async (req, res) => {
    try {
        const { email, password } = req.body;

        // Kullanıcıyı bul
        const user = await User.findOne({ email });

        if (!user) {
            return res.status(401).json({
                success: false,
                message: 'Geçersiz email veya şifre'
            });
        }

        // Hesap kilitli mi kontrol et
        if (user.isLocked) {
            return res.status(423).json({
                success: false,
                message: 'Hesabınız geçici olarak kilitlenmiştir. Lütfen daha sonra tekrar deneyin.'
            });
        }

        // Şifre doğru mu kontrol et
        const isPasswordValid = await user.comparePassword(password);

        if (!isPasswordValid) {
            // Başarısız login denemesini kaydet
            await user.incLoginAttempts();
            
            return res.status(401).json({
                success: false,
                message: 'Geçersiz email veya şifre'
            });
        }

        // Email doğrulanmış mı kontrol et
        if (!user.emailVerified) {
            return res.status(403).json({
                success: false,
                message: 'Lütfen önce email adresinizi doğrulayın'
            });
        }

        // Başarılı login
        await user.resetLoginAttempts();

        // Session oluştur
        req.session.userId = user._id;

        res.json({
            success: true,
            message: 'Giriş başarılı',
            user: {
                id: user._id,
                username: user.username,
                email: user.email,
                role: user.role,
                accountStatus: user.accountStatus,
                lastLogin: user.lastLogin
            }
        });

    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Sunucu hatası: ' + error.message
        });
    }
};

// 🚪 Kullanıcı çıkış işlemi
const logout = (req, res) => {
    req.session.destroy((err) => {
        if (err) {
            return res.status(500).json({
                success: false,
                message: 'Çıkış yapılırken hata oluştu'
            });
        }

        res.json({
            success: true,
            message: 'Başarıyla çıkış yapıldı'
        });
    });
};

// ✅ Email doğrulama
const verifyEmail = async (req, res) => {
    try {
        const { token } = req.params;

        const user = await User.findOne({ emailVerificationToken: token });

        if (!user) {
            return res.status(400).json({
                success: false,
                message: 'Geçersiz doğrulama token\'ı'
            });
        }

        // Email'i doğrulanmış olarak işaretle
        user.emailVerified = true;
        user.emailVerificationToken = null;
        user.accountStatus = ACCOUNT_STATUS.ACTIVE;

        await user.save();

        res.json({
            success: true,
            message: 'Email adresiniz başarıyla doğrulandı. Artık giriş yapabilirsiniz.'
        });

    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Sunucu hatası: ' + error.message
        });
    }
};

// 📋 Kullanıcı profili
const getProfile = async (req, res) => {
    try {
        const user = await User.findById(req.user._id);
        
        res.json({
            success: true,
            user: user
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Sunucu hatası: ' + error.message
        });
    }
};

// ✏️ Profil güncelleme
const updateProfile = async (req, res) => {
    try {
        const { username, tel, country, profilePicture } = req.body;
        const userId = req.user._id;

        // Username benzersizlik kontrolü
        if (username) {
            const existingUser = await User.findOne({ 
                username, 
                _id: { $ne: userId } 
            });

            if (existingUser) {
                return res.status(400).json({
                    success: false,
                    message: 'Bu kullanıcı adı zaten kullanılıyor'
                });
            }
        }

        const updateData = {};
        if (username) updateData.username = username;
        if (tel) updateData.tel = tel;
        if (country) updateData.country = country;
        if (profilePicture !== undefined) updateData.profilePicture = profilePicture;

        const user = await User.findByIdAndUpdate(
            userId,
            updateData,
            { new: true, runValidators: true }
        );

        res.json({
            success: true,
            message: 'Profil başarıyla güncellendi',
            user: user
        });

    } catch (error) {
        res.status(400).json({
            success: false,
            message: error.message
        });
    }
};

// 🔄 Şifre değiştirme
const changePassword = async (req, res) => {
    try {
        const { currentPassword, newPassword } = req.body;
        const userId = req.user._id;

        const user = await User.findById(userId);

        // Mevcut şifre doğru mu kontrol et
        const isCurrentPasswordValid = await user.comparePassword(currentPassword);

        if (!isCurrentPasswordValid) {
            return res.status(400).json({
                success: false,
                message: 'Mevcut şifreniz yanlış'
            });
        }

        // Yeni şifreyi güncelle
        user.password = newPassword;
        await user.save();

        res.json({
            success: true,
            message: 'Şifreniz başarıyla güncellendi'
        });

    } catch (error) {
        res.status(400).json({
            success: false,
            message: error.message
        });
    }
};

// 👥 Tüm kullanıcıları listele (Admin only)
const getAllUsers = async (req, res) => {
    try {
        const { page = 1, limit = 10, role, accountStatus } = req.query;

        const filter = {};
        if (role) filter.role = role;
        if (accountStatus) filter.accountStatus = accountStatus;

        const users = await User.find(filter)
            .limit(limit * 1)
            .skip((page - 1) * limit)
            .sort({ createdAt: -1 });

        const total = await User.countDocuments(filter);

        res.json({
            success: true,
            users: users,
            totalPages: Math.ceil(total / limit),
            currentPage: page,
            total: total
        });

    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Sunucu hatası: ' + error.message
        });
    }
};

// 🔧 Kullanıcı rolünü değiştir (Admin only)
const changeUserRole = async (req, res) => {
    try {
        const { userId } = req.params;
        const { role } = req.body;

        if (!Object.values(ROLES).includes(role)) {
            return res.status(400).json({
                success: false,
                message: 'Geçersiz rol'
            });
        }

        const user = await User.findByIdAndUpdate(
            userId,
            { role },
            { new: true }
        );

        if (!user) {
            return res.status(404).json({
                success: false,
                message: 'Kullanıcı bulunamadı'
            });
        }

        res.json({
            success: true,
            message: 'Kullanıcı rolü başarıyla güncellendi',
            user: user
        });

    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Sunucu hatası: ' + error.message
        });
    }
};

module.exports = {
    register,
    login,
    logout,
    verifyEmail,
    getProfile,
    updateProfile,
    changePassword,
    getAllUsers,
    changeUserRole
};
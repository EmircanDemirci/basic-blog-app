const jwt = require("jsonwebtoken");
require("dotenv").config();

const verifyToken = (requireAdmin = false) => {
  return (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    console.log("📦 Gelen Header:", req.headers['authorization']);
    console.log("🔑 Token:", token);

    if (!token) {
      return res.status(401).json({ message: "Token eksik!" });
    }

    jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
      if (err) {
        console.error("❌ Token doğrulama hatası:", err.message);
        return res.status(403).json({ message: "Token geçersiz!" });
      }

      req.user = user;
      console.log("✅ Token doğrulandı, Kullanıcı:", user);

      if (requireAdmin && !user.isAdmin) {
        return res.status(403).json({ message: "Yetkisiz erişim. Admin değilsin!" });
      }

      next();
    });
  };
};

module.exports = verifyToken;
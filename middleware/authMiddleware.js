const jwt = require("jsonwebtoken");
const rateLimit = require('express-rate-limit');
require("dotenv").config();

// Rate limiting for token verification attempts
const tokenVerifyLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // More lenient for token verification
  message: {
    status: "FAILED",
    message: "Too many token verification attempts, please try again later"
  },
  standardHeaders: true,
  legacyHeaders: false,
  skip: (req) => {
    // Skip rate limiting for valid tokens to avoid blocking legitimate users
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    if (!token) return false;
    
    try {
      jwt.verify(token, process.env.JWT_SECRET);
      return true; // Skip rate limiting for valid tokens
    } catch {
      return false; // Apply rate limiting for invalid tokens
    }
  }
});

// Utility function for logging (can be replaced with proper logger like Winston)
const logger = {
  info: (message, data) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log(`ℹ️ [AUTH] ${message}`, data || '');
    }
  },
  warn: (message, data) => {
    console.warn(`⚠️ [AUTH] ${message}`, data || '');
  },
  error: (message, error) => {
    console.error(`❌ [AUTH] ${message}`, error?.message || error || '');
  }
};

// Token extraction utility
const extractToken = (req) => {
  const authHeader = req.headers['authorization'];
  
  // Support both "Bearer token" and "token" formats
  if (authHeader) {
    if (authHeader.startsWith('Bearer ')) {
      return authHeader.slice(7); // Remove "Bearer " prefix
    }
    // If no Bearer prefix, treat the whole header as token
    return authHeader;
  }
  
  // Also check for token in cookies as fallback
  if (req.cookies && req.cookies.token) {
    return req.cookies.token;
  }
  
  return null;
};

// Token validation utility
const validateTokenFormat = (token) => {
  if (!token || typeof token !== 'string') {
    return false;
  }
  
  // Basic JWT format check (header.payload.signature)
  const parts = token.split('.');
  if (parts.length !== 3) {
    return false;
  }
  
  // Check if each part is base64url encoded (basic check)
  const base64urlPattern = /^[A-Za-z0-9_-]+$/;
  return parts.every(part => base64urlPattern.test(part));
};

// Main verification middleware
const verifyToken = (options = {}) => {
  const {
    requireAdmin = false,
    allowExpired = false,
    customRoles = [],
    skipRateLimit = false
  } = options;

  return [
    // Apply rate limiting unless explicitly skipped
    ...(skipRateLimit ? [] : [tokenVerifyLimiter]),
    
    (req, res, next) => {
      try {
        // Extract token from various sources
        const token = extractToken(req);
        
        logger.info('Token verification attempt', {
          ip: req.ip,
          userAgent: req.get('User-Agent'),
          endpoint: req.originalUrl
        });

        // Check if token exists
        if (!token) {
          logger.warn('Missing token', { ip: req.ip });
          return res.status(401).json({
            status: "FAILED",
            message: "Access token is required",
            code: "TOKEN_MISSING"
          });
        }

        // Validate token format
        if (!validateTokenFormat(token)) {
          logger.warn('Invalid token format', { ip: req.ip });
          return res.status(401).json({
            status: "FAILED",
            message: "Invalid token format",
            code: "TOKEN_INVALID_FORMAT"
          });
        }

        // Verify JWT token
        const jwtOptions = {
          ignoreExpiration: allowExpired
        };

        jwt.verify(token, process.env.JWT_SECRET, jwtOptions, (err, decoded) => {
          if (err) {
            logger.error('Token verification failed', err);
            
            let errorMessage = "Invalid token";
            let errorCode = "TOKEN_INVALID";
            
            switch (err.name) {
              case 'TokenExpiredError':
                errorMessage = "Token has expired";
                errorCode = "TOKEN_EXPIRED";
                break;
              case 'JsonWebTokenError':
                errorMessage = "Invalid token";
                errorCode = "TOKEN_INVALID";
                break;
              case 'NotBeforeError':
                errorMessage = "Token not active yet";
                errorCode = "TOKEN_NOT_ACTIVE";
                break;
              default:
                errorMessage = "Token verification failed";
                errorCode = "TOKEN_VERIFICATION_FAILED";
            }

            return res.status(403).json({
              status: "FAILED",
              message: errorMessage,
              code: errorCode
            });
          }

          // Validate token payload
          if (!decoded || !decoded.id || !decoded.email) {
            logger.error('Invalid token payload', { decoded });
            return res.status(403).json({
              status: "FAILED",
              message: "Invalid token payload",
              code: "TOKEN_INVALID_PAYLOAD"
            });
          }

          // Attach user info to request
          req.user = decoded;
          req.tokenInfo = {
            token,
            issuedAt: new Date(decoded.iat * 1000),
            expiresAt: new Date(decoded.exp * 1000),
            isAdmin: decoded.isAdmin || false
          };

          logger.info('Token verified successfully', {
            userId: decoded.id,
            email: decoded.email,
            isAdmin: decoded.isAdmin
          });

          // Check admin requirement
          if (requireAdmin && !decoded.isAdmin) {
            logger.warn('Admin access required', {
              userId: decoded.id,
              email: decoded.email,
              endpoint: req.originalUrl
            });
            return res.status(403).json({
              status: "FAILED",
              message: "Admin privileges required",
              code: "INSUFFICIENT_PRIVILEGES"
            });
          }

          // Check custom roles if specified
          if (customRoles.length > 0) {
            const userRole = decoded.role || 'user';
            if (!customRoles.includes(userRole)) {
              logger.warn('Insufficient role privileges', {
                userId: decoded.id,
                userRole,
                requiredRoles: customRoles
              });
              return res.status(403).json({
                status: "FAILED",
                message: `Required roles: ${customRoles.join(', ')}`,
                code: "INSUFFICIENT_ROLE"
              });
            }
          }

          next();
        });

      } catch (error) {
        logger.error('Unexpected error in token verification', error);
        return res.status(500).json({
          status: "FAILED",
          message: "Internal server error during authentication",
          code: "AUTH_INTERNAL_ERROR"
        });
      }
    }
  ];
};

// Convenience middleware functions
const requireAuth = () => verifyToken();
const requireAdmin = () => verifyToken({ requireAdmin: true });
const requireRole = (roles) => verifyToken({ customRoles: Array.isArray(roles) ? roles : [roles] });

// Optional user middleware (doesn't fail if no token)
const optionalAuth = () => [
  (req, res, next) => {
    const token = extractToken(req);
    
    if (!token) {
      req.user = null;
      return next();
    }

    if (!validateTokenFormat(token)) {
      req.user = null;
      return next();
    }

    jwt.verify(token, process.env.JWT_SECRET, (err, decoded) => {
      if (err) {
        req.user = null;
      } else {
        req.user = decoded;
        req.tokenInfo = {
          token,
          issuedAt: new Date(decoded.iat * 1000),
          expiresAt: new Date(decoded.exp * 1000),
          isAdmin: decoded.isAdmin || false
        };
      }
      next();
    });
  }
];

// Token refresh utility (for routes that need to check if refresh is needed)
const checkTokenExpiry = (req, res, next) => {
  if (req.tokenInfo && req.tokenInfo.expiresAt) {
    const timeUntilExpiry = req.tokenInfo.expiresAt.getTime() - Date.now();
    const hoursUntilExpiry = timeUntilExpiry / (1000 * 60 * 60);
    
    // Add refresh warning if token expires in less than 2 hours
    if (hoursUntilExpiry < 2 && hoursUntilExpiry > 0) {
      res.set('X-Token-Refresh-Needed', 'true');
      res.set('X-Token-Expires-At', req.tokenInfo.expiresAt.toISOString());
    }
  }
  next();
};

module.exports = {
  verifyToken,
  requireAuth,
  requireAdmin,
  requireRole,
  optionalAuth,
  checkTokenExpiry,
  extractToken,
  validateTokenFormat
};
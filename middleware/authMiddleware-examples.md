# Authentication Middleware Usage Examples

This document provides comprehensive examples of how to use the improved authentication middleware.

## Basic Usage

### 1. Require Authentication (Any Logged-in User)

```javascript
const { requireAuth } = require('./middleware/authMiddleware');

// Protect route - requires valid token
router.get('/profile', requireAuth(), (req, res) => {
  res.json({
    status: "SUCCESS",
    data: {
      user: req.user,
      tokenInfo: req.tokenInfo
    }
  });
});
```

### 2. Require Admin Access

```javascript
const { requireAdmin } = require('./middleware/authMiddleware');

// Admin only route
router.get('/admin/dashboard', requireAdmin(), (req, res) => {
  res.json({
    status: "SUCCESS",
    message: "Welcome to admin dashboard",
    data: { user: req.user }
  });
});
```

### 3. Role-Based Access Control

```javascript
const { requireRole } = require('./middleware/authMiddleware');

// Require specific role
router.get('/moderator/panel', requireRole('moderator'), (req, res) => {
  res.json({
    status: "SUCCESS",
    message: "Moderator panel access granted"
  });
});

// Require multiple roles (any of them)
router.get('/staff/area', requireRole(['admin', 'moderator', 'staff']), (req, res) => {
  res.json({
    status: "SUCCESS",
    message: "Staff area access granted"
  });
});
```

### 4. Optional Authentication

```javascript
const { optionalAuth } = require('./middleware/authMiddleware');

// Public route with optional user info
router.get('/public/content', optionalAuth(), (req, res) => {
  const response = {
    status: "SUCCESS",
    data: { content: "Public content here" }
  };
  
  // Add user-specific data if logged in
  if (req.user) {
    response.data.personalizedContent = "Welcome back, " + req.user.email;
  }
  
  res.json(response);
});
```

## Advanced Usage

### 5. Custom Options

```javascript
const { verifyToken } = require('./middleware/authMiddleware');

// Allow expired tokens (for refresh scenarios)
router.post('/refresh-token', verifyToken({ 
  allowExpired: true,
  skipRateLimit: true 
}), (req, res) => {
  // Handle token refresh logic
  res.json({
    status: "SUCCESS",
    message: "Token refresh endpoint"
  });
});

// Custom role requirements with admin fallback
router.get('/special-access', verifyToken({ 
  customRoles: ['premium', 'vip'],
  requireAdmin: false // Admin can also access
}), (req, res) => {
  res.json({
    status: "SUCCESS",
    message: "Special access granted"
  });
});
```

### 6. Token Expiry Checking

```javascript
const { requireAuth, checkTokenExpiry } = require('./middleware/authMiddleware');

// Check if token needs refresh
router.get('/user/data', requireAuth(), checkTokenExpiry, (req, res) => {
  res.json({
    status: "SUCCESS",
    data: req.user,
    // Client can check these headers:
    // X-Token-Refresh-Needed: true
    // X-Token-Expires-At: 2024-01-01T12:00:00.000Z
  });
});
```

## Error Handling Examples

### Client-Side Error Handling

```javascript
// Frontend example (axios)
const apiCall = async () => {
  try {
    const response = await axios.get('/api/protected-route', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    // Check for refresh warning
    if (response.headers['x-token-refresh-needed']) {
      console.log('Token refresh needed');
      // Trigger token refresh
    }
    
    return response.data;
  } catch (error) {
    if (error.response) {
      const { code, message } = error.response.data;
      
      switch (code) {
        case 'TOKEN_EXPIRED':
          // Redirect to login or refresh token
          window.location.href = '/login';
          break;
        case 'TOKEN_MISSING':
          // Handle missing token
          console.error('Authentication required');
          break;
        case 'INSUFFICIENT_PRIVILEGES':
          // Handle permission denied
          console.error('Access denied');
          break;
        default:
          console.error('Auth error:', message);
      }
    }
  }
};
```

## Multiple Token Sources

The middleware automatically checks for tokens in:

1. **Authorization Header (Bearer format):**
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **Authorization Header (Direct format):**
   ```
   Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. **Cookies:**
   ```javascript
   // Set cookie on client
   document.cookie = "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";
   ```

## Express App Integration

```javascript
const express = require('express');
const { requireAuth, requireAdmin, optionalAuth } = require('./middleware/authMiddleware');
const app = express();

// Public routes
app.get('/api/public', (req, res) => {
  res.json({ message: "Public endpoint" });
});

// Protected routes
app.get('/api/profile', requireAuth(), (req, res) => {
  res.json({ user: req.user });
});

// Admin routes
app.use('/api/admin', requireAdmin());
app.get('/api/admin/users', (req, res) => {
  res.json({ message: "Admin only - user list" });
});

// Mixed access routes
app.get('/api/posts', optionalAuth(), (req, res) => {
  const posts = getAllPosts();
  
  if (req.user) {
    // Add user-specific data for logged-in users
    posts.forEach(post => {
      post.isLiked = checkIfUserLiked(post.id, req.user.id);
    });
  }
  
  res.json({ posts });
});
```

## Error Response Format

All authentication errors follow this standardized format:

```json
{
  "status": "FAILED",
  "message": "Human-readable error message",
  "code": "ERROR_CODE_FOR_PROGRAMMATIC_HANDLING"
}
```

### Common Error Codes:

- `TOKEN_MISSING` - No token provided
- `TOKEN_INVALID_FORMAT` - Token format is invalid
- `TOKEN_EXPIRED` - Token has expired
- `TOKEN_INVALID` - Token signature/content is invalid
- `TOKEN_INVALID_PAYLOAD` - Token payload is malformed
- `INSUFFICIENT_PRIVILEGES` - User doesn't have admin rights
- `INSUFFICIENT_ROLE` - User doesn't have required role
- `AUTH_INTERNAL_ERROR` - Server error during authentication

## Security Features

1. **Rate Limiting:** Prevents brute force attacks on token verification
2. **Token Format Validation:** Validates JWT structure before processing
3. **Multiple Token Sources:** Supports various token transmission methods
4. **Detailed Logging:** Comprehensive logging for security monitoring
5. **Smart Rate Limiting:** Skips rate limiting for valid tokens
6. **Payload Validation:** Ensures token contains required fields

## Production Considerations

1. **Logging:** Replace console logs with proper logging library (Winston, etc.)
2. **Monitoring:** Monitor failed authentication attempts
3. **Token Refresh:** Implement token refresh mechanism
4. **Cookie Security:** Use secure, httpOnly cookies in production
5. **HTTPS:** Always use HTTPS in production for token security
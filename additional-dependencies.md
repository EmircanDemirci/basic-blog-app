# Additional Dependencies for Improved Authentication Router

The improved authentication router requires these additional npm packages:

## New Dependencies

```bash
npm install express-rate-limit express-validator
```

### Package Details:

1. **express-rate-limit** (^6.x.x)
   - Provides rate limiting middleware to prevent brute force attacks
   - Limits authentication attempts per IP address
   - Configurable time windows and request limits

2. **express-validator** (^7.x.x)
   - Provides comprehensive input validation and sanitization
   - Chainable validation rules with custom error messages
   - Built-in email, phone number, and other format validators

## Existing Dependencies (should already be installed)

- express
- bcrypt
- jsonwebtoken
- dotenv
- mongoose (for MongoDB models)

## Installation Command

```bash
npm install express-rate-limit express-validator
```

## Usage in Code

These packages are now used in the authentication router for:
- Input validation with detailed error messages
- Rate limiting to prevent brute force attacks
- Better security and user experience
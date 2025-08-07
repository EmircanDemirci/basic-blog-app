const express = require('express');
const router = express.Router();
const rateLimit = require('express-rate-limit');
const { body, validationResult } = require('express-validator');

// MongoDB user models
const User = require("../model/User");
const UserPermission = require('../model/userPermissionModel');
const jwt = require("jsonwebtoken");

require('dotenv').config();

// Password handler
const bcrypt = require('bcrypt');

// Rate limiting middleware
const authLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 5, // Limit each IP to 5 requests per windowMs
    message: {
        status: "FAILED",
        message: "Too many authentication attempts, please try again later"
    },
    standardHeaders: true,
    legacyHeaders: false,
});

// Validation rules
const signupValidation = [
    body('username')
        .trim()
        .notEmpty()
        .withMessage('Username is required')
        .matches(/^[a-zA-Z\s]+$/)
        .withMessage('Username can only contain letters and spaces')
        .isLength({ min: 2, max: 50 })
        .withMessage('Username must be between 2 and 50 characters'),
    
    body('email')
        .trim()
        .isEmail()
        .normalizeEmail()
        .withMessage('Please provide a valid email address'),
    
    body('password')
        .isLength({ min: 8 })
        .withMessage('Password must be at least 8 characters long')
        .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/)
        .withMessage('Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'),
    
    body('phoneNumber')
        .trim()
        .matches(/^(?:\+90|0)?5\d{9}$/)
        .withMessage('Please provide a valid Turkish phone number'),
    
    body('address')
        .trim()
        .notEmpty()
        .withMessage('Address is required')
        .isLength({ min: 5, max: 200 })
        .withMessage('Address must be between 5 and 200 characters'),
    
    body('role')
        .optional()
        .isIn(['user', 'admin', 'moderator'])
        .withMessage('Invalid role specified')
];

const signinValidation = [
    body('email')
        .trim()
        .isEmail()
        .normalizeEmail()
        .withMessage('Please provide a valid email address'),
    
    body('password')
        .notEmpty()
        .withMessage('Password is required')
];

// Utility functions
const generateToken = (user, isAdmin) => {
    return jwt.sign(
        {
            id: user._id,
            email: user.email,
            isAdmin: isAdmin || false
        },
        process.env.JWT_SECRET,
        { expiresIn: process.env.JWT_EXPIRES_IN || "1d" }
    );
};

const handleValidationErrors = (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({
            status: "FAILED",
            message: "Validation error",
            errors: errors.array()
        });
    }
    next();
};

const asyncHandler = (fn) => (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};

// Routes
router.post("/signup", authLimiter, signupValidation, handleValidationErrors, asyncHandler(async (req, res) => {
    const { username, email, password, phoneNumber, address, date, role = 'user' } = req.body;

    try {
        // Check if user already exists
        const existingUser = await User.findOne({ email });
        if (existingUser) {
            return res.status(409).json({
                status: "FAILED",
                message: "User with this email already exists"
            });
        }

        // Check if username is taken
        const existingUsername = await User.findOne({ username });
        if (existingUsername) {
            return res.status(409).json({
                status: "FAILED",
                message: "Username is already taken"
            });
        }

        // Hash password
        const saltRounds = 12; // Increased for better security
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        // Create new user
        const newUser = new User({
            username,
            email,
            password: hashedPassword,
            date: date || new Date(),
            phoneNumber,
            address,
            role
        });

        const savedUser = await newUser.save();
        
        // Remove password from response
        const userResponse = savedUser.toObject();
        delete userResponse.password;

        const isAdmin = role === 'admin';
        const token = generateToken(savedUser, isAdmin);

        res.status(201).json({
            status: "SUCCESS",
            message: "User registration successful",
            data: {
                user: userResponse,
                isAdmin,
                token
            }
        });

    } catch (error) {
        console.error('Signup error:', error);
        
        // Handle duplicate key errors
        if (error.code === 11000) {
            const field = Object.keys(error.keyPattern)[0];
            return res.status(409).json({
                status: "FAILED",
                message: `${field} already exists`
            });
        }

        res.status(500).json({
            status: "FAILED",
            message: "An error occurred during registration"
        });
    }
}));

router.post("/signin", authLimiter, signinValidation, handleValidationErrors, asyncHandler(async (req, res) => {
    const { email, password } = req.body;

    try {
        // Find user by email
        const user = await User.findOne({ email }).select('+password');
        if (!user) {
            return res.status(401).json({
                status: "FAILED",
                message: "Invalid email or password"
            });
        }

        // Check password
        const isPasswordValid = await bcrypt.compare(password, user.password);
        if (!isPasswordValid) {
            return res.status(401).json({
                status: "FAILED",
                message: "Invalid email or password"
            });
        }

        // Check user permissions
        let isAdmin = false;
        
        // First check if user role is admin
        if (user.role === 'admin') {
            isAdmin = true;
        } else {
            // Check specific permissions
            const userPermissions = await UserPermission.findOne({ user_id: user._id })
                .populate('permissions.permission');
            
            if (userPermissions) {
                isAdmin = userPermissions.permissions.some(p => 
                    p.permission && p.permission.permission_name === "dashboard"
                );
            }
        }

        // Generate token
        const token = generateToken(user, isAdmin);

        // Prepare user response (without password)
        const userResponse = user.toObject();
        delete userResponse.password;

        res.status(200).json({
            status: "SUCCESS",
            message: isAdmin ? "Admin login successful" : "User login successful",
            data: {
                user: userResponse,
                isAdmin,
                token
            }
        });

    } catch (error) {
        console.error('Signin error:', error);
        res.status(500).json({
            status: "FAILED",
            message: "An error occurred during authentication"
        });
    }
}));

// Error handling middleware
router.use((error, req, res, next) => {
    console.error('Auth router error:', error);
    res.status(500).json({
        status: "FAILED",
        message: "Internal server error"
    });
});

module.exports = router;
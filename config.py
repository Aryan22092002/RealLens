# Configuration file for AuthentiLens Backend
# Modify these settings to customize the authenticity detection

# Server Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
DEBUG_MODE = True

# Brand Database Configuration
# Add or modify brands here
BRANDS_DATABASE = {
    'Nike': {
        'keywords': ['nike', 'check', 'swoosh', 'jordan', 'air max', 'dunk'],
        'price_range': (80, 300),
        'colors': ['black', 'white', 'red', 'blue', 'gray'],
        'authenticity_markers': ['quality stitching', 'perfect logo alignment']
    },
    'Apple': {
        'keywords': ['apple', 'iphone', 'ios', 'cupertino', 'airpods', 'ipad'],
        'price_range': (800, 1300),
        'colors': ['silver', 'black', 'gold', 'space gray', 'sierra blue'],
        'authenticity_markers': ['precision manufacturing', 'consistent spacing']
    },
    'Samsung': {
        'keywords': ['samsung', 'galaxy', 'android', 'note', 's series'],
        'price_range': (700, 1200),
        'colors': ['black', 'silver', 'white', 'blue', 'gold'],
        'authenticity_markers': ['clear display', 'responsive interface']
    },
    'Gucci': {
        'keywords': ['gucci', 'gg', 'logo', 'luxury', 'monogram', 'design'],
        'price_range': (500, 5000),
        'colors': ['brown', 'black', 'gold', 'red', 'monogram'],
        'authenticity_markers': ['perfect detailing', 'premium materials']
    },
    'Louis Vuitton': {
        'keywords': ['louis vuitton', 'lv', 'monogram', 'luxury', 'trunk', 'speedy'],
        'price_range': (1000, 10000),
        'colors': ['brown', 'gold', 'cream', 'monogram', 'damier'],
        'authenticity_markers': ['precise stitching', 'quality leather']
    }
}

# Image Quality Analysis Thresholds
IMAGE_QUALITY_THRESHOLDS = {
    'min_sharpness_for_genuine': 30,      # Minimum sharpness score
    'min_saturation_for_genuine': 20,     # Minimum color saturation
    'acceptable_image_size_mb': 5         # Max file size in MB
}

# Authenticity Detection Weights
AUTHENTICITY_WEIGHTS = {
    'image_clarity': 0.35,                # How much image clarity affects result
    'color_saturation': 0.35,             # How much color saturation affects result
    'brand_found': 0.30                   # How much brand matching affects result
}

# Confidence Score Thresholds
CONFIDENCE_THRESHOLDS = {
    'genuine_min': 70,                    # Score >= 70% = Likely Genuine
    'counterfeit_max': 50,                # Score <= 50% = Likely Counterfeit
    'uncertain_range': (50, 70)           # 50-70% = Uncertain
}

# Web Search Configuration
WEB_SEARCH_CONFIG = {
    'enabled': True,
    'timeout_seconds': 10,
    'max_results': 5,
    'include_official_sites': True
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5000',
    'http://localhost:3000',
    'http://127.0.0.1:5000',
    '*'  # Allow all origins for development
]

# Upload Configuration
UPLOAD_CONFIG = {
    'upload_folder': 'uploads',
    'max_file_size_mb': 5,
    'allowed_extensions': ['jpg', 'jpeg', 'png', 'gif']
}

# Feature Extraction
FEATURE_EXTRACTION = {
    'calculate_sharpness': True,
    'calculate_saturation': True,
    'analyze_edges': False,               # Advanced feature (slower)
    'use_color_histograms': False         # Advanced feature (slower)
}

# Logging Configuration
LOGGING = {
    'enabled': True,
    'log_level': 'INFO',
    'log_file': 'authenticity_analysis.log',
    'log_api_requests': True
}

# Model Configuration (for future ML integration)
ML_MODEL = {
    'enabled': False,                     # Set to True when you add ML model
    'model_path': 'models/authenticity_detector.h5',
    'model_type': 'cnn',                  # or 'transformer', 'vit', etc.
    'input_size': (224, 224),
    'use_gpu': False
}

# Cache Configuration
CACHE = {
    'enabled': True,
    'cache_dir': '.cache',
    'ttl_seconds': 3600                   # Cache results for 1 hour
}

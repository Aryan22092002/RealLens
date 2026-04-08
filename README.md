# RealLens - Product Authenticity Detection System

> An AI-powered application that captures product images from your camera and predicts whether items are likely genuine or counterfeit using computer vision and brand authentication analysis.

## 🎯 Project Overview

RealLens is a Final Year Project that combines Flask backend, computer vision analysis, and real-time image processing to detect product authenticity. Users can capture product images directly from their webcam and receive instant analysis with confidence scores and detailed verdicts.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Web Browser)                    │
│  HTML/CSS/JavaScript - Real-time Camera Interface            │
└─────────────────────────────────────┬───────────────────────┘
                                      │
                        HTTP/REST API (POST/GET)
                                      │
┌─────────────────────────────────────▼───────────────────────┐
│                  BACKEND (Flask Server)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Routes                                          │   │
│  │  • /api/analyze       - Main analysis endpoint       │   │
│  │  • /api/search        - Brand search                 │   │
│  │  • /api/brands        - Get supported brands         │   │
│  │  • /api/health        - Health check                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ProductAnalyzer Class                               │   │
│  │  • detect_brand() - Brand recognition                │   │
│  │  • analyze_image_quality() - Quality metrics         │   │
│  │  • authenticate_product() - Authenticity scoring      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  WebSearchValidator Class                            │   │
│  │  • search_product() - Search product info            │   │
│  │  • validate_against_database() - DB validation       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Brand Database (BRANDS_DB)                          │   │
│  │  Nike, Apple, Samsung, Gucci, Louis Vuitton, etc.    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### 1. **User Interaction (Frontend)**
```
Start Camera → Camera Stream Ready
              ↓
         Capture Image
              ↓
         Send to Backend (Base64)
              ↓
         Wait for Analysis
              ↓
         Display Results
```

### 2. **Backend Analysis Pipeline**
```
┌─────────────────────────────────────────────────────┐
│ RECEIVE IMAGE (Base64 Encoded)                      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ STEP 1: BRAND DETECTION                             │
│ • Decode image from Base64                          │
│ • Analyze filename for brand keywords               │
│ • Match against BRANDS_DB                           │
│ • Return: Primary brand + confidence score          │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ STEP 2: IMAGE QUALITY ANALYSIS                      │
│ • Calculate sharpness (Laplacian variance)          │
│ • Measure color saturation                          │
│ • Return: Quality metrics (0-100 scale)             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ STEP 3: AUTHENTICATE PRODUCT                        │
│ • Evaluate image clarity factor                     │
│ • Check color saturation factor                     │
│ • Verify brand existence factor                     │
│ • Calculate authenticity score                      │
│ • Return: Status (Genuine/Uncertain/Counterfeit)   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ STEP 4: WEB SEARCH VALIDATION                       │
│ • Construct search query                            │
│ • Return mock search results (placeholder)          │
│ • Validate against brand database                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ RETURN COMPLETE ANALYSIS RESPONSE                   │
│ {                                                    │
│   timestamp, brand_detection, image_quality,        │
│   authentication, web_search, final_verdict         │
│ }                                                    │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Workflow

### User Workflow

1. **Start Application**
   - Open `http://localhost:5000` in browser
   - Click "Start Camera" button
   - Grant camera permissions

2. **Capture Product**
   - Position product in camera frame
   - Click "Capture" button
   - Image is captured and displayed

3. **Analyze Product**
   - Click "Analyze" button
   - Backend processes image (typically 1-2 seconds)
   - Results displayed with verdict and confidence

4. **Review or Recapture**
   - View authentication verdict (✅ Genuine / ⚠️ Uncertain / ❌ Counterfeit)
   - See brand detection and confidence percentages
   - Click "Recapture" to test another item
   - System returns to capture mode

---

## 🔧 Technical Components

### **Frontend** (`/static/` & `/templates/`)

| File | Purpose |
|------|---------|
| `templates/index.html` | Main web interface with video stream and buttons |
| `static/app.js` | Event handlers, camera control, API communication |
| `static/styles.css` | UI styling and responsive layout |

**Key Features:**
- Real-time camera stream using `getUserMedia()` API
- Canvas-based image capture (JPEG compression)
- Base64 image encoding for transmission
- Dynamic result display with confidence metrics

### **Backend** (`app.py`)

| Component | Responsibility |
|-----------|-----------------|
| `ProductAnalyzer` | Image analysis and authenticity scoring |
| `WebSearchValidator` | Product validation and database lookup |
| `BRANDS_DB` | Hardcoded brand database with characteristics |
| Flask Routes | REST API endpoints for frontend communication |

**Key Functions:**

- **`analyze_image_quality()`**: Calculates sharpness and saturation metrics
  - Sharpness: Laplacian variance (edge detection)
  - Saturation: Standard deviation of color channels

- **`detect_brand()`**: Identifies product brand
  - Scans filename for brand keywords
  - Matches against BRANDS_DB
  - Returns confidence scores

- **`authenticate_product()`**: Determines authenticity
  - Evaluates 3 factors: clarity, saturation, brand existence
  - Generates authenticity score (0-100)
  - Assigns status: Genuine (≥70%), Uncertain (50-70%), Counterfeit (<50%)

- **`search_product()`**: Returns brand information
  - Constructs search queries
  - Returns mock search results (expandable to real APIs)

---

## 📦 Supported Brands

Currently configured brands in database:
- **Nike**: Price range $80-300, keywords: swoosh, check, jordan
- **Apple**: Price range $800-1300, keywords: iphone, ios
- **Samsung**: Price range $700-1200, keywords: galaxy, android
- **Gucci**: Price range $500-5000, keywords: gg, logo
- **Louis Vuitton**: Price range $1000-10000, keywords: lv, monogram

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Webcam/Camera device
- Modern web browser

### Installation & Running

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start backend server
python app.py

# 3. Open in browser
# Navigate to http://localhost:5000
```

The server will display:
```
🚀 AuthentiLens Backend Server
==================================================
📍 Server running at http://0.0.0.0:5000
📍 API Documentation available at /api/health
🎯 Supported brands: Nike, Apple, Samsung, Gucci, Louis Vuitton
==================================================
```

---

## 🔌 API Reference

### POST `/api/analyze`
Analyzes a product image for authenticity.

**Request:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "filename": "nike_shoe.jpg"
}
```

**Response:**
```json
{
  "timestamp": "2026-03-10T12:30:45.123456",
  "brand_detection": {
    "primary_brand": "Nike",
    "confidence": 85,
    "alternatives": []
  },
  "image_quality": {
    "sharpness": 42.5,
    "saturation": 65.3
  },
  "authentication": {
    "status": "Likely Genuine",
    "confidence": 78,
    "factors": {
      "image_clarity": true,
      "color_saturation": true,
      "brand_found": true
    },
    "score": 77.8
  },
  "web_search": {
    "query": "Nike authentic product official specifications",
    "results": [...],
    "validated": true
  },
  "final_verdict": {
    "status": "Likely Genuine",
    "confidence": 78,
    "recommendation": "This product appears to be likely genuine. Confidence level: 78%"
  }
}
```

### GET `/api/brands`
Returns list of supported brands.

**Response:**
```json
{
  "brands": ["Nike", "Apple", "Samsung", "Gucci", "Louis Vuitton"],
  "total": 5
}
```

### GET `/api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-10T12:30:45.123456"
}
```

---

## 📁 Project Structure

```
Final Year Project/
├── app.py                          # Flask backend server
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── QUICKSTART.md                   # Quick start guide
├── BACKEND_SETUP.md                # Backend setup details
├── templates/
│   └── index.html                  # Frontend UI
├── static/
│   ├── app.js                      # Frontend JavaScript
│   └── styles.css                  # Frontend styling
├── uploads/                        # Temporary upload storage
├── scripts/
│   └── dataset_builder.py          # Dataset building utilities
└── Data/
    ├── metadata.jsonl              # Dataset metadata
    └── raw/
        ├── genuine/                # Genuine product images
        └── fake/                   # Counterfeit product images
```

---

## 🔮 Future Enhancements

- [ ] Machine learning model for improved brand detection
- [ ] Integration with real image search APIs (Google Vision, AWS Rekognition)
- [ ] Database persistence for analysis history
- [ ] Multi-image comparison analysis
- [ ] Mobile app support
- [ ] Real-time feature detection (QR codes, holograms, etc.)
- [ ] User authentication and analytics dashboard
- [ ] Barcode/Serial number verification

---

## 📄 License

This is a Final Year Project. All rights reserved.

---

## 👤 Developer Notes

- **Framework**: Flask 2.3.3
- **Image Processing**: Pillow, NumPy, SciPy
- **API Format**: JSON/REST
- **Frontend**: Vanilla JavaScript (no frameworks)
- **CORS**: Enabled for cross-origin requests

---

**Last Updated**: March 2026

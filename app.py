from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from PIL import Image
import io
import base64
import json
import os
from pathlib import Path
import requests
from datetime import datetime
import hashlib
from dotenv import load_dotenv
import numpy as np
from io import BytesIO
import urllib.parse
import re

try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
# Explicit CORS so browser preflight (OPTIONS) never gets 405 on /api/*
CORS(
    app,
    resources={r'/api/*': {'origins': '*', 'methods': ['GET', 'POST', 'OPTIONS'], 'allow_headers': ['Content-Type']}},
)
# Large JSON bodies (base64 photos)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

# Configuration
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Electronics brands: keywords for text matching only. No price/authenticity claims.
# official_hint is a well-known corporate site for user reference (not verified by RealLens).
BRANDS_DB = {
    'Apple': {
        'keywords': ['apple', 'iphone', 'ipad', 'macbook', 'airpods', 'airpod', 'imac', 'mac mini', 'mac studio', 'ios', 'magsafe'],
        'category': 'consumer_electronics',
        'official_hint': 'https://www.apple.com',
    },
    'Samsung': {
        'keywords': ['samsung', 'galaxy', 'buds', 'one ui'],
        'category': 'consumer_electronics',
        'official_hint': 'https://www.samsung.com',
    },
    'Google': {
        'keywords': ['google', 'pixel', 'nest', 'chromecast'],
        'category': 'consumer_electronics',
        'official_hint': 'https://store.google.com',
    },
    'Microsoft': {
        'keywords': ['microsoft', 'surface', 'xbox', 'windows'],
        'category': 'consumer_electronics',
        'official_hint': 'https://www.microsoft.com',
    },
    'Sony': {
        'keywords': ['sony', 'playstation', 'ps5', 'ps4', 'wh-1000', 'bravia'],
        'category': 'consumer_electronics',
        'official_hint': 'https://www.sony.com',
    },
    'Dell': {
        'keywords': ['dell', 'alienware', 'xps', 'latitude', 'inspiron'],
        'category': 'computing',
        'official_hint': 'https://www.dell.com',
    },
    'HP': {
        'keywords': ['hp', 'hewlett', 'omen', 'pavilion', 'spectre', 'envy'],
        'category': 'computing',
        'official_hint': 'https://www.hp.com',
    },
    'Lenovo': {
        'keywords': ['lenovo', 'thinkpad', 'ideapad', 'legion', 'yoga'],
        'category': 'computing',
        'official_hint': 'https://www.lenovo.com',
    },
    'Asus': {
        'keywords': ['asus', 'rog', 'zenbook', 'vivobook', 'tuf'],
        'category': 'computing',
        'official_hint': 'https://www.asus.com',
    },
    'Acer': {
        'keywords': ['acer', 'predator', 'swift', 'nitro'],
        'category': 'computing',
        'official_hint': 'https://www.acer.com',
    },
    'MSI': {
        'keywords': ['msi'],
        'category': 'computing',
        'official_hint': 'https://www.msi.com',
    },
    'LG': {
        'keywords': ['lg', 'gram', 'oled', 'webos'],
        'category': 'consumer_electronics',
        'official_hint': 'https://www.lg.com',
    },
    'OnePlus': {
        'keywords': ['oneplus', 'one plus'],
        'category': 'mobile',
        'official_hint': 'https://www.oneplus.com',
    },
    'Xiaomi': {
        'keywords': ['xiaomi', 'redmi', 'poco', 'mi phone', 'mijia'],
        'category': 'consumer_electronics',
        'official_hint': 'https://www.mi.com',
    },
    'Huawei': {
        'keywords': ['huawei', 'honor'],
        'category': 'consumer_electronics',
        'official_hint': 'https://consumer.huawei.com',
    },
    'Meta': {
        'keywords': ['meta', 'oculus', 'quest'],
        'category': 'vr',
        'official_hint': 'https://www.meta.com',
    },
    'Nintendo': {
        'keywords': ['nintendo', 'switch'],
        'category': 'gaming',
        'official_hint': 'https://www.nintendo.com',
    },
    'Valve': {
        'keywords': ['valve', 'steam deck', 'steamdeck'],
        'category': 'gaming',
        'official_hint': 'https://www.steamdeck.com',
    },
    'DJI': {
        'keywords': ['dji', 'mavic', 'mini 3', 'air 3'],
        'category': 'drones_cameras',
        'official_hint': 'https://www.dji.com',
    },
    'GoPro': {
        'keywords': ['gopro', 'hero 12', 'hero 11'],
        'category': 'cameras',
        'official_hint': 'https://gopro.com',
    },
    'Canon': {
        'keywords': ['canon', 'eos ', 'powershot'],
        'category': 'cameras',
        'official_hint': 'https://www.canon.com',
    },
    'Nikon': {
        'keywords': ['nikon', 'coolpix', 'z6', 'z7', 'z8', 'z9'],
        'category': 'cameras',
        'official_hint': 'https://www.nikon.com',
    },
    'Bose': {
        'keywords': ['bose', 'quietcomfort', 'qc45', 'qc35'],
        'category': 'audio',
        'official_hint': 'https://www.bose.com',
    },
    'JBL': {
        'keywords': ['jbl'],
        'category': 'audio',
        'official_hint': 'https://www.jbl.com',
    },
    'Anker': {
        'keywords': ['anker', 'eufy', 'soundcore'],
        'category': 'accessories',
        'official_hint': 'https://www.anker.com',
    },
    'Logitech': {
        'keywords': ['logitech', 'mx master', 'g502', 'g pro'],
        'category': 'peripherals',
        'official_hint': 'https://www.logitech.com',
    },
    'Razer': {
        'keywords': ['razer', 'blade', 'deathadder', 'blackwidow'],
        'category': 'peripherals',
        'official_hint': 'https://www.razer.com',
    },
    'Corsair': {
        'keywords': ['corsair', 'k70', 'k95', 'vengeance'],
        'category': 'peripherals',
        'official_hint': 'https://www.corsair.com',
    },
    'Intel': {
        'keywords': ['intel', 'core i', 'xeon', 'celeron', 'pentium', 'arc gpu'],
        'category': 'components',
        'official_hint': 'https://www.intel.com',
    },
    'AMD': {
        'keywords': ['amd', 'ryzen', 'radeon', 'threadripper', 'epyc'],
        'category': 'components',
        'official_hint': 'https://www.amd.com',
    },
    'NVIDIA': {
        'keywords': ['nvidia', 'geforce', 'rtx', 'quadro'],
        'category': 'components',
        'official_hint': 'https://www.nvidia.com',
    },
    'Qualcomm': {
        'keywords': ['qualcomm', 'snapdragon'],
        'category': 'components',
        'official_hint': 'https://www.qualcomm.com',
    },
    'Garmin': {
        'keywords': ['garmin', 'fenix', 'forerunner'],
        'category': 'wearables',
        'official_hint': 'https://www.garmin.com',
    },
    'Fitbit': {
        'keywords': ['fitbit'],
        'category': 'wearables',
        'official_hint': 'https://www.fitbit.com',
    },
    'Amazon': {
        'keywords': ['amazon echo', 'echo dot', 'echo show', 'fire tv', 'fire tablet', 'kindle'],
        'category': 'consumer_electronics',
        'official_hint': 'https://www.amazon.com',
    },
    'Nothing': {
        'keywords': ['nothing phone', 'nothing ear'],
        'category': 'mobile',
        'official_hint': 'https://nothing.tech',
    },
    'Fairphone': {
        'keywords': ['fairphone'],
        'category': 'mobile',
        'official_hint': 'https://fairphone.com',
    },
    'Motorola': {
        'keywords': ['motorola', 'moto g', 'moto edge', 'razr'],
        'category': 'mobile',
        'official_hint': 'https://www.motorola.com',
    },
    'Nokia': {
        'keywords': ['nokia', 'hmd'],
        'category': 'mobile',
        'official_hint': 'https://www.nokia.com',
    },
    'Oppo': {
        'keywords': ['oppo', 'find x', 'reno'],
        'category': 'mobile',
        'official_hint': 'https://www.oppo.com',
    },
    'Vivo': {
        'keywords': ['vivo', 'iqoo'],
        'category': 'mobile',
        'official_hint': 'https://www.vivo.com',
    },
    'Realme': {
        'keywords': ['realme'],
        'category': 'mobile',
        'official_hint': 'https://www.realme.com',
    },
    'Panasonic': {
        'keywords': ['panasonic', 'lumix'],
        'category': 'electronics',
        'official_hint': 'https://www.panasonic.com',
    },
    'Philips': {
        'keywords': ['philips', 'hue'],
        'category': 'electronics',
        'official_hint': 'https://www.philips.com',
    },
    'Netgear': {
        'keywords': ['netgear', 'nighthawk', 'orbi'],
        'category': 'networking',
        'official_hint': 'https://www.netgear.com',
    },
    'TP-Link': {
        'keywords': ['tp-link', 'tplink', 'deco', 'archer'],
        'category': 'networking',
        'official_hint': 'https://www.tp-link.com',
    },
    'Ubiquiti': {
        'keywords': ['ubiquiti', 'unifi', 'ubnt'],
        'category': 'networking',
        'official_hint': 'https://www.ui.com',
    },
}

HTTP_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 RealLens/1.0'
    ),
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
}


def match_brand_from_product_text(text):
    if not text:
        return None
    tl = text.lower()
    for brand, info in BRANDS_DB.items():
        for kw in info['keywords']:
            if kw in tl:
                return brand
    return None


# Product name must clearly refer to an electronic device (keep in sync with static/app.js).
ELECTRONICS_PHRASES = (
    'macbook', 'iphone', 'ipad', 'airpods', 'air pods', 'apple watch',
    'galaxy s', 'galaxy z', 'galaxy tab', 'galaxy bud', 'galaxy watch',
    'google pixel', 'surface pro', 'surface laptop', 'surface book', 'surface go',
    'playstation', 'ps5', 'ps4', 'ps vr', 'xbox', 'xbox series',
    'nintendo switch', 'steam deck', 'steamdeck',
    'meta quest', 'oculus quest',
    'smart tv', 'android tv', 'fire tv', 'apple tv',
    'mechanical keyboard', 'gaming laptop', 'gaming mouse', 'gaming headset', 'gaming pc',
    'wireless charger', 'fast charger', 'power bank', 'powerbank',
    'bluetooth speaker', 'smart speaker', 'sound bar', 'soundbar',
    'graphics card', 'video card', 'wireless earbuds',
    'vr headset', 'noise cancelling', 'noise-canceling', 'smart watch', 'smartwatch',
    'robot vacuum', 'roomba',
)

ELECTRONICS_TOKENS = frozenset(
    """
    iphone ipad ipod imac macbook macmini macstudio macpro airpods airpod
    galaxy pixel oneplus xiaomi redmi poco oppo vivo realme fairphone nothing
    smartphone android handheld
    laptop chromebook notebook ultrabook thinkpad ideapad zenbook vivobook
    legion alienware surface inspiron pavilion xps spectre envy omen blade
    tablet kindle ereader e-reader
    earbuds earphones headphones headset earbud
    smartwatch fitbit garmin whoop
    playstation psvr ps4 ps5 xbox nintendo switch steamdeck
    nvidia geforce radeon rtx rx580 rx6700 ryzen threadripper epyc
    intel celeron pentium xeon snapdragon exynos bionic tensor
    m1 m2 m3 m4 a14 a15 a16 a17 a18
    gpu ssd nvme hdd motherboard
    router modem mesh eero ubiquiti tplink netgear orbi
    keyboard mouse webcam trackpad touchpad
    monitor ultrawide oled qled mini-led
    dslr mirrorless gopro insta360 dji mavic drone
    charger powerbank anker belkin logitech razer corsair steelseries hyperx
    beats bose jabra sennheiser shure
    dell asus acer msi lenovo hp samsung apple google microsoft sony lg
    huawei motorola nokia blackberry
    oculus quest echo dot firestick chromecast roku appletv homepod nest
    soundbar subwoofer amplifier dac
    """.split()
)


def is_electronics_product_name(name: str) -> bool:
    if not name or not name.strip():
        return False
    lowered = name.lower()
    for phrase in ELECTRONICS_PHRASES:
        if phrase in lowered:
            return True
    tokens = set(re.findall(r'[a-z0-9]+', lowered))
    if not tokens.isdisjoint(ELECTRONICS_TOKENS):
        return True
    if re.search(r'\btv\b', lowered):
        return True
    return False


class ReferenceImageFetcher:
    """Fetches reference product images (Google Custom Search if configured, else DuckDuckGo)."""

    @staticmethod
    def google_image_links(query, max_results):
        key = os.getenv('GOOGLE_API_KEY')
        cx = os.getenv('GOOGLE_CSE_ID')
        if not key or not cx:
            return []
        out = []
        try:
            params = {
                'key': key,
                'cx': cx,
                'q': query,
                'searchType': 'image',
                'num': min(10, max_results),
                'safe': 'active',
            }
            r = requests.get(
                'https://www.googleapis.com/customsearch/v1',
                params=params,
                timeout=15,
            )
            r.raise_for_status()
            for item in (r.json().get('items') or []):
                link = item.get('link')
                if link:
                    out.append(link)
        except Exception:
            pass
        return out[:max_results]

    @staticmethod
    def duckduckgo_image_links(query, max_results):
        try:
            from duckduckgo_search import DDGS

            out = []
            with DDGS() as ddgs:
                for row in ddgs.images(query, max_results=max_results):
                    u = row.get('image') or row.get('thumbnail')
                    if u:
                        out.append(u)
            return out
        except Exception:
            return []

    @classmethod
    def fetch(cls, product_name, max_results=8):
        query = f"{product_name} official authentic product"
        urls = []
        seen = set()
        for u in cls.google_image_links(query, max_results):
            if u not in seen:
                seen.add(u)
                urls.append(u)
        need = max_results - len(urls)
        if need > 0:
            for u in cls.duckduckgo_image_links(query, need + 6):
                if u not in seen:
                    seen.add(u)
                    urls.append(u)
                if len(urls) >= max_results:
                    break
        return urls[:max_results]


class ProductEncyclopedia:
    """Short encyclopedia-style info (Wikipedia) for the product name."""

    @staticmethod
    def wikipedia_summary_for_query(query):
        if not query or not query.strip():
            return None
        try:
            r = requests.get(
                'https://en.wikipedia.org/w/api.php',
                params={
                    'action': 'opensearch',
                    'search': query.strip(),
                    'limit': 1,
                    'namespace': 0,
                    'format': 'json',
                },
                headers=HTTP_HEADERS,
                timeout=12,
            )
            r.raise_for_status()
            data = r.json()
            titles = data[1] if len(data) > 1 else []
            if not titles:
                return None
            title = titles[0]
            enc = urllib.parse.quote(title.replace(' ', '_'), safe='')
            r2 = requests.get(
                f'https://en.wikipedia.org/api/rest_v1/page/summary/{enc}',
                headers=HTTP_HEADERS,
                timeout=12,
            )
            if r2.status_code != 200:
                return {
                    'title': title,
                    'extract': None,
                    'page_url': f'https://en.wikipedia.org/wiki/{enc}',
                    'thumbnail': None,
                }
            j = r2.json()
            thumb = (j.get('thumbnail') or {}).get('source')
            page_url = (j.get('content_urls') or {}).get('desktop', {}).get('page')
            return {
                'title': j.get('title', title),
                'extract': j.get('extract'),
                'page_url': page_url or f'https://en.wikipedia.org/wiki/{enc}',
                'thumbnail': thumb,
            }
        except Exception:
            return None


class VisualMatcher:
    """Perceptual-hash similarity between user photo and reference images."""

    @staticmethod
    def download_rgb(url):
        r = requests.get(url, headers=HTTP_HEADERS, timeout=12)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert('RGB')
        return img

    @classmethod
    def compare_to_references(cls, user_image, ref_urls):
        if not HAS_IMAGEHASH or not ref_urls:
            return None, []
        user_rgb = user_image.convert('RGB')
        try:
            u_hash = imagehash.phash(user_rgb)
        except Exception:
            return None, []
        details = []
        best = 0.0
        for url in ref_urls:
            entry = {'url': url, 'similarity_percent': None}
            try:
                ref = cls.download_rgb(url)
                r_hash = imagehash.phash(ref)
                dist = u_hash - r_hash
                sim = max(0.0, 100.0 - (dist / 64.0) * 100.0)
                entry['similarity_percent'] = round(sim, 1)
                best = max(best, sim)
            except Exception as ex:
                entry['error'] = str(ex)[:160]
            details.append(entry)
        return round(best, 1), details


class ProductAnalyzer:
    """Analyzes product images for brand recognition and authenticity"""
    
    @staticmethod
    def analyze_image_quality(image):
        """Analyze image quality metrics"""
        img_array = np.array(image)
        
        # Calculate image sharpness
        if len(img_array.shape) == 3:
            gray = np.sum(img_array, axis=2) / 3
        else:
            gray = img_array
        
        # Laplacian variance (sharpness metric)
        try:
            from scipy import ndimage
            laplacian = ndimage.laplace(gray)
            sharpness = np.var(laplacian)
        except:
            sharpness = 50  # Default if scipy not available
        
        # Color vibrancy
        img_array = img_array.astype(float)
        saturation = np.std(img_array)
        
        return {
            'sharpness': float(sharpness),
            'saturation': float(saturation)
        }
    
    @staticmethod
    def detect_brand(image, image_name=''):
        """Match brand from filename / product text using reference keywords only."""
        detected_brands = []
        
        # Check filename for brand hints
        name_lower = image_name.lower()
        for brand, info in BRANDS_DB.items():
            score = 0
            for keyword in info['keywords']:
                if keyword in name_lower:
                    score += 30
            
            if score > 0:
                detected_brands.append({
                    'brand': brand,
                    'confidence': min(80, 30 + score)
                })
        
        # If no brand detected from name, use image quality analysis
        if not detected_brands:
            detected_brands = [{'brand': 'Electronics (no brand keyword in filename)', 'confidence': 25}]
        
        return sorted(detected_brands, key=lambda x: x['confidence'], reverse=True)
    
    @staticmethod
    def authenticate_product(brand, image_quality, visual_similarity_percent=None, user_named_product=False):
        """
        Determine product authenticity based on brand, quality metrics, and optional
        similarity to reference images from the web.
        """
        brand_info = BRANDS_DB.get(brand, {})

        factors = {
            'image_clarity': image_quality['sharpness'] > 30,
            'color_saturation': image_quality['saturation'] > 20,
            'brand_found': len(brand_info) > 0 or user_named_product,
        }

        positive_factors = sum(1 for v in factors.values() if v)
        base_score = (positive_factors / len(factors)) * 100

        if visual_similarity_percent is not None:
            authenticity_score = 0.35 * base_score + 0.65 * float(visual_similarity_percent)
            factors['reference_visual_similarity_ok'] = visual_similarity_percent >= 55
        else:
            authenticity_score = base_score

        if authenticity_score >= 70:
            status = 'Likely Genuine'
            confidence = int(round(authenticity_score))
        elif authenticity_score >= 50:
            status = 'Uncertain'
            confidence = int(round(authenticity_score))
        else:
            status = 'Likely Counterfeit'
            confidence = int(round(100 - authenticity_score))

        confidence = min(99, max(1, confidence))

        return {
            'status': status,
            'confidence': confidence,
            'factors': factors,
            'score': float(authenticity_score),
            'visual_similarity_percent': visual_similarity_percent,
        }

class WebSearchValidator:
    """Validates product authenticity using web search"""
    
    @staticmethod
    def search_product(brand, product_type='product'):
        """
        Search the web for product information
        Uses free search APIs for demo purposes
        """
        search_results = []
        
        try:
            # Construct search query
            query = f"{brand} {product_type} specifications"
            info = BRANDS_DB.get(brand, {})
            hint = info.get('official_hint', '')
            search_results = [
                {
                    'title': 'Counterfeit electronics (general guidance)',
                    'url': 'https://en.wikipedia.org/wiki/Counterfeit_consumer_goods',
                    'snippet': (
                        'Buying from authorized retailers and comparing packaging/serial numbers '
                        'reduces risk. RealLens scores are indicative only, not legal proof.'
                    ),
                    'relevance': 'educational',
                },
            ]
            if hint:
                search_results.append({
                    'title': f'Possible official site for {brand} (verify in browser)',
                    'url': hint,
                    'snippet': 'Use only to compare product info; RealLens does not verify this link for your region.',
                    'relevance': 'reference',
                })
            
            return {
                'query': query,
                'results': search_results,
                'success': True
            }
        except Exception as e:
            return {
                'query': '',
                'results': [],
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def validate_against_database(brand, features):
        """Validate product features against brand database"""
        brand_info = BRANDS_DB.get(brand, {})
        
        if not brand_info:
            return {
                'found': False,
                'validation': 'Brand not in on-device electronics reference list (text only).',
            }

        return {
            'found': True,
            'brand_info': {
                'category': brand_info.get('category'),
                'official_hint': brand_info.get('official_hint'),
            },
            'validation': (
                f'Brand keyword matched the RealLens electronics reference list. '
                f'This is not proof the item is genuine.'
            ),
        }

def infer_brand_label(product_name: str) -> str:
    """Best-effort brand from product text (Apple / Samsung / DB keywords)."""
    if not product_name or not product_name.strip():
        return 'Unknown'
    m = match_brand_from_product_text(product_name)
    if m:
        return m
    low = product_name.lower()
    apple_hints = (
        'iphone', 'ipad', 'macbook', 'airpods', 'airpod', 'apple watch', 'imac',
        'mac mini', 'mac studio', 'homepod', 'airtag',
    )
    if any(h in low for h in apple_hints) or low.strip().startswith('apple '):
        return 'Apple'
    sam_hints = ('galaxy', 'samsung', 'z fold', 'z flip', 'buds2', 'buds fe')
    if any(h in low for h in sam_hints):
        return 'Samsung'
    return 'Unknown'


def build_text_only_insight(product_name: str):
    """
    Wikipedia + web-style hints without using the user's photo.
    Used when image analysis is skipped or impossible.
    """
    name = (product_name or '').strip() or 'Electronic device'
    brand = infer_brand_label(name)
    brand_for_search = brand if brand != 'Unknown' else (name.split()[0] if name.split() else 'Device')

    wiki = ProductEncyclopedia.wikipedia_summary_for_query(name)
    if wiki is None:
        product_info = {
            'title': name,
            'extract': None,
            'page_url': None,
            'thumbnail': None,
        }
    else:
        product_info = wiki

    search_results = WebSearchValidator.search_product(brand_for_search, product_type=name[:120])
    db_brand = brand if brand in BRANDS_DB else None
    if db_brand:
        db_validation = WebSearchValidator.validate_against_database(db_brand, {})
    else:
        db_validation = {'found': False, 'validation': 'Brand not in on-device reference list.'}

    return {
        'product_info': product_info,
        'web_search': {
            'query': search_results.get('query', ''),
            'results': search_results.get('results', []),
            'validated': db_validation.get('found', False),
        },
        'primary_brand': brand,
        'brand_confidence': 50 if brand == 'Unknown' else 55,
    }


def _fallback_analyze_response(product_name: str, reason: str):
    """
    Neutral 50% payload when the image cannot be analyzed.
    Still fills product info + web search (same style as a full run, without image matching).
    """
    name = (product_name or 'Device').strip() or 'Device'
    insight = build_text_only_insight(name)
    brand = insight['primary_brand']

    return {
        'timestamp': datetime.now().isoformat(),
        'degraded': True,
        'degraded_reason': reason,
        'brand_detection': {
            'product_name': name,
            'primary_brand': brand if brand != 'Unknown' else name,
            'confidence': insight['brand_confidence'],
            'alternatives': [],
        },
        'image_quality': {'sharpness': 50.0, 'saturation': 50.0},
        'authentication': {
            'status': 'Uncertain',
            'confidence': 50,
            'factors': {},
            'score': 50.0,
            'visual_similarity_percent': None,
        },
        'reference_match': {
            'image_matching_skipped': True,
            'query': '',
            'reference_image_urls': [],
            'per_reference': [],
            'best_visual_similarity_percent': None,
            'method': None,
            'note': (
                f'Photo could not be used for comparison ({reason}). '
                f'Below: the same Wikipedia and reference links we show for a named product — without pHash matching.'
            ),
        },
        'product_info': insight['product_info'],
        'web_search': insight['web_search'],
        'final_verdict': {
            'status': 'Uncertain',
            'confidence': 50,
            'recommendation': (
                'Image analysis unavailable — neutral score 50%. '
                'Use the links and summary below; buy only from authorized sellers when possible.'
            ),
        },
    }


# Routes
@app.route('/')
def index():
    """Serve the main application"""
    return render_template('index.html')


@app.route('/api/product-context', methods=['GET', 'OPTIONS'])
def product_context():
    """Wikipedia + web-search hints for a product name (no image). For offline UI enrichment."""
    if request.method == 'OPTIONS':
        return '', 204
    name = (request.args.get('product_name') or '').strip() or 'Electronic device'
    insight = build_text_only_insight(name)
    brand = insight['primary_brand']
    return jsonify({
        'product_info': insight['product_info'],
        'web_search': insight['web_search'],
        'brand_detection': {
            'product_name': name,
            'primary_brand': brand if brand != 'Unknown' else name,
            'confidence': insight['brand_confidence'],
            'alternatives': [],
        },
    }), 200


@app.route('/api/analyze', methods=['POST', 'OPTIONS', 'GET'])
def analyze_product():
    """
    Main API endpoint for product analysis.
    Expects: image (base64), product_name (string) — reference images are fetched from the web
    and compared to the user's photo (perceptual hash). Wikipedia summary is included when found.
    """
    if request.method == 'OPTIONS':
        return '', 204
    if request.method == 'GET':
        return jsonify({
            'ok': True,
            'hint': 'Send POST with JSON: { "image": "<base64 or data URL>", "product_name": "..." }',
        }), 200

    try:
        data = request.get_json(force=True, silent=True)
        if data is None:
            try:
                raw = request.get_data(as_text=True)
                data = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                data = None
        if not isinstance(data, dict):
            return jsonify(_fallback_analyze_response('', 'Invalid JSON body.')), 200

        product_name = (data.get('product_name') or '').strip()

        if 'image' not in data or data.get('image') in (None, ''):
            return jsonify(_fallback_analyze_response(product_name, 'No image in request.')), 200

        if not product_name:
            product_name = 'Electronic device'

        if not is_electronics_product_name(product_name):
            return jsonify(_fallback_analyze_response(
                product_name,
                'Name does not look like a typical electronics product; neutral score applied.',
            )), 200

        raw_image = data['image']
        if isinstance(raw_image, str) and ',' in raw_image:
            image_data = raw_image.split(',', 1)[1]
        else:
            image_data = raw_image
        if not isinstance(image_data, str):
            return jsonify(_fallback_analyze_response(product_name, 'Image must be base64 text.')), 200
        image_data = image_data.strip()
        try:
            image_bytes = base64.b64decode(image_data, validate=True)
        except Exception:
            try:
                image_bytes = base64.b64decode(image_data, validate=False)
            except Exception:
                return jsonify(_fallback_analyze_response(product_name, 'Could not decode base64 image.')), 200
        if not image_bytes:
            return jsonify(_fallback_analyze_response(product_name, 'Empty image after decode.')), 200
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.load()
        except Exception:
            return jsonify(_fallback_analyze_response(product_name, 'Could not open image bytes.')), 200

        image_name = data.get('filename', '') or product_name

        matched_brand = match_brand_from_product_text(product_name)
        detected_brands = ProductAnalyzer.detect_brand(image, image_name)

        if matched_brand:
            primary_brand = matched_brand
            brand_confidence = 88
            alts = [{'brand': matched_brand, 'confidence': brand_confidence}]
            for row in detected_brands:
                if row['brand'] != matched_brand:
                    alts.append(row)
            alternatives = alts[1:4]
        else:
            primary_brand = detected_brands[0]['brand'] if detected_brands else product_name
            brand_confidence = detected_brands[0]['confidence'] if detected_brands else 42
            alternatives = detected_brands[1:3] if len(detected_brands) > 1 else []

        image_quality = ProductAnalyzer.analyze_image_quality(image)

        ref_urls = ReferenceImageFetcher.fetch(product_name, max_results=8)
        best_visual, visual_details = VisualMatcher.compare_to_references(image, ref_urls)

        authentication = ProductAnalyzer.authenticate_product(
            primary_brand,
            image_quality,
            visual_similarity_percent=best_visual,
            user_named_product=True,
        )

        search_results = WebSearchValidator.search_product(primary_brand, product_type=product_name[:120])
        db_validation = WebSearchValidator.validate_against_database(primary_brand, {})
        wiki = ProductEncyclopedia.wikipedia_summary_for_query(product_name)

        if wiki is None:
            product_info = {
                'title': product_name,
                'extract': None,
                'page_url': None,
                'thumbnail': None,
            }
        else:
            product_info = wiki

        vis_note = (
            'Compared your photo to online reference images using perceptual hashing (pHash). '
            'Similar lighting and angle improve match scores; this is indicative only.'
        )
        if best_visual is None and ref_urls:
            vis_note += ' Could not compute similarity (install ImageHash or unreachable images).'
        elif best_visual is None and not ref_urls:
            vis_note = (
                'No reference images were retrieved. Set GOOGLE_API_KEY + GOOGLE_CSE_ID for image search, '
                'or check network access for DuckDuckGo image results.'
            )

        response = {
            'timestamp': datetime.now().isoformat(),
            'brand_detection': {
                'product_name': product_name,
                'primary_brand': primary_brand,
                'confidence': brand_confidence,
                'alternatives': alternatives,
            },
            'image_quality': image_quality,
            'authentication': authentication,
            'reference_match': {
                'query': f"{product_name} official authentic product",
                'reference_image_urls': ref_urls,
                'per_reference': visual_details,
                'best_visual_similarity_percent': best_visual,
                'method': 'perceptual_hash_phash' if HAS_IMAGEHASH else None,
                'note': vis_note,
            },
            'product_info': product_info,
            'web_search': {
                'query': search_results.get('query', ''),
                'results': search_results.get('results', []),
                'validated': db_validation['found'],
            },
            'final_verdict': {
                'status': authentication['status'],
                'confidence': authentication['confidence'],
                'recommendation': (
                    f"This product appears to be {authentication['status'].lower()}. "
                    f"Confidence level: {authentication['confidence']}%"
                ),
            },
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify(_fallback_analyze_response('', f'Server error: {e!s}')), 200

@app.route('/api/search/<brand>', methods=['GET'])
def search_brand(brand):
    """Search web for brand information"""
    try:
        results = WebSearchValidator.search_product(brand)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/brands', methods=['GET'])
def get_brands():
    """Get list of supported brands"""
    return jsonify({
        'brands': list(BRANDS_DB.keys()),
        'total': len(BRANDS_DB)
    }), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == "__main__":
    print(" RealLens Backend Server")
    print("=" * 50)
    print(f" Server running at http://0.0.0.0:5000")
    print(f" API Documentation available at /api/health")
    print(f" Supported brands: {', '.join(BRANDS_DB.keys())}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
import time
import re
import json
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import arabic_reshaper
from bidi.algorithm import get_display
from urllib.parse import urljoin, quote
from deep_translator import GoogleTranslator

# -------------------- Basic translation settings --------------------
TRANSLATION_DICT = {
    # Fuel types
    'كهرباء': 'Electric',
    'هايبرد': 'Hybrid',
    'بنزين': 'Petrol',
    'ديزل': 'Diesel',
    # Car condition
    'جديد (زيرو)': 'New (Zero)',
    'مستعمل': 'Used',
    # Seller type
    'شخصي': 'Private',
    'معرض': 'Dealer',
    'وكالة': 'Agency',
    'معرض/وكالة': 'Dealer/Agency',
    # Insurance
    'لا يوجد تأمين': 'No Insurance',
    'يوجد تأمين': 'Insured',
    'تأمين شامل': 'Comprehensive Insurance',
    'تأمين إلزامي': 'Mandatory Insurance',
    'مكفولة': 'Warranty Included',
    # Cities
    'عمان': 'Amman',
    'الزرقاء': 'Zarqa',
    'إربد': 'Irbid',
    'البلقاء': 'Balqa',
    'المفرق': 'Mafraq',
    'جرش': 'Jerash',
    'مادبا': 'Madaba',
    'الكرك': 'Karak',
    'الطفيلة': 'Tafila',
    'معان': 'Ma\'an',
    'العقبة': 'Aqaba',
    'عجلون': 'Ajloun',
    'المنطقة الحرة': 'Free Zone',
    # Transmission
    'اوتوماتيك': 'Automatic',
    'يدوي': 'Manual',
    'اتوماتيك': 'Automatic',
    # Colors
    'أبيض': 'White',
    'أسود': 'Black',
    'رمادي': 'Gray',
    'فضي': 'Silver',
    'أزرق': 'Blue',
    'أحمر': 'Red',
    'أخضر': 'Green',
    'بني': 'Brown',
    'بيج': 'Beige',
    'ذهبي': 'Gold',
    'أزرق فاتح': 'Light Blue',
    # Default values
    'غير محدد': 'Not Specified',
    'غير متوفر': 'N/A',
    'نعم': 'Yes',
    'لا': 'No',
}

# -------------------- Comprehensive brand and model dictionaries --------------------
BRAND_TRANSLATION = {
    # Japanese brands
    'تويوتا': 'Toyota',
    'هوندا': 'Honda',
    'نيسان': 'Nissan',
    'ميتسوبيشي': 'Mitsubishi',
    'مازدا': 'Mazda',
    'كيا': 'Kia',
    'هيونداي': 'Hyundai',
    'سوبارو': 'Subaru',
    'سوزوكي': 'Suzuki',
    'ديهاتسو': 'Daihatsu',
    'ايسوزو': 'Isuzu',
    'لكزس': 'Lexus',
    'انفينيتي': 'Infiniti',
    # German brands
    'مرسيدس': 'Mercedes-Benz',
    'بي ام دبليو': 'BMW',
    'أودي': 'Audi',
    'فولكس فاجن': 'Volkswagen',
    'بورش': 'Porsche',
    'أوبل': 'Opel',
    # American brands
    'فورد': 'Ford',
    'شيفروليه': 'Chevrolet',
    'جيب': 'Jeep',
    'كاديلاك': 'Cadillac',
    'كرايسلر': 'Chrysler',
    'دودج': 'Dodge',
    'رام': 'Ram',
    'جمس': 'GMC',
    'لينكولن': 'Lincoln',
    # British brands
    'رنج روفر': 'Range Rover',
    'لاند روفر': 'Land Rover',
    'جاغوار': 'Jaguar',
    'ميني': 'Mini',
    'بنتلي': 'Bentley',
    'رولز رويس': 'Rolls-Royce',
    'استون مارتن': 'Aston Martin',
    'ماكلارين': 'McLaren',
    # Italian brands
    'فيات': 'Fiat',
    'ألفا روميو': 'Alfa Romeo',
    'مازيراتي': 'Maserati',
    'لوتس': 'Lotus',
    'لامبورغيني': 'Lamborghini',
    'فيراري': 'Ferrari',
    # French brands
    'رينو': 'Renault',
    'بيجو': 'Peugeot',
    'سيتروين': 'Citroën',
    'داسيا': 'Dacia',
    # Chinese brands
    'بي واي دي': 'BYD',
    'ام جي': 'MG',
    'جاك': 'JAC',
    'هافال': 'Haval',
    'شانجان': 'Changan',
    'جيلي': 'Geely',
    'شيري': 'Chery',
    'نيتا': 'Neta',
    'بروتون': 'Proton',
    # Other brands
    'تيسلا': 'Tesla',
    'فولفو': 'Volvo',
}

MODEL_TRANSLATION = {
    # Toyota
    'كامري': 'Camry',
    'كورولا': 'Corolla',
    'يارس': 'Yaris',
    'راف فور': 'RAV4',
    'هيلوكس': 'Hilux',
    'لاند كروزر': 'Land Cruiser',
    'برادو': 'Prado',
    'افالون': 'Avalon',
    'سوبرا': 'Supra',
    # Honda
    'سيفيك': 'Civic',
    'اكورد': 'Accord',
    'سي ار في': 'CR-V',
    'اتش ار في': 'HR-V',
    'بايلوت': 'Pilot',
    # Nissan
    'سنترا': 'Sentra',
    'التيما': 'Altima',
    'ماكسيما': 'Maxima',
    'باترول': 'Patrol',
    'قشقاي': 'Qashqai',
    # Hyundai
    'سوناتا': 'Sonata',
    'النترا': 'Elantra',
    'افانتي': 'Elantra',
    'اكسنت': 'Accent',
    'توسان': 'Tucson',
    'سانتافي': 'Santa Fe',
    'ازيرا': 'Azera',
    # Kia
    'سبورتاج': 'Sportage',
    'سورينتو': 'Sorento',
    'اوبتيما': 'Optima',
    'كادينزا': 'Cadenza',
    'ريو': 'Rio',
    'سول': 'Soul',
    # Mercedes
    'الفئة-سي': 'C-Class',
    'الفئة-اي': 'E-Class',
    'الفئة-اس': 'S-Class',
    'جي ال اي': 'GLE',
    'جي ال سي': 'GLC',
    'ايه ام جي': 'AMG',
    # BMW
    'الفئة الثالثة': '3 Series',
    'الفئة الخامسة': '5 Series',
    'الفئة السابعة': '7 Series',
    'اكس 1': 'X1',
    'اكس 3': 'X3',
    'اكس 5': 'X5',
    # Audi
    'ايه 3': 'A3',
    'ايه 4': 'A4',
    'ايه 6': 'A6',
    'ايه 8': 'A8',
    'كيو 2': 'Q2',
    'كيو 3': 'Q3',
    'كيو 5': 'Q5',
    'كيو 7': 'Q7',
    # Ford
    'فوكس': 'Focus',
    'فيوجن': 'Fusion',
    'موستانج': 'Mustang',
    'اف-150': 'F-150',
    'اكسبلورر': 'Explorer',
    # Chevrolet
    'ماليبو': 'Malibu',
    'كامارو': 'Camaro',
    'كورفيت': 'Corvette',
    'سيلفرادو': 'Silverado',
    'تاهو': 'Tahoe',
    # Tesla
    'موديل 3': 'Model 3',
    'موديل اس': 'Model S',
    'موديل اكس': 'Model X',
    'موديل واي': 'Model Y',
    # Other common models
    'باناميرا': 'Panamera',
    'كايين': 'Cayenne',
    'ماكان': 'Macan',
    'جولف': 'Golf',
    'باسات': 'Passat',
    'لوجان': 'Logan',
    'داستر': 'Duster',
    'سانديرو': 'Sandero',
}

# Trim keywords
TRIM_KEYWORDS = {
    'Standard': ['standard', 'base', 'اساسي', 'قياسي'],
    'Sport': ['sport', 'spt', 'رياضي'],
    'Luxury': ['luxury', 'lux', 'فاخر'],
    'Premium': ['premium', 'بريميوم'],
    'Limited': ['limited', 'ليمتد', 'محدود'],
    'Platinum': ['platinum', 'بلاتينيوم'],
    'Titanium': ['titanium', 'تيتانيوم'],
    'SEL': ['sel'],
    'SE': ['se'],
    'LE': ['le'],
    'XLE': ['xle'],
    'XE': ['xe'],
    'GT': ['gt'],
    'GTE': ['gte'],
    'Plus': ['plus', 'بلس'],
    'Pro': ['pro', 'برو'],
}

# List of brands for model extraction
CAR_BRANDS = list(BRAND_TRANSLATION.keys())

# -------------------- Smart model translation functions --------------------
def search_car_model_online(car_name):
    """
    Search for car model translation online (Wikipedia)
    """
    try:
        search_query = quote(f"{car_name} car")
        url = f"https://en.wikipedia.org/wiki/{search_query.replace(' ', '_')}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('h1', {'id': 'firstHeading'})
            if title:
                return title.text.strip()
    except:
        pass
    return None

def split_car_model(text):
    """
    Split car name into parts: brand, model, trim
    """
    text = text.strip()
    original = text
    brand = None
    model = None
    trim = []
    remaining = []

    # Search for brand
    for ar_brand in BRAND_TRANSLATION.keys():
        if ar_brand in text:
            brand = ar_brand
            text = text.replace(ar_brand, '', 1).strip()
            break

    # Search for model
    words = text.split()
    for word in words:
        found = False
        for ar_model in MODEL_TRANSLATION.keys():
            if ar_model in word or word in ar_model:
                model = ar_model
                text = text.replace(ar_model, '', 1).strip()
                found = True
                break
        if found:
            break

    # Search for trim keywords
    words = text.split()
    for word in words:
        word_lower = word.lower()
        matched = False
        for trim_name, keywords in TRIM_KEYWORDS.items():
            if word_lower in keywords or any(kw in word_lower for kw in keywords):
                trim.append(trim_name)
                text = text.replace(word, '', 1).strip()
                matched = True
                break
        if not matched:
            remaining.append(word)

    # Clean up remaining text
    extra = ' '.join(remaining).strip()
    if extra and not model:
        model = extra
        extra = ''

    return {
        'brand': brand,
        'model': model,
        'trim': ' '.join(trim) if trim else None,
        'extra': extra if extra else None
    }

def translate_car_model_smart(text):
    """
    Smart translation of car names using dictionaries and online search.
    """
    if not isinstance(text, str) or text.strip() == '':
        return text
    original = text.strip()

    # Parse the name
    parts = split_car_model(original)

    translated_parts = []

    # Translate brand
    if parts['brand']:
        translated_parts.append(BRAND_TRANSLATION.get(parts['brand'], parts['brand']))

    # Translate model
    if parts['model']:
        if parts['model'] in MODEL_TRANSLATION:
            translated_parts.append(MODEL_TRANSLATION[parts['model']])
        else:
            # Try online search
            online = search_car_model_online(parts['model'])
            if online:
                translated_parts.append(online)
            else:
                translated_parts.append(parts['model'])  # keep as is

    # Add trim
    if parts['trim']:
        translated_parts.append(parts['trim'])

    # Add extra text
    if parts['extra']:
        # If it contains Arabic, translate it normally
        if any('\u0600' <= c <= '\u06FF' for c in parts['extra']):
            translated_parts.append(translate_text_fallback(parts['extra']))
        else:
            translated_parts.append(parts['extra'])

    # If nothing was translated, return original
    if not translated_parts:
        return original

    return ' '.join(translated_parts)

def translate_text_fallback(text, target='en'):
    """Translate plain text using dictionary or automatic translation."""
    if text in TRANSLATION_DICT:
        return TRANSLATION_DICT[text]
    try:
        translated = GoogleTranslator(source='ar', target=target).translate(text)
        if translated and translated != text:
            return translated
    except:
        pass
    return text

def translate_text(text, target='en'):
    # General function for other texts (not model)
    return translate_text_fallback(text, target)

def fix_arabic(text):
    """Reshape Arabic text for proper display."""
    if isinstance(text, str) and any("\u0600" <= c <= "\u06FF" for c in text):
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        except:
            return text
    return text

# -------------------- Basic data extraction functions --------------------
def convert_arabic_numbers(text):
    """Convert Arabic numerals (e.g., ١٢٣) to Western numbers (123)."""
    arabic_nums = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    return text.translate(arabic_nums)

def extract_year(text):
    text = convert_arabic_numbers(text)
    matches = re.findall(r'\b(19[0-9]{2}|20[0-9]{2})\b', text)
    for match in matches:
        year = int(match)
        if 1900 <= year <= 2025:
            return match
    return "N/A"

def extract_mileage(text):
    text = convert_arabic_numbers(text)
    patterns = [
        r'(\d+[,.]?\d*\s*-\s*\d+[,.]?\d*)\s*(كم|كيلومتر|km)',
        r'(\+?\d+[,.]?\d*)\s*(كم|كيلومتر|km)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(0)
    return "غير محدد"

def extract_condition(text):
    if re.search(r'(جديد|زيرو|zero|وكالة|new)', text, re.I):
        return "جديد (زيرو)"
    elif re.search(r'(مستعمل|used)', text, re.I):
        return "مستعمل"
    return "غير محدد"

def extract_seller_type(card):
    try:
        badge = card.find_element(By.CSS_SELECTOR, "div.memberBadge")
        badge_text = badge.text
        if "مستخدم موثق" in badge_text:
            return "شخصي"
        elif "نشاط تجاري موثق" in badge_text:
            return "معرض/وكالة"
    except:
        pass
    text = card.text
    if re.search(r'(معرض|dealership)', text, re.I):
        return "معرض"
    elif re.search(r'(وكالة|agency)', text, re.I):
        return "وكالة"
    elif re.search(r'(شخصي|private|مالك)', text, re.I):
        return "شخصي"
    return "غير محدد"

def extract_json_ld(html):
    try:
        pattern = r'<script type="application/ld\+json">(.*?)</script>'
        scripts = re.findall(pattern, html, re.DOTALL)
        for script in scripts:
            try:
                data = json.loads(script)
                if isinstance(data, dict) and data.get('@type') == 'Vehicle':
                    return data
                elif isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'Vehicle':
                            return item
            except:
                continue
    except:
        pass
    return None

# -------------------- Enhanced model extraction functions --------------------
def extract_model_from_card_and_page(card, page_html=None, page_driver=None):
    # 1. JSON-LD
    if page_html:
        json_data = extract_json_ld(page_html)
        if json_data:
            if 'name' in json_data and json_data['name']:
                return json_data['name']
            if 'model' in json_data and json_data['model']:
                return json_data['model']
    # 2. h1 from details page
    if page_driver:
        try:
            h1 = page_driver.find_element(By.CSS_SELECTOR, "h1")
            h1_text = h1.text.strip()
            if h1_text:
                return h1_text
        except:
            pass
    # 3. h2 on card
    try:
        h2 = card.find_element(By.CSS_SELECTOR, "h2.breakWord.trimTwoLines.font-20, h2.breakWord, h2")
        h2_text = h2.text.strip()
        if h2_text:
            return h2_text
    except:
        pass
    # 4. First line of card text
    card_text = card.text
    lines = [line.strip() for line in card_text.split('\n') if line.strip()]
    if lines:
        return lines[0]
    # 5. Fallback to text analysis
    return extract_brand_model_from_text(card_text)

def extract_brand_model_from_text(text):
    text = text.strip()
    found_brand = None
    for brand in CAR_BRANDS:
        if brand in text:
            found_brand = brand
            break
    if found_brand:
        rest = text.replace(found_brand, '', 1).strip()
        rest = re.sub(r'\b(للبيع|سيارة|بحالة|نظيف|مستعمل|جديد|زيرو|وكالة|معرض|شخصي|فحص|كامل|ممتازة|عداد|قليل|فل|كاش|اقساط|بدون|جمرك|لقطة|مالك|شركه|الوكاله|نظيفة|استخدام)\b', '', rest, flags=re.I)
        rest = re.sub(r'\s+', ' ', rest).strip()
        if rest:
            return f"{found_brand} {rest}"
        else:
            return found_brand
    cleaned = re.sub(r'\b(للبيع|سيارة|بحالة|نظيف|مستعمل|جديد|زيرو|وكالة|معرض|شخصي|فحص|كامل|ممتازة|عداد|قليل|فل|كاش|اقساط|بدون|جمرك|لقطة|مالك|شركه)\b', '', text, flags=re.I)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else "غير متوفر"

# -------------------- Enhanced fuel type extraction --------------------
def extract_fuel_type_advanced(driver):
    json_data = extract_json_ld(driver.page_source)
    page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    if json_data and 'fuelType' in json_data:
        fuel = json_data['fuelType'].lower()
        if 'electric' in fuel:
            return "كهرباء"
        elif 'hybrid' in fuel:
            return "هايبرد"
        elif 'diesel' in fuel:
            return "ديزل"
        elif 'petrol' in fuel or 'gasoline' in fuel:
            return "بنزين"
    try:
        fuel_elem = driver.find_element(By.XPATH, "//span[contains(text(),'نوع الوقود')]/following-sibling::a")
        fuel_text = fuel_elem.text.strip()
        if fuel_text:
            if 'كهرباء' in fuel_text:
                return "كهرباء"
            elif 'هايبرد' in fuel_text:
                return "هايبرد"
            elif 'ديزل' in fuel_text:
                return "ديزل"
            elif 'بنزين' in fuel_text:
                return "بنزين"
    except:
        pass
    if re.search(r'\b(هايبرد|hybrid)\b', page_text, re.I):
        return "هايبرد"
    if re.search(r'\b(ديزل|diesel)\b', page_text, re.I):
        return "ديزل"
    if re.search(r'\b(بنزين|petrol|gasoline)\b', page_text, re.I):
        return "بنزين"
    if re.search(r'\b(كهرباء|electric|ev)\b', page_text, re.I):
        return "كهرباء"
    return "غير محدد"

# -------------------- Price extraction and advanced installment detection --------------------
def clean_price_number(price_str):
    if not isinstance(price_str, str) or price_str == "N/A":
        return np.nan
    match = re.search(r'(\d+[,.]?\d*)', price_str)
    if match:
        try:
            return float(match.group(1).replace(',', ''))
        except:
            pass
    return np.nan

def is_installment_advanced(price_str, page_text, fuel_type=None, price_num=None):
    if not isinstance(price_str, str):
        return False

    # Explicit installment keywords
    installment_keywords = ['قسط', 'شهري', 'تقسيط', 'installment', 'monthly', 'دفعة أولى', 'دفعة']
    combined = price_str + " " + page_text
    for kw in installment_keywords:
        if re.search(rf'\b{kw}\b', combined, re.I):
            return True

    # Price rules based on fuel type
    if fuel_type is not None and price_num is not None:
        if fuel_type == 'كهرباء' and price_num < 9000:
            return True
        if fuel_type == 'هايبرد' and price_num < 6000:
            return True

    return False

def extract_price_from_page(driver):
    json_data = extract_json_ld(driver.page_source)
    page_text = driver.find_element(By.TAG_NAME, "body").text
    price_text = "N/A"
    price_num = np.nan

    # 1. JSON-LD
    if json_data and 'offers' in json_data:
        offers = json_data['offers']
        if isinstance(offers, dict) and 'price' in offers:
            price_val = offers['price']
            try:
                if isinstance(price_val, (int, float)):
                    num = price_val
                else:
                    num = float(str(price_val).replace(',', ''))
                if 1000 <= num <= 200000:
                    currency = offers.get('priceCurrency', 'دينار')
                    price_text = f"{price_val} {currency}"
                    price_num = num
            except:
                pass

    # 2. Visible price elements
    if price_num is np.nan:
        selectors = [
            "div.priceColor.bold.alignSelfCenter.font-18.ms-auto",
            "span.postCard__price",
            "div._price",
            "span.price"
        ]
        for selector in selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+)\s*(دينار|JD)?', text)
                if match:
                    num_str = match.group(1)
                    try:
                        num = float(num_str.replace(',', ''))
                        if 1000 <= num <= 200000:
                            price_text = text
                            price_num = num
                            break
                    except:
                        pass
            except:
                continue

    # 3. General page search
    if price_num is np.nan:
        patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*(دينار|JD)',
            r'(\d+)\s*(دينار|JD)'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, page_text)
            for num_str, unit in matches:
                clean_num = float(num_str.replace(',', ''))
                if 1000 <= clean_num <= 200000:
                    price_text = f"{num_str} دينار"
                    price_num = clean_num
                    break
            if price_num is not np.nan:
                break

    return price_text, price_num

# -------------------- Other helper functions --------------------
def extract_transmission_from_page(driver):
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text
        if re.search(r'(اوتوماتيك|automatic|اتوماتيك)', page_text, re.I):
            return "اوتوماتيك"
        elif re.search(r'(يدوي|manual|عادي)', page_text, re.I):
            return "يدوي"
    except:
        pass
    try:
        trans_elem = driver.find_element(By.XPATH, "//span[contains(text(),'ناقل الحركة')]/following-sibling::a")
        return trans_elem.text.strip()
    except:
        pass
    return "غير محدد"

def extract_color_from_page(driver):
    try:
        color_elem = driver.find_element(By.XPATH, "//span[contains(text(),'اللون')]/following-sibling::a")
        return color_elem.text.strip()
    except:
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            colors = ['أبيض', 'أسود', 'رمادي', 'فضي', 'أزرق', 'أحمر', 'أخضر', 'بني', 'بيج', 'ذهبي', 'أزرق فاتح']
            for c in colors:
                if c in page_text:
                    return c
        except:
            pass
    return "غير محدد"

def extract_insurance_from_page(driver):
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text
        if re.search(r'تأمين شامل', page_text, re.I):
            return "تأمين شامل"
        elif re.search(r'تأمين إلزامي', page_text, re.I):
            return "تأمين إلزامي"
        elif re.search(r'(تأمين|مؤمنة|مرخصة)', page_text, re.I):
            return "يوجد تأمين"
    except:
        pass
    return "لا يوجد تأمين"

# -------------------- Browser setup --------------------
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# -------------------- Main program --------------------
def main():
    driver = setup_driver()
    base_url = "https://jo.opensooq.com"
    search_url = urljoin(base_url, "/ar/سيارات-ومركبات/سيارات-للبيع?search=true&Post_type=7511&Payment_Method=7513&CarCustoms=12565&has_price=1")

    print(fix_arabic("🔗 Loading search page..."))
    driver.get(search_url)
    wait = WebDriverWait(driver, 20)

    # Initial statistics
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.postListItemData")))
        first_page_count = len(driver.find_elements(By.CSS_SELECTOR, "a.postListItemData"))
        try:
            last_page_link = driver.find_element(By.CSS_SELECTOR, "a[data-id='lastPageArrow']")
            last_page_href = last_page_link.get_attribute("href")
            match = re.search(r'page=(\d+)', last_page_href)
            total_pages = int(match.group(1)) if match else 1
        except:
            total_pages = 1
        total_ads_estimate = first_page_count * total_pages
        print(fix_arabic(f"\n📊 Search statistics:"))
        print(fix_arabic(f"   - Ads on first page: {first_page_count}"))
        print(fix_arabic(f"   - Available pages: {total_pages}"))
        print(fix_arabic(f"   - Estimated total: ~{total_ads_estimate} ads"))
    except Exception as e:
        print(fix_arabic(f"⚠️ Could not calculate statistics: {e}"))

    # Choose number of ads
    print(fix_arabic("\n🔢 How many ads do you want to scrape? (Enter a number or 'all' to scrape all): "))
    user_input = input().strip().lower()
    if user_input == 'all':
        max_ads = float('inf')
    else:
        try:
            max_ads = int(user_input)
        except:
            print(fix_arabic("❌ Invalid input, scraping only 10 ads."))
            max_ads = 10

    all_ads = []
    ad_counter = 1
    current_page = 1
    stop_flag = False

    while not stop_flag:
        print(fix_arabic(f"\n📄 Scraping page {current_page}..."))
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.postListItemData")))
            time.sleep(2)
            ad_cards = driver.find_elements(By.CSS_SELECTOR, "a.postListItemData")
            print(fix_arabic(f"   Found {len(ad_cards)} ads on this page."))

            for card in ad_cards:
                if ad_counter > max_ads:
                    stop_flag = True
                    break

                try:
                    relative_link = card.get_attribute("href")
                    if not relative_link:
                        continue
                    full_link = urljoin(base_url, relative_link)

                    # Data from card
                    card_text = card.text
                    try:
                        location_elem = card.find_element(By.CSS_SELECTOR, "div.flex.alignItems.gap-5.darkGrayColor")
                        location = location_elem.text.strip()
                    except:
                        location = "غير محدد"

                    year = extract_year(card_text)
                    mileage = extract_mileage(card_text)
                    condition = extract_condition(card_text)
                    seller_type = extract_seller_type(card)

                    # Initial model extraction
                    model = extract_model_from_card_and_page(card)

                    # Enter details page
                    price_text = "N/A"
                    price_num = np.nan
                    fuel_type = "غير محدد"
                    insurance = "لا يوجد تأمين"
                    transmission = "غير محدد"
                    color = "غير محدد"

                    if full_link:
                        try:
                            driver.execute_script("window.open(arguments[0]);", full_link)
                            driver.switch_to.window(driver.window_handles[1])
                            time.sleep(2)

                            page_html = driver.page_source
                            model = extract_model_from_card_and_page(card, page_html, driver)

                            if year == "N/A":
                                year = extract_year(driver.find_element(By.TAG_NAME, "body").text)

                            # Extract price
                            price_text, price_num = extract_price_from_page(driver)

                            # Extract fuel type
                            fuel_type = extract_fuel_type_advanced(driver)

                            # Advanced installment check
                            page_text_full = driver.find_element(By.TAG_NAME, "body").text
                            if is_installment_advanced(price_text, page_text_full, fuel_type, price_num):
                                print(fix_arabic(f"⏭️ Skipping ad {ad_counter} (installment) - {fuel_type} at {price_num}"))
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                continue

                            # Remaining data
                            insurance = extract_insurance_from_page(driver)
                            transmission = extract_transmission_from_page(driver)
                            color = extract_color_from_page(driver)

                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                        except Exception as e:
                            print(fix_arabic(f"⚠️ Error opening details for ad {ad_counter}: {e}"))
                            if len(driver.window_handles) > 1:
                                driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            continue

                    if model == "غير متوفر" or not model:
                        model = extract_brand_model_from_text(card_text)

                    all_ads.append({
                        'ID': ad_counter,
                        'Model': model,
                        'Year': year,
                        'Condition': condition,
                        'Fuel Type': fuel_type,
                        'Mileage': mileage,
                        'Seller Type': seller_type,
                        'Location': location,
                        'Price': price_text,
                        'Insurance': insurance,
                        'Transmission': transmission,
                        'Color': color
                    })

                    print(fix_arabic(f"   ✅ {ad_counter}: {model[:50]}... | {price_text} | {fuel_type}"))
                    ad_counter += 1

                except Exception as e:
                    print(fix_arabic(f"⚠️ Error processing ad: {e}"))
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    continue

            if stop_flag:
                break

            # Go to next page
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a[data-id='nextPageArrow']")
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)
                current_page += 1
            except NoSuchElementException:
                print(fix_arabic("No more pages."))
                break

        except TimeoutException:
            print(fix_arabic("Page load timeout."))
            break
        except Exception as e:
            print(fix_arabic(f"Unexpected error: {e}"))
            break

    driver.quit()

    # Process and save data
    if all_ads:
        df = pd.DataFrame(all_ads)
        df = df[['ID', 'Model', 'Year', 'Condition', 'Fuel Type', 'Mileage', 'Seller Type', 'Location', 'Price', 'Insurance', 'Transmission', 'Color']]

        # Save Arabic version
        arabic_file = "cars_arabic.xlsx"
        df.to_excel(arabic_file, index=False)
        print(fix_arabic(f"\n✅ Saved Arabic version: {arabic_file}"))

        # Create English version with smart translation
        print(fix_arabic("🔄 Translating data to English..."))
        df_en = df.copy()

        # Translate textual fields (except Model)
        for col in ['Condition', 'Fuel Type', 'Seller Type', 'Location', 'Insurance', 'Transmission', 'Color']:
            df_en[col] = df_en[col].apply(lambda x: translate_text(x))

        # Translate model using smart translation
        df_en['Model'] = df_en['Model'].apply(lambda x: translate_car_model_smart(x))

        # Replace invalid values
        df_en = df_en.replace(['N/A', 'غير محدد', 'غير متوفر', 'لا يوجد تأمين'], np.nan)

        # No ad_id added
        # Save Kaggle file
        kaggle_file = "jordan_cars_kaggle.csv"
        df_en.to_csv(kaggle_file, index=False, encoding='utf-8-sig')
        print(fix_arabic(f"✅ Saved Kaggle version: {kaggle_file}"))

        # Quick statistics
        print(fix_arabic("\n📊 Data statistics:"))
        print(f"Total ads: {len(df_en)}")
        print(f"Electric cars: {df_en[df_en['Fuel Type'] == 'Electric'].shape[0]}")
        print(f"Hybrid cars: {df_en[df_en['Fuel Type'] == 'Hybrid'].shape[0]}")
        print(f"Petrol cars: {df_en[df_en['Fuel Type'] == 'Petrol'].shape[0]}")
        print(f"Diesel cars: {df_en[df_en['Fuel Type'] == 'Diesel'].shape[0]}")

        # Show sample
        print(fix_arabic("\n📋 Sample of final data (first 5 rows):"))
        print(df_en[['Model', 'Year', 'Fuel Type', 'Price']].head())

    else:
        print(fix_arabic("No data found."))

if __name__ == "__main__":
    main()

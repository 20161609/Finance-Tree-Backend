# app/lib/ai_receipt.py

import re
import time
from datetime import datetime
from difflib import SequenceMatcher
from io import BytesIO
from typing import Any, List, Optional, Tuple

import numpy as np
from fastapi import UploadFile
from PIL import Image, ImageOps
from paddleocr import PaddleOCR


DEFAULT_MAX_OCR_SIDE = 1100
DEBUG_TIMING = True

TOP_CROP_RATIO = 0.22
MIDDLE_START_RATIO = 0.38
MIDDLE_END_RATIO = 0.82
BOTTOM_CROP_RATIO = 0.25

KNOWN_MERCHANTS = [
    "Walmart", "Walmart Supercentre", "Costco", "Costco Wholesale",
    "Loblaws", "Real Canadian Superstore", "No Frills", "FreshCo", "Metro",
    "Food Basics", "Farm Boy", "Sobeys", "Independent Grocer",
    "Your Independent Grocer", "Valu-Mart", "Whole Foods Market", "Adonis",
    "T&T Supermarket", "Giant Tiger", "Bulk Barn", "Dollarama", "Dollar Tree",
    "Canadian Tire", "Mark's", "Home Depot", "Rona", "Rona Plus",
    "Home Hardware", "Lowe's", "IKEA", "Staples", "Staples Canada",
    "Best Buy", "The Source", "Winners", "Marshalls", "Homesense",
    "Hudson's Bay", "Old Navy", "Gap", "Banana Republic", "H&M", "Zara",
    "Uniqlo", "Sport Chek", "Atmosphere", "Mountain Warehouse", "MEC",
    "Indigo", "Chapters", "Pet Valu", "Petsmart",

    "Shoppers Drug Mart", "Rexall", "Jean Coutu", "Pharmaprix", "Circle K",
    "Mac's", "7-Eleven", "Quickie", "Couche-Tard", "Esso", "Shell",
    "Petro-Canada", "Ultramar", "Pioneer", "Chevron", "Mobil",
    "Costco Gas", "Canadian Tire Gas+", "Irving", "Husky",

    "Tim Hortons", "Starbucks", "Second Cup", "Bridgehead", "McCafe",
    "Coffee Culture", "Cafe Nero", "Cinnabon", "Cobs Bread", "Panera Bread",
    "Pret A Manger", "Krispy Kreme", "Mavericks Donuts",
    "Mavericks Donut Company", "BeaverTails",

    "McDonald's", "Burger King", "A&W", "Wendy's", "Harvey's", "Five Guys",
    "Shake Shack", "Subway", "Taco Bell", "KFC", "Popeyes", "Mary Brown's",
    "Mary Brown's Chicken", "Pizza Pizza", "Little Caesars", "Domino's",
    "Pizza Hut", "Papa Johns", "Gabriel Pizza", "Pizza Nova", "Pizza Depot",
    "New York Fries", "Smoke's Poutinerie", "Pita Pit", "Osmow's",
    "Lazeez Shawarma", "Shawarma Palace", "Shawarma Prince",
    "Jimmy the Greek", "Mucho Burrito", "Chipotle", "Quesada", "Freshii",
    "Booster Juice", "Jugo Juice", "Baskin Robbins", "Dairy Queen",

    "Swiss Chalet", "St Hubert", "Montana's", "Montana's BBQ & Bar",
    "Kelseys", "Kelseys Original Roadhouse", "East Side Mario's",
    "Boston Pizza", "Milestones", "Moxies", "Jack Astor's",
    "Lone Star Texas Grill", "The Keg", "The Keg Steakhouse & Bar",
    "Outback Steakhouse", "Texas Roadhouse", "Denny's", "IHOP",
    "Applebee's", "Chili's", "Olive Garden", "Red Lobster",
    "Buffalo Wild Wings", "Mandarin", "St Louis Bar & Grill",
    "St. Louis Bar & Grill", "Cora", "Cora Breakfast and Lunch",
    "Allo Mon Coco", "Sunset Grill", "Perkins", "Eggsmart", "Aperitivo",
    "Nando's", "Nando's Peri-Peri", "Joey", "Earls", "Local Public Eatery",
    "Thai Express", "Thai Express Kitchen", "Pho Hoa", "Kinton Ramen",
    "Sansotei Ramen", "Sushi Shop", "Sushi Kan", "Hello Sushiman",
    "Kelsey's", "Kelseys Roadhouse",

    "Uber Eats", "DoorDash", "SkipTheDishes", "Fantuan", "Instacart",
    "Crumbl Cookies", "Menchie's", "Marble Slab Creamery",
    "Cold Stone Creamery",

    "Warehouse Stationery", "FedEx Office", "FedEx", "UPS Store", "UPS",
    "Purolator", "Canada Post", "ServiceOntario", "Service Canada",

    "OC Transpo", "STM", "TTC", "Uber", "Lyft", "Via Rail", "Air Canada",
    "WestJet", "Porter Airlines", "FlixBus", "Megabus", "Enterprise",
    "Budget", "Avis", "Hertz",

    "Holiday Inn", "Holiday Inn Express", "Best Western", "Marriott",
    "Courtyard Marriott", "Residence Inn", "Fairfield Inn", "Hilton",
    "Hampton Inn", "Sheraton", "Delta Hotels", "Novotel", "Days Inn",
    "Motel 6", "Comfort Inn",

    "Rogers", "Bell", "Telus", "Fido", "Koodo", "Virgin Plus",
    "Freedom Mobile", "TD Canada Trust", "RBC", "Scotiabank", "BMO",
    "CIBC", "National Bank", "Desjardins",
]

BANNED_MERCHANT_PHRASES = {
    "take out", "takeout", "receipt", "subtotal", "total", "grand total",
    "total due", "amount paid", "amount due", "balance due", "sale", "cash",
    "debit", "credit", "card", "server", "table", "thank you", "email",
    "sign up", "rewards", "store", "store id", "store number", "restaurant",
    "order", "order number", "ticket", "transaction", "drive thru", "pickup",
    "pick up", "cashier", "host", "payment", "change", "change due",
    "approved", "approved amount", "visa", "mastercard", "amex", "gst",
    "hst", "tax",
}

CATEGORY_KEYWORDS = {
    "Restaurant": [
        "combo", "burger", "fries", "pizza", "wings", "sandwich", "drink",
        "soda", "coffee", "latte", "donut", "chicken", "beef", "poutine",
        "shawarma", "burrito", "taco", "nuggets", "meal", "order",
        "drive thru", "take out", "takeout", "dine in", "cashier", "server",
        "table", "roast beef", "cheddar", "coke", "pepsi", "biscuit",
        "gravy", "mashed potatoes", "tenders", "hamburger", "cheeseburger",
        "milkshake", "hot dog", "sub", "wrap", "bowl",
    ],
    "Grocery Store": [
        "grocery", "produce", "dairy", "frozen", "meat", "bakery", "banana",
        "onion", "lettuce", "milk", "egg", "eggs", "bread", "rice", "apple",
        "carrots", "potato", "potatoes", "yogurt", "cream", "cheese",
        "chicken thigh", "lemon", "mango", "garlic", "ginger", "broccoli",
        "asparagus", "hummus", "sour cream", "sushi rice", "soy bean",
        "soy sauce", "drumstick", "green onion",
    ],
    "Pharmacy": [
        "pharmacy", "drug", "prescription", "vitamin", "supplement",
        "toothpaste", "shampoo", "conditioner", "body wash", "pain relief",
        "cold medicine", "medicine", "allergy", "bandage", "ointment",
        "rexall", "shoppers",
    ],
    "Electronics": [
        "usb", "charger", "cable", "adapter", "battery", "batteries",
        "headphones", "earbuds", "mouse", "keyboard", "monitor",
        "screen protector", "phone case", "hdmi", "ssd", "memory card",
        "laptop", "tablet", "iphone", "android",
    ],
    "Gas / Convenience": [
        "fuel", "gas", "diesel", "regular", "premium", "pump", "litre",
        "liter", "car wash", "lottery", "cigarettes", "tobacco", "snack",
        "slush", "energy drink", "convenience", "propane",
    ],
    "Clothing / Retail": [
        "shirt", "t shirt", "pants", "jeans", "socks", "hoodie", "jacket",
        "shoes", "sneakers", "dress", "skirt", "toy", "home", "decor",
        "storage", "hanger", "pillow", "blanket", "lamp", "notebook",
        "binder", "marker",
    ],
}

EXCLUDE_AMOUNT_KEYWORDS = [
    "subtotal", "sub total", "tax", "gst", "hst", "vat", "sales tax",
    "state tax", "tip", "suggested tip", "gratuity", "change", "change due",
    "discount", "save", "saved", "savings", "reward", "points", "rate",
    "off", "qty", "quantity", "price", "unit price", "auth", "approved",
    "ref", "trace", "aid", "tc", "entry", "sign up", "email", "rewards",
    "item sold", "items sold", "total number of items",
]

ITEMISH_KEYWORDS = [
    "burger", "fries", "pizza", "wings", "drink", "soda", "combo", "meal",
    "coffee", "donut", "chicken", "sandwich", "burrito", "taco", "wrap",
    "nuggets", "shake", "bread", "rice", "milk", "egg", "banana",
]

DATE_HINT_KEYWORDS = [
    "date", "transaction date", "order date", "invoice date", "purchase date",
]

_AMOUNT_PATTERN = re.compile(r"(?<![\d%])(\d{1,6}\.\d{2})(?![\d%])")

_OCR_ENGINE: Optional[PaddleOCR] = None
KNOWN_MERCHANTS_CANON: List[Tuple[str, str]] = []
BANNED_MERCHANT_PHRASES_CANON = set()


def _log_timing(label: str, started_at: float) -> None:
    if DEBUG_TIMING:
        print(f"[ai_receipt] {label}: {time.perf_counter() - started_at:.3f}s")


def _init_caches() -> None:
    global KNOWN_MERCHANTS_CANON, BANNED_MERCHANT_PHRASES_CANON

    if not KNOWN_MERCHANTS_CANON:
        KNOWN_MERCHANTS_CANON = [
            (merchant, _canonicalize_for_match(merchant))
            for merchant in KNOWN_MERCHANTS
        ]

    if not BANNED_MERCHANT_PHRASES_CANON:
        BANNED_MERCHANT_PHRASES_CANON = {
            _canonicalize_for_match(x) for x in BANNED_MERCHANT_PHRASES
        }


def _get_ocr_engine() -> PaddleOCR:
    global _OCR_ENGINE

    if _OCR_ENGINE is None:
        t0 = time.perf_counter()
        _OCR_ENGINE = PaddleOCR(
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="en_PP-OCRv5_mobile_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        _log_timing("ocr_engine_init", t0)

    return _OCR_ENGINE


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _looks_meaningful_text(text: str) -> bool:
    text = _normalize_whitespace(text)
    if not text:
        return False
    if len(re.sub(r"[^A-Za-z0-9]", "", text)) < 2:
        return False
    return True


def _canonicalize_for_match(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("&", " and ")
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^a-z0-9' ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_texts_from_ocr_result(result: Any) -> List[str]:
    found: List[str] = []
    seen = set()

    def add_text(value: str) -> None:
        s = _normalize_whitespace(value)
        if not _looks_meaningful_text(s):
            return
        key = s.lower()
        if key in seen:
            return
        seen.add(key)
        found.append(s)

    def walk(obj: Any) -> None:
        if obj is None:
            return

        if isinstance(obj, str):
            add_text(obj)
            return

        if isinstance(obj, dict):
            for key in ("rec_texts", "texts", "text", "label_names", "labels"):
                value = obj.get(key)
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            add_text(item)
                elif isinstance(value, str):
                    add_text(value)

            if "res" in obj:
                walk(obj["res"])
            elif "result" in obj:
                walk(obj["result"])
            return

        if isinstance(obj, (list, tuple)):
            for item in obj:
                walk(item)
            return

        if hasattr(obj, "rec_texts"):
            try:
                for item in getattr(obj, "rec_texts", []):
                    if isinstance(item, str):
                        add_text(item)
            except Exception:
                pass
            return

        if hasattr(obj, "__dict__"):
            data = vars(obj)
            if "rec_texts" in data:
                walk(data["rec_texts"])
            elif "res" in data:
                walk(data["res"])

    walk(result)
    return found


def _image_bytes_to_pil(image_bytes: bytes) -> Image.Image:
    img = Image.open(BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def _resize_if_needed(img: Image.Image, max_side: int = DEFAULT_MAX_OCR_SIDE) -> Image.Image:
    w, h = img.size
    longest = max(w, h)

    if longest <= max_side:
        return img

    scale = max_side / float(longest)
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.LANCZOS)


def _pil_to_numpy(img: Image.Image) -> np.ndarray:
    return np.array(img)


def _crop_top(img: Image.Image, ratio: float = TOP_CROP_RATIO) -> Image.Image:
    w, h = img.size
    return img.crop((0, 0, w, max(1, int(h * ratio))))


def _crop_middle(img: Image.Image, start_ratio: float = MIDDLE_START_RATIO, end_ratio: float = MIDDLE_END_RATIO) -> Image.Image:
    w, h = img.size
    y1 = max(0, int(h * start_ratio))
    y2 = min(h, int(h * end_ratio))
    if y2 <= y1:
        y1, y2 = 0, h
    return img.crop((0, y1, w, y2))


def _crop_bottom(img: Image.Image, ratio: float = BOTTOM_CROP_RATIO) -> Image.Image:
    w, h = img.size
    start_y = max(0, int(h * (1.0 - ratio)))
    return img.crop((0, start_y, w, h))


def _run_ocr_on_pil(img: Image.Image, label: str) -> List[str]:
    t0 = time.perf_counter()
    ocr = _get_ocr_engine()
    _log_timing(f"{label}_get_ocr_engine", t0)

    t1 = time.perf_counter()
    resized = _resize_if_needed(img)
    image_np = _pil_to_numpy(resized)
    _log_timing(f"{label}_prepare_image", t1)

    t2 = time.perf_counter()
    result = ocr.predict(image_np)
    _log_timing(f"{label}_ocr_predict", t2)

    t3 = time.perf_counter()
    lines = _extract_texts_from_ocr_result(result)
    _log_timing(f"{label}_extract_texts", t3)

    return lines


def _score_category(lines: List[str]) -> str:
    blob = _canonicalize_for_match(" ".join(lines))
    best_category = "General Retail"
    best_score = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            kw_norm = _canonicalize_for_match(kw)
            if kw_norm and kw_norm in blob:
                score += 2
        if score > best_score:
            best_score = score
            best_category = category

    return best_category


def _normalize_merchant_name(candidate: str) -> Optional[str]:
    _init_caches()

    if not candidate:
        return None

    cand = _canonicalize_for_match(candidate)
    if not cand or cand in BANNED_MERCHANT_PHRASES_CANON:
        return None

    for merchant, merchant_canon in KNOWN_MERCHANTS_CANON:
        if cand and len(cand) >= 4 and (cand in merchant_canon or merchant_canon in cand):
            return merchant

    best_match = None
    best_score = 0.0

    for merchant, merchant_canon in KNOWN_MERCHANTS_CANON:
        score = SequenceMatcher(None, cand, merchant_canon).ratio()
        if score > best_score:
            best_score = score
            best_match = merchant

    if best_score >= 0.86:
        return best_match

    return None


def _extract_merchant(lines: List[str]) -> Optional[str]:
    _init_caches()

    if not lines:
        return None

    best_match = None
    best_score = 0.0

    for line in lines[:8]:
        s = _normalize_whitespace(line)
        norm = _canonicalize_for_match(s)

        if not s:
            continue
        if len(re.sub(r"[^A-Za-z]", "", s)) < 3:
            continue
        if norm in BANNED_MERCHANT_PHRASES_CANON:
            continue
        if any(bp in norm for bp in BANNED_MERCHANT_PHRASES_CANON):
            continue
        if re.search(r"\d{3}[-\s]?\d{3}[-\s]?\d{4}", s):
            continue
        if re.search(r"\d+\.\d{2}", s):
            continue
        if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", s):
            continue
        if re.search(r"\b\d{1,2}:\d{2}\b", s):
            continue
        if re.search(r"\b(st|street|rd|road|ave|avenue|blvd|dr|drive|hwy|highway)\b", norm):
            continue

        merchant = _normalize_merchant_name(s)
        if not merchant:
            continue

        merchant_canon = _canonicalize_for_match(merchant)
        if norm and len(norm) >= 4 and (norm in merchant_canon or merchant_canon in norm):
            score = 0.95
        else:
            score = SequenceMatcher(None, norm, merchant_canon).ratio()

        if score > best_score:
            best_score = score
            best_match = merchant

    if best_score >= 0.86:
        return best_match

    return None


def _extract_description(lines: List[str]) -> Optional[str]:
    merchant = _extract_merchant(lines)
    if merchant:
        return merchant

    category = _score_category(lines)
    return category if category else None


def _normalize_line_for_amount(line: str) -> str:
    return _normalize_whitespace(line.replace(",", ""))


def _extract_amounts_from_line(line: str) -> List[float]:
    normalized = _normalize_line_for_amount(line)
    values: List[float] = []

    for m in _AMOUNT_PATTERN.findall(normalized):
        try:
            values.append(float(m))
        except ValueError:
            pass

    return values


def _contains_any(line_norm: str, keywords: List[str]) -> bool:
    return any(k in line_norm for k in keywords)


def _is_excluded_amount_line(line: str) -> bool:
    norm = _canonicalize_for_match(line)
    return _contains_any(norm, EXCLUDE_AMOUNT_KEYWORDS)


def _looks_like_item_line(line: str) -> bool:
    norm = _canonicalize_for_match(line)
    if _contains_any(norm, ITEMISH_KEYWORDS):
        return True
    if re.search(r"\b\d+\s+[@x]\s*\d", norm):
        return True
    return False


def _normalize_date_candidate(text: str) -> str:
    text = _normalize_whitespace(text)
    text = text.replace("O", "0").replace("o", "0")
    text = text.replace(".", "/").replace("-", "/")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _try_parse_date(date_str: str) -> Optional[str]:
    formats = [
        "%Y/%m/%d",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%y",
        "%m/%d/%y %H:%M",
        "%m/%d/%y %H:%M:%S",
        "%d/%m/%y",
        "%d/%m/%y %H:%M",
        "%d/%m/%y %H:%M:%S",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
        "%d %B %Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if 2000 <= dt.year <= 2100:
                return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def _score_date_candidate(raw: str, line_idx: int) -> int:
    score = 0
    norm = _canonicalize_for_match(raw)

    if line_idx < 12:
        score += 3
    elif line_idx < 24:
        score += 1

    if any(hint in norm for hint in DATE_HINT_KEYWORDS):
        score += 4
    if re.search(r"\b20\d{2}[/-]\d{1,2}[/-]\d{1,2}\b", raw):
        score += 5
    if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]20\d{2}\b", raw):
        score += 4
    if re.search(r"\b[A-Za-z]{3,9}\s+\d{1,2},\s*20\d{2}\b", raw):
        score += 4
    if re.search(r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+20\d{2}\b", raw):
        score += 4

    return score


def _extract_date(lines: List[str]) -> Optional[str]:
    if not lines:
        return None

    numeric_patterns = [
        r"\b(20\d{2}[/-]\d{1,2}[/-]\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)\b",
        r"\b(\d{1,2}[/-]\d{1,2}[/-]20\d{2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)\b",
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)\b",
    ]

    text_patterns = [
        r"\b([A-Za-z]{3,9}\s+\d{1,2},\s*20\d{2})\b",
        r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+20\d{2})\b",
    ]

    candidates: List[Tuple[int, str]] = []

    for idx, line in enumerate(lines):
        normalized = _normalize_date_candidate(line)

        for pattern in numeric_patterns:
            matches = re.findall(pattern, normalized)
            for match in matches:
                parsed = _try_parse_date(match)
                if parsed:
                    candidates.append((_score_date_candidate(match, idx), parsed))

        for pattern in text_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                parsed = _try_parse_date(match)
                if parsed:
                    candidates.append((_score_date_candidate(match, idx), parsed))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _extract_cashflow(lines: List[str]) -> Optional[float]:
    if not lines:
        return None

    candidates: List[Tuple[int, float, int, str]] = []
    subtotal_hits: List[Tuple[int, float]] = []
    tax_hits: List[Tuple[int, float]] = []

    for idx, line in enumerate(lines):
        norm = _canonicalize_for_match(line)
        vals = [v for v in _extract_amounts_from_line(line) if v > 0]
        if not vals:
            continue

        amount = vals[-1]
        score = 0

        if "subtotal" in norm or "sub total" in norm:
            subtotal_hits.append((idx, amount))
            continue

        if any(k in norm for k in ["gst", "hst", "vat", "sales tax", "state tax", "tax"]):
            if "total tax" not in norm:
                tax_hits.append((idx, amount))
            continue

        strong_total_keywords = [
            "grand total", "amount due", "balance due", "total due",
            "net total", "order total", "take out total", "take out",
            "take-out total", "amount paid", "total purchase"
        ]
        if any(k in norm for k in strong_total_keywords):
            score += 120

        if "total" in norm and "subtotal" not in norm and "sub total" not in norm:
            score += 70

        payment_keywords = [
            "payment", "approved amount", "approved", "credit card",
            "debit", "visa", "mastercard", "amex", "paid"
        ]
        if any(k in norm for k in payment_keywords):
            score += 35

        score += idx * 3

        if amount < 1:
            score -= 30
        elif amount < 5:
            score -= 10

        if _is_excluded_amount_line(line):
            score -= 120

        if _looks_like_item_line(line):
            score -= 60

        alpha_count = len(re.sub(r"[^A-Za-z]", "", line))
        if alpha_count == 0:
            score -= 20

        candidates.append((idx, amount, score, line))

    print("CASHFLOW_CANDIDATES =", candidates)
    print("SUBTOTAL_HITS =", subtotal_hits)
    print("TAX_HITS =", tax_hits)

    strong = [x for x in candidates if x[2] >= 80]
    if strong:
        strong.sort(key=lambda x: (x[2], x[0], x[1]), reverse=True)
        return strong[0][1]

    if subtotal_hits and tax_hits:
        subtotal = subtotal_hits[-1][1]
        tax = tax_hits[-1][1]
        combined = round(subtotal + tax, 2)

        near_combined = [
            x for x in candidates
            if abs(x[1] - combined) <= 0.05 and x[2] > -50
        ]
        if near_combined:
            near_combined.sort(key=lambda x: (x[2], x[0]), reverse=True)
            return near_combined[0][1]

        return combined

    if candidates:
        candidates.sort(key=lambda x: (x[2], x[0], x[1]), reverse=True)
        best = candidates[0]
        if best[2] >= 20:
            return best[1]

    fallback_vals: List[Tuple[int, float]] = []
    for idx, line in enumerate(lines):
        if _is_excluded_amount_line(line):
            continue
        vals = [v for v in _extract_amounts_from_line(line) if v > 0]
        for v in vals:
            fallback_vals.append((idx, v))

    if fallback_vals:
        fallback_vals.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return fallback_vals[0][1]

    return None


def _merge_unique_lines(*groups: List[str]) -> List[str]:
    result: List[str] = []
    seen = set()

    for group in groups:
        for line in group:
            key = line.lower()
            if key not in seen:
                seen.add(key)
                result.append(line)

    return result


async def extract_receipt_info(receipt: UploadFile) -> Optional[dict]:
    print("version_3")
    total_t0 = time.perf_counter()

    if not receipt or not receipt.filename:
        return None

    lower_name = receipt.filename.lower()
    if not lower_name.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
        return None

    print("DEFAULT_MAX_OCR_SIDE", DEFAULT_MAX_OCR_SIDE)

    try:
        t0 = time.perf_counter()
        content = await receipt.read()
        _log_timing("read_upload", t0)

        if not content:
            return None

        t1 = time.perf_counter()
        original_img = _image_bytes_to_pil(content)
        _log_timing("open_image", t1)

        t2 = time.perf_counter()
        top_img = _crop_top(original_img)
        middle_img = _crop_middle(original_img)
        bottom_img = _crop_bottom(original_img)
        _log_timing("crop_image", t2)

        top_lines = _run_ocr_on_pil(top_img, "top")
        middle_lines = _run_ocr_on_pil(middle_img, "middle")
        bottom_lines = _run_ocr_on_pil(bottom_img, "bottom")

        merged_lines = _merge_unique_lines(top_lines, middle_lines, bottom_lines)
        cashflow_lines = _merge_unique_lines(middle_lines, bottom_lines)

        print("TOP_LINES =", top_lines)
        print("MIDDLE_LINES =", middle_lines)
        print("BOTTOM_LINES =", bottom_lines)
        print("MERGED_LINES =", merged_lines)
        print("CASHFLOW_LINES =", cashflow_lines)

        date_value = _extract_date(top_lines) or _extract_date(merged_lines)
        description_value = _extract_description(top_lines) or _extract_description(merged_lines)

        full_lines: List[str] = []

        cashflow_value = _extract_cashflow(middle_lines)
        if cashflow_value is None:
            cashflow_value = _extract_cashflow(cashflow_lines)
        if cashflow_value is None:
            full_lines = _run_ocr_on_pil(original_img, "full_cashflow_fallback")
            print("FULL_CASHFLOW_LINES =", full_lines)
            cashflow_value = _extract_cashflow(full_lines)

        if not date_value and not description_value:
            if not full_lines:
                full_lines = _run_ocr_on_pil(original_img, "full_header_fallback")
            date_value = date_value or _extract_date(full_lines)
            description_value = description_value or _extract_description(full_lines)

        t3 = time.perf_counter()
        result = {
            "date": date_value,
            "cashflow": cashflow_value,
            "description": description_value,
        }
        _log_timing("post_process", t3)
        _log_timing("extract_receipt_info_total", total_t0)

        return result

    except Exception as e:
        print(f"Failed to extract receipt info: {e}")
        return None

    finally:
        try:
            await receipt.seek(0)
        except Exception:
            pass
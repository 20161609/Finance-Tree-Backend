import re
import uuid
import shutil
import tempfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, List, Optional, Tuple

from fastapi import UploadFile
from PIL import Image, ImageOps
from paddleocr import PaddleOCR


DEFAULT_MAX_OCR_SIDE = 1400

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

TOTAL_PRIMARY_KEYWORDS = [
    "grand total", "total due", "amount due", "balance due", "order total",
    "take out total", "take-out total", "net total", "total",
]

TOTAL_SECONDARY_KEYWORDS = [
    "payment", "approved amount", "credit card", "visa", "debit", "pin",
]

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

_OCR_ENGINE: Optional[PaddleOCR] = None
KNOWN_MERCHANTS_CANON = []
BANNED_MERCHANT_PHRASES_CANON = set()


def _init_caches():
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
        _OCR_ENGINE = PaddleOCR(
            lang="en",
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="en_PP-OCRv5_mobile_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
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


def _recursive_collect_strings(obj: Any) -> List[str]:
    found: List[str] = []

    def walk(x: Any):
        if x is None:
            return
        if isinstance(x, str):
            s = _normalize_whitespace(x)
            if _looks_meaningful_text(s):
                found.append(s)
            return
        if isinstance(x, dict):
            for key in ("rec_texts", "texts", "text", "label_names", "labels", "transcription", "transcriptions"):
                if key in x:
                    walk(x[key])
            for value in x.values():
                walk(value)
            return
        if isinstance(x, (list, tuple, set)):
            for item in x:
                walk(item)
            return
        if hasattr(x, "__dict__"):
            walk(vars(x))

    walk(obj)

    deduped: List[str] = []
    seen = set()
    for item in found:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def _prepare_image_for_ocr(image_path: Path, max_side: int = DEFAULT_MAX_OCR_SIDE) -> Image.Image:
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)

    if img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    longest = max(w, h)

    if longest > max_side:
        scale = max_side / float(longest)
        new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
        img = img.resize(new_size, Image.LANCZOS)

    return img


def _run_ocr(image_path: Path) -> List[str]:
    ocr = _get_ocr_engine()

    temp_dir = Path(tempfile.mkdtemp(prefix="receipt_ocr_"))
    temp_file = temp_dir / f"{uuid.uuid4().hex}.png"

    try:
        prepared_img = _prepare_image_for_ocr(image_path)
        prepared_img.save(temp_file, format="PNG")
        result = ocr.predict(str(temp_file))
        return _recursive_collect_strings(result)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


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

    best_match = None
    best_score = 0.0

    for merchant, merchant_canon in KNOWN_MERCHANTS_CANON:
        if cand and len(cand) >= 4 and (cand in merchant_canon or merchant_canon in cand):
            score = 0.90
        else:
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
            score = 0.90
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
    pattern = re.compile(r"(?<![\d%])(\d{1,6}\.\d{2})(?![\d%])")
    values: List[float] = []

    for m in pattern.findall(normalized):
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


def _is_primary_total_line(line: str) -> bool:
    norm = _canonicalize_for_match(line)
    if "subtotal" in norm or "sub total" in norm:
        return False
    if "total tax" in norm or "total savings" in norm or "total discount" in norm:
        return False
    return _contains_any(norm, TOTAL_PRIMARY_KEYWORDS)


def _is_secondary_total_line(line: str) -> bool:
    norm = _canonicalize_for_match(line)
    if _is_excluded_amount_line(line):
        return False
    return _contains_any(norm, TOTAL_SECONDARY_KEYWORDS)


def _looks_like_item_line(line: str) -> bool:
    norm = _canonicalize_for_match(line)
    if _contains_any(norm, ITEMISH_KEYWORDS):
        return True
    if re.search(r"\b\d+\s+[@x]\s*\d", norm):
        return True
    return False


def _pick_best_amount_from_line(line: str) -> Optional[float]:
    vals = [v for v in _extract_amounts_from_line(line) if v > 0]
    if not vals:
        return None
    return vals[-1]


def _extract_cashflow(lines: List[str]) -> Optional[float]:
    if not lines:
        return None

    primary_hits: List[Tuple[int, float]] = []
    secondary_hits: List[Tuple[int, float]] = []
    subtotal_hits: List[Tuple[int, float]] = []
    tax_hits: List[Tuple[int, float]] = []

    for idx, line in enumerate(lines):
        norm = _canonicalize_for_match(line)
        amount = _pick_best_amount_from_line(line)
        if amount is None or amount <= 0:
            continue

        if _is_primary_total_line(line):
            primary_hits.append((idx, amount))
            continue

        if _is_secondary_total_line(line):
            secondary_hits.append((idx, amount))
            continue

        if "subtotal" in norm or "sub total" in norm:
            subtotal_hits.append((idx, amount))
            continue

        if any(k in norm for k in ["gst", "hst", "vat", "sales tax", "state tax", "tax"]):
            if "total tax" not in norm:
                tax_hits.append((idx, amount))
            continue

    if primary_hits:
        return primary_hits[-1][1]

    if subtotal_hits and tax_hits:
        subtotal = subtotal_hits[-1][1]
        tax = tax_hits[-1][1]
        expected = round(subtotal + tax, 2)
        for _, amt in secondary_hits:
            if abs(amt - expected) <= 0.05:
                return amt

    if secondary_hits:
        return secondary_hits[-1][1]

    if subtotal_hits and tax_hits:
        return round(subtotal_hits[-1][1] + tax_hits[-1][1], 2)

    fallback_candidates: List[Tuple[int, float]] = []
    for idx, line in enumerate(lines):
        if _is_excluded_amount_line(line):
            continue
        if _looks_like_item_line(line):
            continue
        vals = [v for v in _extract_amounts_from_line(line) if v > 0]
        for v in vals:
            fallback_candidates.append((idx, v))

    if fallback_candidates:
        fallback_candidates.sort(key=lambda x: x[0], reverse=True)
        return fallback_candidates[0][1]

    return None


async def extract_receipt_info(receipt: UploadFile) -> Optional[dict]:
    if not receipt or not receipt.filename:
        return None

    suffix = Path(receipt.filename).suffix.lower() or ".png"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
        return None

    temp_dir = Path(tempfile.mkdtemp(prefix="receipt_input_"))
    temp_file = temp_dir / f"{uuid.uuid4().hex}{suffix}"

    try:
        content = await receipt.read()
        if not content:
            return None

        with open(temp_file, "wb") as f:
            f.write(content)

        lines = _run_ocr(temp_file)
        if not lines:
            return {"cashflow": None, "description": None}

        return {
            "cashflow": _extract_cashflow(lines),
            "description": _extract_description(lines),
        }

    except Exception as e:
        print(f"Failed to extract receipt info: {e}")
        return None

    finally:
        try:
            await receipt.seek(0)
        except Exception:
            pass
        shutil.rmtree(temp_dir, ignore_errors=True)
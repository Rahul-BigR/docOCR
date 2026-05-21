import re

# -----------------------------
# Common OCR Character Fix
# -----------------------------
def fix_common_errors(text):

    if not text:
        return text

    replacements = {
        "O": "0",
        "I": "1",
        "L": "1",
        "B": "8",
        # "S": "5",
        "Z": "2"
    }

    text = text.upper()

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


# -----------------------------
# IFSC Correction
# -----------------------------
def correct_ifsc(text):

    if not text:
        return text

    text = text.upper().replace(" ", "")

    chars = list(text)

    # First 4 chars should be letters
    for i in range(min(4, len(chars))):

        if chars[i] == '5':
            chars[i] = 'S'

        elif chars[i] == '8':
            chars[i] = 'B'

        elif chars[i] == '0':
            chars[i] = 'O'

        elif chars[i] == '1':
            chars[i] = 'I'

    # Remaining chars should be numeric/alphanumeric
    for i in range(4, len(chars)):

        if chars[i] == 'O':
            chars[i] = '0'

        elif chars[i] == 'I':
            chars[i] = '1'

        elif chars[i] == 'L':
            chars[i] = '1'

        elif chars[i] == 'Z':
            chars[i] = '2'

    text = ''.join(chars)

    # IFSC length = 11
    text = text[:11]

    match = re.search(r"[A-Z]{4}[0-9A-Z]{7}", text)

    if match:
        return match.group()

    return text


# -----------------------------
# Amount Correction
# -----------------------------
def correct_amount(text):

    text = fix_common_errors(text)

    numbers = re.findall(r"\d+", text)

    if numbers:
        return "".join(numbers)

    return text


# -----------------------------
# Date Correction
# -----------------------------
def _expand_year(year_str):
    """Expand a 2-digit year to 4-digit. 00-30 -> 20xx, 31-99 -> 19xx."""
    if len(year_str) == 2:
        yr = int(year_str)
        return ('20' if yr <= 30 else '19') + year_str
    return year_str


def _validate_date(day, month, year):
    """Return True if day/month/year values are in valid ranges."""
    try:
        return 1 <= int(day) <= 31 and 1 <= int(month) <= 12 and 1900 <= int(year) <= 2100
    except (ValueError, TypeError):
        return False


def correct_date(text):

    if not text:
        return text

    text = text.upper().strip()

    # Fix common OCR character confusion: O->0, I/L->1, B->8, S->5, Z->2
    char_fixes = {'O': '0', 'I': '1', 'L': '1', 'B': '8', 'S': '5', 'Z': '2'}
    text = ''.join(char_fixes.get(ch, ch) for ch in text)

    # Normalize ALL common separators (slash, pipe, backslash, dash, dot, comma, space) -> slash
    text = re.sub(r'[|\\.,\- ]+', '/', text)

    # Remove any remaining non-digit, non-slash characters (e.g. brackets, letters)
    text = re.sub(r'[^0-9/]', '', text)

    # Collapse multiple consecutive slashes and strip leading/trailing slashes
    text = re.sub(r'/+', '/', text).strip('/')

    # --- Step 1: Direct regex match dd/mm/yyyy or d/m/yy ---
    date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', text)
    if date_match:
        day   = date_match.group(1).zfill(2)
        month = date_match.group(2).zfill(2)
        year  = _expand_year(date_match.group(3))
        if _validate_date(day, month, year):
            return f"{day}/{month}/{year}"

    # Collect all digit groups and all digits as one string
    numbers    = re.findall(r'\d+', text)
    all_digits = ''.join(numbers)

    # --- Step 2: All digits concatenated = 8 chars -> ddmmyyyy ---
    if len(all_digits) == 8:
        day, month, year = all_digits[:2], all_digits[2:4], all_digits[4:8]
        if _validate_date(day, month, year):
            return f"{day}/{month}/{year}"

    # --- Step 3: All digits concatenated = 6 chars -> ddmmyy ---
    if len(all_digits) == 6:
        day, month, year = all_digits[:2], all_digits[2:4], _expand_year(all_digits[4:6])
        if _validate_date(day, month, year):
            return f"{day}/{month}/{year}"

    # --- Step 4: Exactly 2 groups like ['2501', '2016'] -> ddmm + yyyy ---
    if len(numbers) == 2:
        first, second = numbers[0], numbers[1]
        if len(first) == 4 and len(second) in (2, 4):
            day, month = first[:2], first[2:4]
            year = _expand_year(second[:4])
            if _validate_date(day, month, year):
                return f"{day}/{month}/{year}"

    # --- Step 5: 3 or more groups -> use first three ---
    if len(numbers) >= 3:
        day   = numbers[0][:2].zfill(2)
        month = numbers[1][:2].zfill(2)
        year  = _expand_year(numbers[2][:4])
        if _validate_date(day, month, year):
            return f"{day}/{month}/{year}"

    return text


# -----------------------------
# Account Number Correction
# -----------------------------
def correct_account_number(text):

    text = fix_common_errors(text)

    numbers = re.findall(r"\d+", text)

    if numbers:
        return "".join(numbers)

    return text


# -----------------------------
# Cheque Number Correction
# -----------------------------
def correct_cheque_number(text):

    text = fix_common_errors(text)

    # Strip MICR bracket characters and other non-digit symbols
    text = re.sub(r'[^0-9A-Z\s]', ' ', text)

    numbers = re.findall(r"\d+", text)

    if numbers:
        # Join ALL digit groups — TrOCR often reads MICR digits as separate chunks
        return "".join(numbers)

    return text


# -----------------------------
# Payee Name Cleaning
# -----------------------------
def correct_name(text):

    if not text:
        return text

    text = text.upper()

    # remove numbers
    text = re.sub(r"\d+", "", text)

    # remove special characters
    text = re.sub(r"[^A-Z\s]", "", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# -----------------------------
# Main Post Processing Function
# -----------------------------
def post_process(field, text):

    if field == "IFSC_Code":
        return correct_ifsc(text)

    elif field == "Amount":
        return correct_amount(text)

    elif field == "Date":
        return correct_date(text)

    elif field == "Account_Number":
        return correct_account_number(text)

    elif field == "Cheque_Number":
        return correct_cheque_number(text)

    elif field == "Payee_Name":
        return correct_name(text)

    return text

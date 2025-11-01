import pytesseract
import re

def extract_text(image):
    return pytesseract.image_to_string(image, config='--oem 3 --psm 6')

def extract_fields(text):
    fields = {}

    # Cheque number (often 6 digits)
    match = re.search(r'\b(\d{6})\b', text)
    fields['cheque_number'] = match.group(1) if match else 'Not found'

    # IFSC code
    match = re.search(r'\b([A-Z]{4}0[A-Z0-9]{6})\b', text)
    fields['ifsc'] = match.group(1) if match else 'Not found'

    # Account number (9-18 digits)
    match = re.search(r'(?:A/c. No.\.?)\b\d{9,18}\b', text)
    fields['account_number'] = match.group(0) if match else 'Not found'

    # Date (dd-mm-yyyy or dd/mm/yyyy)
    match = re.search(r'\b\d{2}[-/]\d{2}[-/]\d{4}\b', text)
    fields['date'] = match.group(0) if match else 'Not found'

    # Amount (₹ or RS in digits)
    match = re.search(r'(?:₹|Rs\.?)\s?[\d,]+\.\d{2}', text)
    fields['amount'] = match.group(0) if match else 'Not found'

    return fields

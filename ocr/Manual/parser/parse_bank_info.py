# run_ocr_parser.py

import cv2
import pytesseract
import re
import os
from PIL import Image

# -----------------------
# STEP 1: OCR Function
# -----------------------
def extract_text_from_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    text = pytesseract.image_to_string(thresh)
    return text

# -----------------------
# STEP 2: Parser Function
# -----------------------
def parse_banking_info(text):
    info = {}

    # Extract name
    name_match = re.search(r'Name[:\s]+([A-Z ]+)', text)
    if name_match:
        info['name'] = name_match.group(1).strip()

    # Extract account number
    acc_match = re.search(r'Account(?: No)?[:\s]*([\d]{9,20})', text)
    if acc_match:
        info['account_number'] = acc_match.group(1)

    # Extract IFSC
    ifsc_match = re.search(r'IFSC[:\s]*([A-Z]{4}0[A-Z0-9]{6})', text)
    if ifsc_match:
        info['ifsc'] = ifsc_match.group(1)

    # Extract balance
    balance_match = re.search(r'Balance[:\s]*₹?([0-9,]+)', text)
    if balance_match:
        info['balance'] = f"₹{balance_match.group(1)}"

    # Extract date
    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
    if date_match:
        info['date'] = date_match.group(1)

    return info

# -----------------------
# STEP 3: Run it
# -----------------------
if __name__ == "__main__":
    image_path = "templates/sample2.jpg"  # Replace with your own image path

    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        exit()

    print("\n[🔍 Performing OCR...]\n")
    raw_text = extract_text_from_image(image_path)
    print("[📄 Raw OCR Output]:\n")
    print(raw_text)

    print("\n[🧠 Parsing Extracted Data...]\n")
    structured = parse_banking_info(raw_text)
    if structured:
        for k, v in structured.items():
            print(f"{k.capitalize()}: {v}")
    else:
        print("No structured data found. Try another image or improve OCR output.")

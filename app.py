from ocr.extract_text import extract_text

if __name__ == "__main__":
    path = 'templates/sample2.jpg'  # add your image
    output = extract_text(path)
    print("=== Extracted Text ===")
    print(output)

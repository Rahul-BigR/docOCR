import os
from ocr.preprocess import preprocess_image
from ocr.extract import extract_text, extract_fields

cheque_folder = "dataset/cheques"
output_folder = "outputs"
os.makedirs(output_folder, exist_ok=True)

for fname in os.listdir(cheque_folder):
    if fname.endswith(".tif"):
        img_path = os.path.join(cheque_folder, fname)

        # Preprocess & OCR
        img = preprocess_image(img_path)
        text = extract_text(img)
        fields = extract_fields(text)

        # Save or print output
        print(f"\n--- {fname} ---")
        for k, v in fields.items():
            print(f"{k}: {v}")

        # Save as .txt or JSON
        with open(os.path.join(output_folder, fname.replace(".tif", ".txt")), "w") as f:
            f.write(text)

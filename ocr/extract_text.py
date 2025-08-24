
#import cv2
import pytesseract
from PIL import Image
from ocr.preprocesser import preprocess_image

def extract_text(image_path):
    
    #img = cv2.imread(image_path)
    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #_, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    img = preprocess_image(image_path)

    text = pytesseract.image_to_string(img)
    return text


#if __name__ == "__main__":
 #   path = "templates/sample2.jpg"  
  #  text = extract_text_from_image(path)
   # print("\n--- Extracted Text ---\n")
    #print(text)

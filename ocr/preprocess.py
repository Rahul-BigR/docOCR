import cv2

def preprocess_image(path):
    #img = cv2.GaussianBlur(img, (5, 5), 0)
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (1000, 1000))  # optional resize
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

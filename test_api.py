import cv2
import numpy as np
import requests

# Create a simple image with text
img = np.zeros((200, 400, 3), dtype=np.uint8)
img.fill(255)
cv2.putText(img, 'AI TEXT EXTRACTOR', (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
cv2.imwrite('test_image.jpg', img)

# Send to API
url = 'http://127.0.0.1:8000/api/upload'
files = {'file': open('test_image.jpg', 'rb')}
data = {'language': 'eng'}
try:
    response = requests.post(url, files=files, data=data)
    print("Status:", response.status_code)
    print("JSON:", response.json())
except Exception as e:
    print("Upload failed:", e)

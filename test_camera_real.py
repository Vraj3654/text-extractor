import urllib.request
import urllib.error
import json
import time
import base64
from PIL import Image, ImageDraw, ImageFont
import io

URL = "https://text-extractor-production-46b3.up.railway.app"

def req(path, data=None, token=None):
    req_obj = urllib.request.Request(f"{URL}{path}")
    if token:
        req_obj.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req_obj.add_header("Content-Type", "application/json")
        req_obj.data = json.dumps(data).encode("utf-8")
    
    try:
        with urllib.request.urlopen(req_obj) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def create_text_image():
    # Create a white image
    img = Image.new('RGB', (400, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Draw some large text
    d.text((50, 80), "HELLO WORLD THIS IS A TEST", fill=(0,0,0))
    
    # Save to memory as JPEG
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def test_camera_ocr():
    print(f"Testing {URL}...")
    
    username = f"testuser_{int(time.time())}"
    status, body = req("/api/register", data={"username": username, "password": "password"})
    print("Register:", status)
    
    login_data = f"username={username}&password=password".encode("utf-8")
    login_req = urllib.request.Request(f"{URL}/api/token", data=login_data)
    login_req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(login_req) as response:
        login_res = json.loads(response.read().decode("utf-8"))
    
    token = login_res["access_token"]
    
    b64_image = create_text_image()
    payload = {"image": f"data:image/jpeg;base64,{b64_image}"}
    
    print("Calling /api/camera-ocr with real text image...")
    status, body = req("/api/camera-ocr", data=payload, token=token)
    print("Camera OCR Response:", status)
    print("Camera OCR Text:", body)

if __name__ == "__main__":
    test_camera_ocr()

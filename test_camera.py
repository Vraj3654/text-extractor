import urllib.request
import urllib.error
import json
import time

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

def test_camera_ocr():
    print(f"Testing {URL}...")
    
    # 1. Register a test user
    username = f"testuser_{int(time.time())}"
    status, body = req("/api/register", data={"username": username, "password": "password"})
    print("Register:", status, body)
    
    # 2. Login to get token (application/x-www-form-urlencoded)
    # Wait, /api/token requires form-data
    login_data = f"username={username}&password=password".encode("utf-8")
    login_req = urllib.request.Request(f"{URL}/api/token", data=login_data)
    login_req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(login_req) as response:
        login_res = json.loads(response.read().decode("utf-8"))
    
    token = login_res["access_token"]
    
    # 3. Create a dummy base64 JPEG image (1x1 white pixel)
    b64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
    payload = {"image": f"data:image/jpeg;base64,{b64_image}"}
    
    # 4. Call camera OCR
    print("Calling /api/camera-ocr...")
    status, body = req("/api/camera-ocr", data=payload, token=token)
    print("Camera OCR Response:", status)
    print("Camera OCR Text:", body)

if __name__ == "__main__":
    test_camera_ocr()

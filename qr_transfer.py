import qrcode
import json
from key_storage import load_or_create_keys


def export_keys_to_qr(username):
    priv, pub = load_or_create_keys(f"{username}_keys.json")
    data = {"private": priv, "public": pub}
    qr = qrcode.make(json.dumps(data))
    filename = f"{username}_keys_qr.png"
    qr.save(filename)
    print(f"📦 QR code with keys saved to {filename}")


def import_keys_from_qr(image_path):
    import cv2
    detector = cv2.QRCodeDetector()
    img = cv2.imread(image_path)
    data, _, _ = detector.detectAndDecode(img)
    if not data:
        print("❌ No QR code found or unreadable.")
        return
    keys = json.loads(data)
    with open("imported_keys.json", "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2)
    print("✅ Keys imported and saved to imported_keys.json")

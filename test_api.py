#!/usr/bin/env python3
"""
📹 Kamera API Test Script
"""

import requests
import json
import time
import base64
from PIL import Image
import io

# API URL
API_URL = "http://localhost:8000"

def test_health():
    """Sağlık kontrolü"""
    print("🏥 Health check...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check hatası: {e}")
        return False

def test_status():
    """Kamera durumu"""
    print("\n📊 Kamera durumu...")
    try:
        response = requests.get(f"{API_URL}/api/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"❌ Status hatası: {e}")
        return None

def test_connect():
    """Kameraya bağlan"""
    print("\n🔗 Kameraya bağlanıyor...")
    config = {
        "ip_address": "192.168.1.102",
        "username": "manuco",
        "password": "manu0625",
        "rtsp_port": 554,
        "stream_path": "stream1"
    }
    
    try:
        response = requests.post(f"{API_URL}/api/connect", json=config)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()["success"]
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return False

def test_frame():
    """Frame al"""
    print("\n📸 Frame alınıyor...")
    try:
        response = requests.get(f"{API_URL}/api/frame")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data["success"] and data["frame"]:
                print("✅ Frame başarıyla alındı")
                
                # Base64'ü decode et ve kaydet
                img_data = base64.b64decode(data["frame"])
                img = Image.open(io.BytesIO(img_data))
                img.save("test_frame.jpg")
                print("💾 Frame 'test_frame.jpg' olarak kaydedildi")
                return True
            else:
                print(f"❌ Frame alınamadı: {data.get('error', 'Bilinmeyen hata')}")
                return False
        else:
            print(f"❌ HTTP hatası: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frame alma hatası: {e}")
        return False

def test_snapshot():
    """Fotoğraf çek"""
    print("\n📷 Fotoğraf çekiliyor...")
    try:
        response = requests.get(f"{API_URL}/api/snapshot")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()["success"]
    except Exception as e:
        print(f"❌ Fotoğraf çekme hatası: {e}")
        return False

def test_info():
    """Kamera bilgileri"""
    print("\nℹ️ Kamera bilgileri...")
    try:
        response = requests.get(f"{API_URL}/api/info")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Bilgi alma hatası: {e}")
        return False

def test_disconnect():
    """Bağlantıyı kes"""
    print("\n🔌 Bağlantı kesiliyor...")
    try:
        response = requests.get(f"{API_URL}/api/disconnect")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()["success"]
    except Exception as e:
        print(f"❌ Bağlantı kesme hatası: {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 Kamera API Test Başlatılıyor...")
    print("=" * 50)
    
    # Health check
    if not test_health():
        print("❌ API çalışmıyor!")
        return
    
    # İlk durum
    test_status()
    
    # Bağlan
    if test_connect():
        print("✅ Bağlantı başarılı!")
        
        # Durumu kontrol et
        time.sleep(2)
        test_status()
        
        # Frame al
        if test_frame():
            print("✅ Frame testi başarılı!")
        
        # Fotoğraf çek
        if test_snapshot():
            print("✅ Fotoğraf testi başarılı!")
        
        # Bilgileri al
        test_info()
        
        # Bağlantıyı kes
        test_disconnect()
    else:
        print("❌ Bağlantı başarısız!")
    
    print("\n" + "=" * 50)
    print("🏁 Test tamamlandı!")

if __name__ == "__main__":
    main() 
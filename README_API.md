# 📹 Kamera API - NextJS Entegrasyonu

Bu API, NextJS web uygulamanızda kamera görüntüsünü kullanabilmenizi sağlar.

## 🚀 Özellikler

- **FastAPI** tabanlı modern API
- **RTSP** kamera desteği
- **Base64** görüntü formatı
- **CORS** desteği (NextJS için)
- **Docker** containerization
- **Otomatik bağlantı** yönetimi

## 📋 API Endpoints

### 🔗 Temel Endpoints

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/` | GET | API durumu |
| `/health` | GET | Sağlık kontrolü |
| `/docs` | GET | Swagger dokümantasyonu |

### 📹 Kamera Endpoints

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/api/connect` | POST | Kameraya bağlan |
| `/api/disconnect` | GET | Bağlantıyı kes |
| `/api/status` | GET | Kamera durumu |
| `/api/frame` | GET | Canlı görüntü (base64) |
| `/api/snapshot` | GET | Fotoğraf çek |
| `/api/info` | GET | Kamera bilgileri |

## 🛠️ Kurulum

### 1. **Docker ile (Önerilen)**

```bash
# Docker image'ı build et
docker build -t camera-api .

# Container'ı çalıştır
docker run -p 8000:8000 camera-api
```

### 2. **Docker Compose ile**

```bash
# Servisi başlat
docker-compose up -d

# Logları izle
docker-compose logs -f
```

### 3. **Manuel Kurulum**

```bash
# Bağımlılıkları yükle
pip install -r api/requirements.txt

# API'yi başlat
cd api && python main.py
```

## 🔧 Environment Variables

```bash
CAMERA_IP=192.168.1.102
CAMERA_USERNAME=manuco
CAMERA_PASSWORD=manu0625
```

## 📱 NextJS Entegrasyonu

### 1. **API URL'sini Ayarlayın**

```javascript
// .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. **Kamera Hook'u Oluşturun**

```javascript
// hooks/useCamera.js
import { useState, useEffect } from 'react';

export const useCamera = () => {
  const [frame, setFrame] = useState(null);
  const [status, setStatus] = useState({ connected: false, streaming: false });
  const [loading, setLoading] = useState(true);

  const fetchFrame = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/frame`);
      const data = await response.json();
      
      if (data.success && data.frame) {
        setFrame(`data:image/jpeg;base64,${data.frame}`);
      }
    } catch (error) {
      console.error('Frame alma hatası:', error);
    }
  };

  const checkStatus = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/status`);
      const data = await response.json();
      setStatus(data);
      setLoading(false);
    } catch (error) {
      console.error('Durum kontrolü hatası:', error);
    }
  };

  const takeSnapshot = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/snapshot`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Fotoğraf çekme hatası:', error);
    }
  };

  useEffect(() => {
    checkStatus();
    const statusInterval = setInterval(checkStatus, 2000);
    
    return () => clearInterval(statusInterval);
  }, []);

  useEffect(() => {
    if (status.connected && status.streaming) {
      const frameInterval = setInterval(fetchFrame, 100);
      return () => clearInterval(frameInterval);
    }
  }, [status.connected, status.streaming]);

  return { frame, status, loading, takeSnapshot };
};
```

### 3. **React Component'i**

```jsx
// components/CameraViewer.jsx
import { useCamera } from '../hooks/useCamera';

export const CameraViewer = () => {
  const { frame, status, loading, takeSnapshot } = useCamera();

  if (loading) {
    return <div>Yükleniyor...</div>;
  }

  return (
    <div className="camera-viewer">
      <div className="status">
        Durum: {status.connected ? 'Bağlı' : 'Bağlı Değil'}
        {status.streaming && ' - Yayın Aktif'}
      </div>
      
      {frame ? (
        <img 
          src={frame} 
          alt="Kamera Görüntüsü" 
          className="camera-frame"
        />
      ) : (
        <div className="no-frame">
          Görüntü yok
        </div>
      )}
      
      <button onClick={takeSnapshot}>
        Fotoğraf Çek
      </button>
    </div>
  );
};
```

### 4. **CSS Stilleri**

```css
/* styles/camera.css */
.camera-viewer {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.camera-frame {
  width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.status {
  margin-bottom: 20px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
}

.no-frame {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border-radius: 8px;
  color: #666;
}
```

## 🌐 Deployment

### **Vercel + Railway**

1. **API'yi Railway'e deploy edin:**
   ```bash
   # Railway CLI ile
   railway login
   railway init
   railway up
   ```

2. **NextJS'i Vercel'e deploy edin:**
   ```bash
   # Vercel CLI ile
   vercel
   ```

3. **Environment variables'ı ayarlayın:**
   - Vercel'de `NEXT_PUBLIC_API_URL` = Railway URL'si

### **Docker + VPS**

1. **VPS'e Docker kurun**
2. **Image'ı push edin:**
   ```bash
   docker tag camera-api your-registry/camera-api
   docker push your-registry/camera-api
   ```
3. **VPS'te çalıştırın:**
   ```bash
   docker run -d -p 8000:8000 your-registry/camera-api
   ```

## 🔒 Güvenlik

- **CORS** ayarlarını production'da sınırlayın
- **API Key** ekleyin
- **Rate Limiting** uygulayın
- **HTTPS** kullanın

## 📊 Monitoring

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

## 🐛 Sorun Giderme

### **Bağlantı Sorunları**
- Kamera IP'sini kontrol edin
- RTSP portunu kontrol edin
- Ağ bağlantısını test edin

### **Performans Sorunları**
- Frame rate'i düşürün
- Görüntü kalitesini azaltın
- Buffer boyutunu artırın

Bu API ile NextJS uygulamanızda profesyonel kamera entegrasyonu yapabilirsiniz! 🎉 
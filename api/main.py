from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import cv2
import numpy as np
import base64
import threading
import time
import logging
import os
from typing import Optional, Dict, Any
import urllib3

# SSL uyarılarını devre dışı bırak
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kamera API",
    description="NextJS için kamera görüntü API'si",
    version="1.0.0"
)

# CORS ayarları (NextJS için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik domain yazın
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kamera sınıfı
class RTSPCamera:
    def __init__(self, ip_address: str, username: str, password: str, rtsp_port: int = 554, stream_path: str = "stream1"):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.rtsp_port = rtsp_port
        self.stream_path = stream_path
        
        # RTSP URL'ini oluştur
        self.rtsp_url = f"rtsp://{username}:{password}@{ip_address}:{rtsp_port}/{stream_path}?tcp"
        
        self.cap = None
        self.is_connected = False
        self.current_frame = None
        self.stream_thread = None
        self.is_streaming = False
        self.frame_lock = threading.Lock()
        
    def connect(self) -> bool:
        """RTSP bağlantısını kur"""
        try:
            logger.info(f"RTSP bağlantısı kuruluyor: {self.ip_address}")
            
            # OpenCV VideoCapture ile RTSP bağlantısı
            self.cap = cv2.VideoCapture(self.rtsp_url)
            
            # RTSP optimizasyonları
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
            
            if not self.cap.isOpened():
                logger.error("RTSP bağlantısı açılamadı")
                return False
            
            # Bağlantıyı test et
            ret, frame = self.cap.read()
            if not ret:
                logger.error("RTSP stream'den frame alınamadı")
                return False
            
            self.is_connected = True
            logger.info("RTSP bağlantısı başarılı!")
            return True
            
        except Exception as e:
            logger.error(f"RTSP bağlantısı başarısız: {str(e)}")
            self.is_connected = False
            return False
    
    def start_stream(self) -> bool:
        """Canlı yayın başlat"""
        if not self.is_connected:
            logger.error("RTSP bağlı değil!")
            return False
        
        if self.is_streaming:
            logger.info("Yayın zaten aktif!")
            return True
        
        self.is_streaming = True
        self.stream_thread = threading.Thread(target=self._stream_worker)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        logger.info("RTSP yayın başlatıldı!")
        return True
    
    def stop_stream(self):
        """Canlı yayını durdur"""
        self.is_streaming = False
        if self.stream_thread:
            self.stream_thread.join(timeout=2)
        logger.info("RTSP yayın durduruldu!")
    
    def _stream_worker(self):
        """Yayın işçi thread'i"""
        while self.is_streaming:
            try:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        # Frame'i yeniden boyutlandır
                        frame = cv2.resize(frame, (640, 480))
                        
                        with self.frame_lock:
                            self.current_frame = frame
                    else:
                        logger.warning("Frame alınamadı, bağlantıyı yeniden kuruyor...")
                        self._reconnect()
                else:
                    logger.error("RTSP bağlantısı kapalı")
                    self._reconnect()
                    
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                logger.error(f"Frame alma hatası: {str(e)}")
                time.sleep(0.5)
    
    def _reconnect(self):
        """Bağlantıyı yeniden kur"""
        try:
            if self.cap:
                self.cap.release()
            
            self.cap = cv2.VideoCapture(self.rtsp_url)
            if not self.cap.isOpened():
                logger.error("Yeniden bağlantı başarısız")
                self.is_connected = False
            else:
                logger.info("Yeniden bağlantı başarılı")
                self.is_connected = True
                
        except Exception as e:
            logger.error(f"Yeniden bağlantı hatası: {str(e)}")
            self.is_connected = False
    
    def get_current_frame(self):
        """Mevcut frame'i döndür"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def get_frame_as_base64(self) -> Optional[str]:
        """Frame'i base64 formatında döndür"""
        frame = self.get_current_frame()
        if frame is None:
            return None
        
        try:
            # BGR'den RGB'ye çevir
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # JPEG'e çevir
            _, buffer = cv2.imencode('.jpg', rgb_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_str = base64.b64encode(buffer).decode()
            
            return img_str
        except Exception as e:
            logger.error(f"Frame base64 dönüşüm hatası: {str(e)}")
            return None
    
    def take_snapshot(self, filename: Optional[str] = None) -> Optional[str]:
        """Anlık fotoğraf çek"""
        if not self.is_connected:
            logger.error("RTSP bağlı değil!")
            return None
        
        try:
            if filename is None:
                filename = f"snapshot_{int(time.time())}.jpg"
            
            frame = self.get_current_frame()
            if frame is not None:
                cv2.imwrite(filename, frame)
                logger.info(f"Fotoğraf kaydedildi: {filename}")
                return filename
            else:
                logger.error("Frame mevcut değil")
                return None
            
        except Exception as e:
            logger.error(f"Fotoğraf çekme hatası: {str(e)}")
            return None
    
    def get_camera_info(self) -> Dict[str, Any]:
        """Kamera bilgilerini al"""
        return {
            "ip_address": self.ip_address,
            "username": self.username,
            "rtsp_url": f"rtsp://***:***@{self.ip_address}:{self.rtsp_port}/{self.stream_path}",
            "connection_type": "RTSP",
            "stream_path": self.stream_path,
            "is_connected": self.is_connected,
            "is_streaming": self.is_streaming
        }
    
    def disconnect(self):
        """RTSP bağlantısını kes"""
        self.stop_stream()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.is_connected = False
        logger.info("RTSP bağlantısı kesildi!")

# Global kamera instance
camera = None
camera_lock = threading.Lock()

# Pydantic modelleri
class CameraConfig(BaseModel):
    ip_address: str
    username: str
    password: str
    rtsp_port: int = 554
    stream_path: str = "stream1"

class ConnectionResponse(BaseModel):
    success: bool
    message: str
    camera_info: Optional[Dict[str, Any]] = None

class FrameResponse(BaseModel):
    success: bool
    frame: Optional[str] = None
    timestamp: float
    error: Optional[str] = None

# API Routes
@app.get("/")
async def root():
    """Ana sayfa"""
    return {"message": "Kamera API v1.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    """Sağlık kontrolü"""
    global camera
    return {
        "status": "healthy",
        "camera_connected": camera.is_connected if camera else False,
        "camera_streaming": camera.is_streaming if camera else False,
        "timestamp": time.time()
    }

@app.post("/api/connect", response_model=ConnectionResponse)
async def connect_camera(config: CameraConfig):
    """Kameraya bağlan"""
    global camera
    
    with camera_lock:
        # Mevcut bağlantıyı kes
        if camera:
            camera.disconnect()
            camera = None
        
        # Yeni bağlantı oluştur
        camera = RTSPCamera(
            config.ip_address,
            config.username,
            config.password,
            config.rtsp_port,
            config.stream_path
        )
        
        if camera.connect():
            camera.start_stream()
            return ConnectionResponse(
                success=True,
                message="Kamera bağlantısı başarılı",
                camera_info=camera.get_camera_info()
            )
        else:
            return ConnectionResponse(
                success=False,
                message="Kamera bağlantısı başarısız"
            )

@app.get("/api/disconnect")
async def disconnect_camera():
    """Kameradan bağlantıyı kes"""
    global camera
    
    with camera_lock:
        if camera:
            camera.disconnect()
            camera = None
    
    return {"success": True, "message": "Kamera bağlantısı kesildi"}

@app.get("/api/status")
async def get_status():
    """Kamera durumunu al"""
    global camera
    
    if camera and camera.is_connected:
        return {
            "connected": True,
            "streaming": camera.is_streaming,
            "has_frame": camera.get_current_frame() is not None,
            "camera_info": camera.get_camera_info()
        }
    else:
        return {
            "connected": False,
            "streaming": False,
            "has_frame": False,
            "camera_info": None
        }

@app.get("/api/frame", response_model=FrameResponse)
async def get_frame():
    """Mevcut frame'i base64 formatında döndür"""
    global camera
    
    if camera and camera.is_connected:
        frame_b64 = camera.get_frame_as_base64()
        if frame_b64:
            return FrameResponse(
                success=True,
                frame=frame_b64,
                timestamp=time.time()
            )
        else:
            return FrameResponse(
                success=False,
                error="Frame mevcut değil",
                timestamp=time.time()
            )
    else:
        return FrameResponse(
            success=False,
            error="Kamera bağlı değil",
            timestamp=time.time()
        )

@app.get("/api/snapshot")
async def take_snapshot():
    """Anlık fotoğraf çek"""
    global camera
    
    if camera and camera.is_connected:
        filename = camera.take_snapshot()
        if filename:
            return {"success": True, "filename": filename}
        else:
            raise HTTPException(status_code=500, detail="Fotoğraf çekilemedi")
    else:
        raise HTTPException(status_code=400, detail="Kamera bağlı değil")

@app.get("/api/info")
async def get_camera_info():
    """Kamera bilgilerini al"""
    global camera
    
    if camera and camera.is_connected:
        return {"success": True, "info": camera.get_camera_info()}
    else:
        raise HTTPException(status_code=400, detail="Kamera bağlı değil")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında otomatik bağlantı"""
    global camera
    
    # Environment variables'dan kamera bilgilerini al
    camera_ip = os.getenv("CAMERA_IP", "192.168.1.102")
    camera_username = os.getenv("CAMERA_USERNAME", "manuco")
    camera_password = os.getenv("CAMERA_PASSWORD", "manu0625")
    
    logger.info(f"Otomatik kamera bağlantısı: {camera_ip}")
    
    camera = RTSPCamera(camera_ip, camera_username, camera_password)
    if camera.connect():
        camera.start_stream()
        logger.info("Otomatik kamera bağlantısı başarılı")
    else:
        logger.warning("Otomatik kamera bağlantısı başarısız")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapanırken bağlantıyı kes"""
    global camera
    
    if camera:
        camera.disconnect()
        logger.info("Kamera bağlantısı kapatıldı")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
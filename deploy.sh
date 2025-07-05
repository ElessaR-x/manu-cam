#!/bin/bash

# 🚀 Kamera API Deployment Script

echo "📹 Kamera API Deployment başlatılıyor..."

# Docker image'ı build et
echo "🔨 Docker image build ediliyor..."
docker build -t camera-api .

# Eski container'ı durdur ve sil
echo "🛑 Eski container durduruluyor..."
docker stop camera-api-container 2>/dev/null || true
docker rm camera-api-container 2>/dev/null || true

# Yeni container'ı başlat
echo "🚀 Yeni container başlatılıyor..."
docker run -d \
  --name camera-api-container \
  -p 8000:8000 \
  -e CAMERA_IP=192.168.1.102 \
  -e CAMERA_USERNAME=manuco \
  -e CAMERA_PASSWORD=manu0625 \
  -v $(pwd)/snapshots:/app/snapshots \
  --restart unless-stopped \
  camera-api

# Container durumunu kontrol et
echo "📊 Container durumu kontrol ediliyor..."
sleep 5
docker ps | grep camera-api-container

# Health check
echo "🏥 Health check yapılıyor..."
curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "Health check başarısız"

echo "✅ Deployment tamamlandı!"
echo "🌐 API URL: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "📊 Health: http://localhost:8000/health" 
# 🤖 AI-Server Project - Центр ИИ при ЖезУ

## Сводный документ для работы через Claude Code

---

## 📋 Общая информация

| Параметр | Значение |
|----------|----------|
| **Проект** | Центр искусственного интеллекта при ЖезУ им. О.А. Байконурова |
| **Бюджет** | 11.2 млн ₸ |
| **Город** | Жезказган, Казахстан |
| **Партнёры** | Ulytau HUB (Каратаев Алибек), Alem.Cloud |

---

## 🖥️ Технические характеристики сервера

### Оборудование

| Компонент | Модель/Характеристики |
|-----------|----------------------|
| **GPU** | NVIDIA GeForce RTX 5090 (32 GB VRAM) |
| **CPU** | Intel Core i9-13900KF |
| **RAM** | 128 GB DDR5 |
| **Storage** | 4 TB NVMe SSD (MSI M580) |
| **Motherboard** | MSI MPG Z690 EDGE WIFI (MS-7D31) |

### Операционная система

| Параметр | Значение |
|----------|----------|
| **ОС** | Ubuntu 24.04.4 LTS (Server) |
| **Kernel** | 6.8.0-101-generic x86_64 |
| **Hostname** | ai-server |
| **Dual-boot** | Windows 11 (300 GB) + Ubuntu (3.3 TB) |

### Драйверы и CUDA

| Компонент | Версия |
|-----------|--------|
| **NVIDIA Driver** | 590.48.01 |
| **CUDA Version** | 13.1 |

---

## 🌐 Сетевая конфигурация

### IP-адреса

| Тип | Адрес |
|-----|-------|
| **Локальный IP (LAN)** | 192.168.50.13 |
| **Tailscale IP (VPN)** | 100.118.110.5 |
| **Gateway** | 192.168.50.2 |
| **Subnet** | 192.168.50.0/24 |

### SSH доступ

```bash
# Через Tailscale (из любой точки мира)
ssh ubuntu@100.118.110.5

# Через локальную сеть
ssh ubuntu@192.168.50.13
```

**Пользователь:** `ubuntu`
**Пароль:** (установлен при инсталляции Ubuntu)

---

## 🐳 Docker сервисы

### Расположение проекта

```
/home/ubuntu/ai-server/
├── docker-compose.yml
├── ollama/
├── open-webui/
├── whisper/
├── piper/
├── comfyui/
└── voice-assistant/
```

### Запущенные контейнеры

| Сервис | Образ | Порт | Назначение |
|--------|-------|------|------------|
| **ollama** | ollama/ollama:latest | 11434 | LLM движок |
| **open-webui** | ghcr.io/open-webui/open-webui:main | 3000 | Веб-интерфейс чата |
| **whisper** | fedirz/faster-whisper-server:latest-cuda | 9000 | Распознавание речи (STT) |
| **piper** | rhasspy/wyoming-piper:latest | 5500 | Синтез речи (TTS) |
| **comfyui** | ghcr.io/ai-dock/comfyui:latest | 8188 | Генерация изображений |
| **voice-assistant** | ghcr.io/open-webui/open-webui:main | 3002 | Голосовой ассистент |

### URL-адреса сервисов

| Сервис | URL |
|--------|-----|
| **Open WebUI (чат)** | http://100.118.110.5:3000 |
| **Voice Assistant** | http://100.118.110.5:3002 |
| **ComfyUI** | http://100.118.110.5:8188 |
| **Whisper API docs** | http://100.118.110.5:9000/docs |
| **Ollama API** | http://100.118.110.5:11434 |
| **Perplexica (AI-поиск)** | http://100.118.110.5:3001 |

---

## 🧠 Установленные LLM модели

```bash
docker exec ollama ollama list
```

| Модель | Размер | Назначение |
|--------|--------|------------|
| **qwen2.5:32b** | 19 GB | Основной чат, русский язык ⭐ |
| **deepseek-coder-v2:16b** | 8.9 GB | Программирование |
| **llama3.1:8b** | 4.9 GB | Быстрые задачи |
| **nomic-embed-text** | 274 MB | RAG / embeddings |

**Общий размер:** ~33 GB

---

## 🔧 docker-compose.yml (актуальная версия)

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports: ["11434:11434"]
    volumes: ["./ollama:/root/.ollama"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: unless-stopped
    ports: ["3000:8080"]
    volumes: ["./open-webui:/app/backend/data"]
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_AUTH=true
    depends_on: [ollama]

  whisper:
    image: fedirz/faster-whisper-server:latest-cuda
    container_name: whisper
    restart: unless-stopped
    ports: ["9000:8000"]
    environment:
      - WHISPER__MODEL=Systran/faster-whisper-large-v3
      - WHISPER__INFERENCE_DEVICE=cuda
      - WHISPER__COMPUTE_TYPE=float16
    volumes:
      - ./whisper/models:/root/.cache/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  piper:
    image: rhasspy/wyoming-piper:latest
    container_name: piper
    restart: unless-stopped
    ports: ["5500:10200"]
    volumes: ["./piper/data:/data"]
    command: --voice ru_RU-irina-medium

  comfyui:
    image: ghcr.io/ai-dock/comfyui:latest
    container_name: comfyui
    restart: unless-stopped
    ports: ["8188:8188"]
    volumes:
      - ./comfyui:/workspace
    environment:
      - CLI_ARGS=--listen
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  voice-assistant:
    image: ghcr.io/open-webui/open-webui:main
    container_name: voice-assistant
    restart: unless-stopped
    ports: ["3002:8080"]
    volumes: ["./voice-assistant:/app/backend/data"]
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - AUDIO_STT_ENGINE=openai
      - AUDIO_STT_OPENAI_API_BASE_URL=http://whisper:8000/v1
      - AUDIO_STT_OPENAI_API_KEY=sk-111
      - AUDIO_STT_MODEL=Systran/faster-whisper-large-v3
      - WEBUI_AUTH=false
    depends_on: [ollama, whisper]
```

---

## ⚠️ Текущие проблемы (требуют решения)

### 1. Голосовой ввод не работает

**Симптомы:**
- Ошибка `Transcription failed` в браузере
- HTTP 400 Bad Request при отправке аудио

**Возможные причины:**
- Неправильная конфигурация STT в Open WebUI
- Проблемы с сетью между контейнерами
- CORS или другие ограничения браузера

**Диагностика:**
```bash
# Логи Whisper
docker logs whisper --tail 50

# Логи Voice Assistant  
docker logs voice-assistant --tail 50

# Тест API Whisper
curl http://localhost:9000/v1/models

# Тест связи между контейнерами
docker exec voice-assistant curl -s http://whisper:8000/v1/models
```

### 2. Требуется HTTPS для микрофона

**Проблема:** Браузер блокирует доступ к микрофону на HTTP

**Временное решение (Chrome):**
1. Открыть `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
2. Добавить: `http://100.118.110.5:3002,http://100.118.110.5:3000`
3. Включить → Relaunch

**Постоянное решение:**
- Настроить SSL через Tailscale или Cloudflare Tunnel

---

## 📝 Полезные команды

### Управление Docker

```bash
cd ~/ai-server

# Статус сервисов
docker compose ps

# Перезапуск всех сервисов
docker compose down && docker compose up -d

# Перезапуск конкретного сервиса
docker compose up -d whisper --force-recreate

# Логи сервиса
docker logs whisper --tail 100 -f

# Обновление образов
docker compose pull && docker compose up -d
```

### Мониторинг GPU

```bash
# Текущее состояние
nvidia-smi

# Мониторинг в реальном времени
watch -n 1 nvidia-smi

# Краткий вывод
nvidia-smi --query-gpu=name,memory.used,memory.total,temperature.gpu --format=csv
```

### Управление моделями Ollama

```bash
# Список моделей
docker exec ollama ollama list

# Скачать модель
docker exec ollama ollama pull qwen2.5:72b

# Удалить модель
docker exec ollama ollama rm model_name

# Запустить модель интерактивно
docker exec -it ollama ollama run qwen2.5:32b
```

### Системные команды

```bash
# Дисковое пространство
df -h

# Память
free -h

# Процессы
htop

# Перезагрузка
sudo reboot
```

---

## 📂 Связанные файлы проекта

| Файл | Расположение | Описание |
|------|--------------|----------|
| **Дорожная карта** | /mnt/user-data/uploads/Дорожная_карта_Центр_ИИ.docx | План развития Feb-Apr 2026 |
| **Концепция** | /mnt/user-data/uploads/Концепция_развития_Центра_ИИ__3_.docx | Полная концепция проекта |
| **Должностная инструкция** | /mnt/user-data/outputs/Должностная_инструкция_Руководитель_Центра_ИИ.docx | ДИ руководителя |
| **Deploy Guide** | /mnt/user-data/uploads/AI-Server-Deploy-Guide.docx | Инструкция по развёртыванию |

---

## 🎯 KPI проекта (Q1 2026)

| Метрика | Целевое значение |
|---------|------------------|
| AI-решения развёрнуты | 2+ |
| Fine-tuned модели | 2+ |
| Участники сообщества | 5+ |
| Мероприятия с Ulytau HUB | 2+ |
| Удовлетворённость пользователей | 80%+ |

---

## 🚀 Следующие шаги

1. **Исправить голосовой ввод (STT)** - диагностировать и настроить связь Whisper ↔ Open WebUI
2. **Настроить TTS (Piper)** - интегрировать синтез речи на русском
3. **Настроить HTTPS** - для работы микрофона без chrome://flags
4. **Скачать модели для ComfyUI** - Stable Diffusion XL / Flux
5. **Настроить RAG** - загрузка документов в Open WebUI
6. **Fine-tuning** - дообучение моделей на данных университета

---

## 👤 Контакты

**Проект:** Центр ИИ при ЖезУ
**Партнёр:** Ulytau HUB (Каратаев Алибек)
**Облачный партнёр:** Alem.Cloud

---

*Документ создан: Март 2026*
*Последнее обновление: 09.03.2026*

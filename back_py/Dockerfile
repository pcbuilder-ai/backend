FROM python:3.11-slim

WORKDIR /app

# Chrome + 필수 패키지 설치 (apt-key 안 씀)
RUN apt-get update && apt-get install -y wget gnupg unzip curl && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Selenium에서 Chrome 실행 시 필요한 환경변수
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PATH="/usr/local/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12

USER root

# Install Tor and Proxychains
RUN apt-get update && \
    apt-get install -y tor proxychains-ng && \
    rm -rf /var/lib/apt/lists/*

# Install Chromium runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


RUN apt-get install python3 -y

COPY . .

# Install Python dependencies + playwright
RUN pip install -r requirements.txt --break-system-packages
RUN playwright install chromium

# Configure Tor
RUN echo "SOCKSPort 9050"    >> /etc/tor/torrc && \
    echo "ControlPort 9051"  >> /etc/tor/torrc && \
    echo "Log notice stdout" >> /etc/tor/torrc

CMD tor & \
    python3 main.py
FROM python:3.11-slim

# Install FFmpeg (required for yt-dlp to convert audio/video)
# Install curl + unzip for Deno installation
RUN apt-get update && apt-get install -y ffmpeg curl unzip && rm -rf /var/lib/apt/lists/*

# Install Deno (required by yt-dlp for YouTube JS challenge solving)
RUN curl -fsSL https://deno.land/install.sh | sh
ENV DENO_INSTALL="/root/.deno"
ENV PATH="${DENO_INSTALL}/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Also install yt-dlp nightly for latest YouTube fixes
RUN pip install --no-cache-dir -U --pre "yt-dlp[default]"

COPY . .

# Run the FastAPI server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "10000"]

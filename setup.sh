#!/bin/bash
set -e

echo "======================================"
echo "  CUSTOM HARNESS - SETUP"
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# 1. Check Python
log "Checking Python 3.10+..."
python3 --version || err "Python3 not found. Install: sudo apt install python3"

# 2. Check FFmpeg
log "Checking FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    warn "FFmpeg not found. Installing..."
    sudo apt-get update -q && sudo apt-get install -y ffmpeg
fi
log "FFmpeg: $(ffmpeg -version 2>&1 | head -1)"

# 3. Install Python deps
log "Installing Python dependencies..."
pip3 install -q -r requirements.txt

# 4. Install Ollama
if ! command -v ollama &> /dev/null; then
    log "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    log "Ollama already installed: $(ollama --version)"
fi

# 5. Pull Ollama model
log "Pulling Llama 3.1:8b model (this may take a while)..."
ollama serve &> /dev/null &
sleep 3
ollama pull llama3.1:8b
log "Model ready!"

# 6. Download font
log "Downloading fonts..."
FONT_DIR="assets/fonts"
mkdir -p $FONT_DIR

# Download Montserrat Bold (viral video font)
wget -q "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf" \
    -O "$FONT_DIR/bold.ttf" 2>/dev/null || \
    cp /usr/share/fonts/truetype/freefont/FreeSansBold.ttf "$FONT_DIR/bold.ttf" 2>/dev/null || \
    warn "Font download failed, will use system font"

wget -q "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Regular.ttf" \
    -O "$FONT_DIR/regular.ttf" 2>/dev/null || \
    cp /usr/share/fonts/truetype/freefont/FreeSans.ttf "$FONT_DIR/regular.ttf" 2>/dev/null || \
    warn "Regular font download failed"

# 7. Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    warn "Created .env file - Fill in your API keys!"
fi

# 8. Create dirs
mkdir -p output/videos logs

echo ""
echo "======================================"
log "SETUP COMPLETE!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Fill in your API keys in .env"
echo "  2. Run: python3 main.py          (single run)"
echo "  3. Run: python3 main.py --daemon  (auto scheduler)"
echo ""
echo "Test run (no publishing):"
echo "  python3 main.py --test"
echo ""

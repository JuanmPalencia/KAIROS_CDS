#!/bin/bash

################################################################################
# KAIROS CDS - Unified Setup & Run Script (Linux/macOS)
################################################################################

clear

cat << "EOF"

  ╔════════════════════════════════════════════════════════════════╗
  ║                   KAIROS CDS v1.0.0                            ║
  ║            Emergency Fleet Management Digital Twin            ║
  ╚════════════════════════════════════════════════════════════════╝

EOF

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi
echo "✅ Docker is ready"

# 1. Start Docker Compose
echo ""
echo "Starting services (PostgreSQL, Redis, Backend, Frontend)..."
docker compose up -d --build
if [ $? -ne 0 ]; then
    echo "❌ Failed to start Docker Compose"
    exit 1
fi
echo "✅ Services started"

# 2. Wait for Backend (max 60 seconds)
echo ""
echo "Waiting for API to be ready..."
ATTEMPTS=0
while [ $ATTEMPTS -lt 30 ]; do
    if curl -s http://localhost:5001/docs > /dev/null 2>&1; then
        break
    fi
    ATTEMPTS=$((ATTEMPTS + 1))
    echo "  Attempt $ATTEMPTS/30..."
    sleep 2
done

if [ $ATTEMPTS -eq 30 ]; then
    echo "❌ Backend timeout. Check logs: docker compose logs backend"
    exit 1
fi
echo "✅ API is ready"

# 3. Initialize data
echo ""
echo "Initializing data..."
curl -s -X POST http://localhost:5001/api/auth/init-admin \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" > /dev/null 2>&1
echo "✅ Data initialized"

# 4. Start auto-generation
echo ""
echo "Starting incident auto-generation..."
curl -s -X POST "http://localhost:5001/simulation/auto-generate/start?interval=15" > /dev/null 2>&1
curl -s -X POST "http://localhost:5001/simulation/lifecycle/start" > /dev/null 2>&1
echo "✅ Auto-generation active"

# 5. Summary
cat << "EOF"

  ╔════════════════════════════════════════════════════════════════╗
  ║                    SETUP COMPLETE! ✅                          ║
  ╠════════════════════════════════════════════════════════════════╣
  ║  Frontend ................. http://localhost:5173             ║
  ║  API ....................... http://localhost:5001             ║
  ║  API Docs .................. http://localhost:5001/docs       ║
  ║                                                                ║
  ║  Credentials:                                                  ║
  ║    admin    / admin123                                         ║
  ║    operator / operator123                                      ║
  ║    doctor  / doctor123                                         ║
  ║    viewer  / viewer123                                         ║
  ╚════════════════════════════════════════════════════════════════╝

  📌 To restart services: docker compose restart
  📌 To view logs:        docker compose logs -f
  📌 To stop:             docker compose down

EOF

docker rm -f flask-app || true
docker build -t flask-app .
docker compose up -d
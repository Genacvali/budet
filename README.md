# Budget PWA (FastAPI + SvelteKit SPA)

## Backend
```bash
cd backend
python3 -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Frontend
```bash
cd frontend
npm i
npm run build
```

## Deploy (server)

```bash
# Backend service
sudo cp deploy/budget-api.service /etc/systemd/system/budget-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now budget-api
systemctl status budget-api --no-pager

# Frontend publish
sudo mkdir -p /opt/budget-pwa/frontend
sudo rsync -a --delete frontend/build/ /opt/budget-pwa/frontend/

# Nginx
sudo cp deploy/nginx-budget.conf /etc/nginx/conf.d/budget.conf
sudo nginx -t && sudo systemctl reload nginx
sudo setsebool -P httpd_can_network_connect 1
sudo firewall-cmd --add-service=http --permanent && sudo firewall-cmd --reload
```

DNS: создайте A-запись mikvabadget.com → ваш публичный IP.
Откройте: http://mikvabadget.com
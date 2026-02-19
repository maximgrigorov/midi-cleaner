DEPLOY_HOST  := alma
DEPLOY_USER  := mgrigorov
DEPLOY_DIR   := /home/$(DEPLOY_USER)/midi-cleaner
SSH          := ssh $(DEPLOY_USER)@$(DEPLOY_HOST)

.PHONY: dev dev-frontend dev-backend build up down restart logs logs-backend logs-frontend clean install install-backend install-frontend test deploy

# ── Local development ──────────────────────────────────────────────
dev-backend:
	cd backend && pip install -q -r requirements.txt && python app.py

dev-frontend:
	cd frontend && npm run dev

dev:
	make -j2 dev-backend dev-frontend

# ── Podman build & deploy (local) ─────────────────────────────────
build:
	podman-compose build

up:
	podman-compose up -d

down:
	podman-compose down

restart:
	podman-compose restart

logs:
	podman-compose logs -f

logs-backend:
	podman-compose logs -f backend

logs-frontend:
	podman-compose logs -f frontend

# ── Install ────────────────────────────────────────────────────────
install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend

# ── Test ───────────────────────────────────────────────────────────
test:
	cd backend && python -m pytest tests/ -v

# ── Remote deploy to alma ──────────────────────────────────────────
deploy:
	@echo "==> Syncing project to $(DEPLOY_HOST):$(DEPLOY_DIR)..."
	$(SSH) "mkdir -p $(DEPLOY_DIR)"
	rsync -avz --delete \
		--exclude '__pycache__' \
		--exclude '*.pyc' \
		--exclude '.git' \
		--exclude '.DS_Store' \
		--exclude '.pytest_cache' \
		--exclude 'node_modules' \
		--exclude 'frontend/dist' \
		--exclude 'uploads/' \
		--exclude 'standalone.html' \
		--exclude 'backend/static' \
		--exclude 'backend/templates' \
		./ $(DEPLOY_USER)@$(DEPLOY_HOST):$(DEPLOY_DIR)/

	@echo "==> Building and starting containers on $(DEPLOY_HOST) as $(DEPLOY_USER)..."
	$(SSH) "cd $(DEPLOY_DIR) && \
		podman-compose down 2>/dev/null || true && \
		podman-compose build && \
		podman-compose up -d"

	@echo ""
	@echo "✓ Deployed! MIDI Cleaner running at http://$(DEPLOY_HOST):8080"
	@echo "  Containers run as $(DEPLOY_USER) (rootless podman)."

# ── Cleanup ────────────────────────────────────────────────────────
clean:
	podman-compose down -v
	podman image prune -f

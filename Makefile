IMAGE_NAME   := midi-cleaner
CONTAINER_NAME := midi-cleaner
LOCAL_PORT   := 5000
REMOTE_PORT  := 8040

DEPLOY_HOST  := alma
DEPLOY_USER  := mgrigorov
DEPLOY_DIR   := /home/$(DEPLOY_USER)/midi-cleaner
SSH          := ssh $(DEPLOY_USER)@$(DEPLOY_HOST)

.PHONY: build run stop restart logs clean dev deploy deploy-setup

# ── Local ──────────────────────────────────────

build:
	podman build -t $(IMAGE_NAME) .

run: build stop
	podman run -d \
		--name $(CONTAINER_NAME) \
		-p $(LOCAL_PORT):5000 \
		-e SECRET_KEY="$$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
		$(IMAGE_NAME)
	@echo "MIDI Cleaner running at http://localhost:$(LOCAL_PORT)"

stop:
	podman stop $(CONTAINER_NAME) 2>/dev/null || true
	podman rm $(CONTAINER_NAME) 2>/dev/null || true

restart: stop run

logs:
	podman logs -f $(CONTAINER_NAME)

clean: stop
	podman rmi $(IMAGE_NAME) 2>/dev/null || true

dev:
	pip install -r requirements.txt
	python app.py

# ── Remote deploy to alma ──────────────────────

deploy:
	@echo "==> Syncing project to $(DEPLOY_HOST):$(DEPLOY_DIR)..."
	$(SSH) "mkdir -p $(DEPLOY_DIR)"
	rsync -avz --delete \
		--exclude '__pycache__' \
		--exclude '*.pyc' \
		--exclude 'uploads/' \
		--exclude '.git' \
		--exclude 'playwright-browsers' \
		--exclude 'node_modules' \
		--exclude '.DS_Store' \
		./ $(DEPLOY_USER)@$(DEPLOY_HOST):$(DEPLOY_DIR)/

	@echo "==> Building and starting container on $(DEPLOY_HOST) as $(DEPLOY_USER)..."
	$(SSH) "cd $(DEPLOY_DIR) && \
		podman stop $(CONTAINER_NAME) 2>/dev/null || true && \
		podman rm $(CONTAINER_NAME) 2>/dev/null || true && \
		podman build -t $(IMAGE_NAME) . && \
		podman run -d \
			--name $(CONTAINER_NAME) \
			--restart=always \
			-p $(REMOTE_PORT):5000 \
			-e SECRET_KEY=\"$$(python3 -c 'import secrets; print(secrets.token_hex(32))')\" \
			$(IMAGE_NAME)"

	@echo "==> Enabling lingering for $(DEPLOY_USER) and generating systemd unit..."
	$(SSH) "loginctl enable-linger $(DEPLOY_USER) 2>/dev/null || true && \
		mkdir -p ~/.config/systemd/user && \
		podman generate systemd --name $(CONTAINER_NAME) --new --files && \
		mv container-$(CONTAINER_NAME).service ~/.config/systemd/user/ 2>/dev/null || true && \
		systemctl --user daemon-reload && \
		systemctl --user enable container-$(CONTAINER_NAME).service 2>/dev/null || true"

	@echo ""
	@echo "✓ Deployed! MIDI Cleaner running at http://$(DEPLOY_HOST):$(REMOTE_PORT)"
	@echo "  Container runs as $(DEPLOY_USER) (rootless podman)."
	@echo "  Auto-starts on reboot via user-level systemd + lingering."

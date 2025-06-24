.PHONY: help setup dev test clean service-install service-uninstall service-start service-stop service-restart service-status service-logs install-mcp

help:  ## Show this help
	@echo "Nexus_3 Development Commands"
	@echo "==========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## Set up development environment
	./setup.sh

dev:  ## Start development server
	uv run uvicorn nexus.app:app --reload --host 0.0.0.0 --port 8100

test:  ## Run tests
	uv run pytest tests/ -v

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

service-install:  ## Install Nexus as a service
	./manage_service.sh install

service-uninstall:  ## Uninstall Nexus service
	./manage_service.sh uninstall

service-start:  ## Start Nexus service
	./manage_service.sh start

service-stop:  ## Stop Nexus service
	./manage_service.sh stop

service-restart:  ## Restart Nexus service
	./manage_service.sh restart

service-status:  ## Check Nexus service status
	./manage_service.sh status

service-logs:  ## View Nexus service logs
	./manage_service.sh logs

service-errors:  ## View Nexus error logs
	./manage_service.sh errors

install-mcp:  ## Build and install MCP server
	cd mcp_server && npm install && npm run build
	@echo "Add to Claude with:"
	@echo "claude mcp add nexus -s user -- node $(PWD)/mcp_server/dist/index.js"

check-services:  ## Check if required services are running
	@echo "Checking services..."
	@echo -n "Cortex_2 API: "
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ Running" || echo "❌ Not running"
	@echo -n "Nexus_3 API: "
	@curl -s http://localhost:8100/health > /dev/null && echo "✅ Running" || echo "❌ Not running"

test-api:  ## Test API endpoints
	@echo "Testing Nexus_3 API..."
	@curl -s http://localhost:8100/health | python3 -m json.tool || echo "API not running"

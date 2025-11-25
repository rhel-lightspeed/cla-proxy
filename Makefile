.PHONY: dev
dev: ## Run development API
	@echo "🚀 Running API: development"
	@uv run fastapi dev cla_proxy/api.py

.PHONY: request
request: ## Make an OpenAI-compatible request to the v1 API
	@echo "🚀 Making a request to the API"
	@curl -sX POST localhost:8000/v1/chat/completions \
		-H "Content-Type: application/json" \
		--data '{"messages": [{"role": "user", "content": "How do I enable SSH root login on RHEL?"}], "stream": false}' | jq

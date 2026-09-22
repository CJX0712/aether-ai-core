PY ?= python
VENV := .venv
BIN := $(VENV)/Scripts/python.exe

.PHONY: help venv install test e2e gate serve clean docker-build docker-run

help:
	@echo "venv        创建虚拟环境"
	@echo "install     安装锁定依赖"
	@echo "test        运行单元测试（离线可跑）"
	@echo "e2e         运行端到端验证（拉起真实服务进程）"
	@echo "gate        运行 P0 门禁（emoji 扫描）"
	@echo "verify      test + e2e + gate 全量验证"
	@echo "serve       启动 REST 服务"
	@echo "docker-build / docker-run  构建并运行容器"

venv:
	$(PY) -m venv $(VENV)

install:
	$(BIN) -m pip install -r requirements.lock.txt

test:
	$(BIN) -m pytest tests

e2e:
	$(BIN) tools/run_e2e.py

gate:
	$(BIN) tools/scan_emoji.py

verify: test e2e gate

serve:
	$(BIN) -m uvicorn aether.api.app:app --host 127.0.0.1 --port 8000

clean:
	rm -rf $(VENV) build dist .pytest_cache

docker-build:
	docker build -t aether-ai-core:0.1.0 .

docker-run:
	docker run --rm -p 8000:8000 aether-ai-core:0.1.0

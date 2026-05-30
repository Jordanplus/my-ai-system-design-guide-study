# AI System Design Guide — study & build helpers
# Usage: `make` (or `make help`) lists targets. `make study` opens the guide.

PORT  ?= 8000
ENTRY ?= index.html

# Pick the right "open in browser" command per OS
UNAME := $(shell uname)
ifeq ($(UNAME),Darwin)
  OPEN := open
else
  OPEN := xdg-open
endif

.DEFAULT_GOAL := help
.PHONY: help study serve open report diagram assets clean

help:
	@echo "AI System Design Guide — make targets"
	@echo ""
	@echo "  make study     啟動本機伺服器並開啟 $(ENTRY) 開始學習（Ctrl+C 結束）"
	@echo "  make serve     只啟動伺服器，不開瀏覽器"
	@echo "  make open      直接用 file:// 開啟 $(ENTRY)（頁內 Markdown 閱讀器功能受限）"
	@echo "  make report    重新產生並開啟 ai-system-design-guide.html 報告"
	@echo "  make diagram   由 .dot 重新算繪學習地圖 SVG（需 graphviz）"
	@echo "  make assets    下載 marked / mermaid 到 assets/（離線用）"
	@echo "  make clean     移除產生的檔案（保留 assets/）"
	@echo ""
	@echo "  覆寫埠號：make study PORT=8090"

# Main entry: serve over HTTP (so the in-page reader can fetch .md) and open the browser.
study:
	@command -v python3 >/dev/null || { echo "找不到 python3"; exit 1; }
	@echo "▶ 在 http://localhost:$(PORT)/$(ENTRY) 開始學習（按 Ctrl+C 結束伺服器）"
	@python3 -m http.server $(PORT) >/dev/null 2>&1 & \
	  SERVER_PID=$$!; \
	  trap 'kill $$SERVER_PID 2>/dev/null' INT TERM EXIT; \
	  sleep 1; \
	  if ! kill -0 $$SERVER_PID 2>/dev/null; then \
	    echo "✗ 埠號 $(PORT) 可能已被占用，請改用：make study PORT=8090"; exit 1; \
	  fi; \
	  $(OPEN) "http://localhost:$(PORT)/$(ENTRY)" 2>/dev/null || true; \
	  wait $$SERVER_PID

serve:
	@command -v python3 >/dev/null || { echo "找不到 python3"; exit 1; }
	@echo "▶ Serving on http://localhost:$(PORT)/  (Ctrl+C to stop)"
	@python3 -m http.server $(PORT)

open:
	@$(OPEN) "$(ENTRY)"

# Regenerate the arvinsa-style report (depends on the rendered diagram) and open it.
report: diagram
	@python3 diagrams/gen_report.py
	@$(OPEN) "ai-system-design-guide.html" 2>/dev/null || true

diagram: diagrams/learning-map.svg
diagrams/learning-map.svg: diagrams/learning-map.dot
	@command -v dot >/dev/null || { echo "需要 graphviz：brew install graphviz"; exit 1; }
	@dot -Tsvg $< -o $@ && echo "✓ 產生 $@"

# Vendor the JS libs locally so index.html works fully offline.
assets: assets/marked.min.js assets/mermaid.min.js
assets/marked.min.js:
	@mkdir -p assets && curl -fsSL -o $@ https://cdn.jsdelivr.net/npm/marked/marked.min.js && echo "✓ $@"
assets/mermaid.min.js:
	@mkdir -p assets && curl -fsSL -o $@ https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js && echo "✓ $@"

clean:
	@rm -f ai-system-design-guide.html diagrams/learning-map.svg
	@echo "✓ 已清除產生的報告與 SVG（assets/ 保留；如要移除請手動 rm -rf assets）"

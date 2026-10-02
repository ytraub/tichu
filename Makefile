PROJECT_FOLDER := ./project
JOURNAL_FOLDER := ./journal

ifeq ($(OS),Windows_NT)
    PYTHON := python
else
    PYTHON := python3
endif

client:
	@cd $(PROJECT_FOLDER)/client && $(PYTHON) -m http.server 2211 -d ./

server:
	@cd $(PROJECT_FOLDER)/server && source .venv/Scripts/activate && $(PYTHON) main.py

.PHONY: client server
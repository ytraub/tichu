ifeq ($(OS),Windows_NT)
    PYTHON := python
else
    PYTHON := python3
endif

client:
	@$(PYTHON) -m http.server 2211 -d ./client/

server:
	@cd server && $(PYTHON) main.py


.PHONY: client server
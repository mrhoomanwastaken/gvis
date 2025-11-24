# Makefile for gvis - Music Visualizer

# Variables
ARCH := $(shell uname -m)
OUTPUT_DIR := nudist
NUITKA_BASE_ARGS := --onefile --output-dir=$(OUTPUT_DIR) \
	--include-data-files='./.env=.env' \
	--include-data-dir="./src/images=src/images" \
	--include-data-files="./src/visualizers/shaders/bars_vertex.glsl=src/visualizers/shaders/bars_vertex.glsl" \
	--include-data-files="./src/visualizers/shaders/common_fragment.glsl=src/visualizers/shaders/common_fragment.glsl" \
	--include-data-files="./src/visualizers/shaders/lines_vertex.glsl=src/visualizers/shaders/lines_vertex.glsl" \
	--include-package="gi" \
	--debug \
	--show-progress
PREFIX ?= /usr/local
DESTDIR ?=
BINDIR = $(PREFIX)/bin
DESKTOPDIR = $(PREFIX)/share/applications

# Architecture-specific library
ifeq ($(ARCH),x86_64)
    CAVA_LIB := --include-data-files='./src/cava/libcavacore.x86.so=src/cava/libcavacore.x86.so'
else ifeq ($(ARCH),aarch64 arm64 armv8)
    CAVA_LIB := --include-data-files='./src/cava/libcavacore.arm64.so=src/cava/libcavacore.arm64.so'
else
    $(error Unsupported architecture: $(ARCH))
endif


# Default target
.PHONY: all setup clean compile x86 arm64 help install install-user uninstall

all: install

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt && pip install nuitka

# Auto-detect architecture and compile
compile: setup
	@echo "Compiling for $(ARCH)..."
	. venv/bin/activate && nuitka $(NUITKA_BASE_ARGS) $(CAVA_LIB) gvis.py

# Force x86_64 compilation
x86: setup
	@echo "Compiling for x86_64..."
	. venv/bin/activate && nuitka $(NUITKA_BASE_ARGS) --include-data-files='./src/cava/libcavacore.x86.so=src/cava/libcavacore.x86.so' gvis.py

# Force ARM64 compilation
arm64: setup
	@echo "Compiling for ARM64..."
	. venv/bin/activate && nuitka $(NUITKA_BASE_ARGS) --include-data-files='./src/cava/libcavacore.arm64.so=src/cava/libcavacore.arm64.so' gvis.py

# Clean build artifacts
clean:
	rm -rf $(OUTPUT_DIR)
	rm -rf venv



# System-wide installation
install: compile mkconfig
	install -Dm755 $(OUTPUT_DIR)/gvis.bin $(DESTDIR)$(BINDIR)/gvis
	install -Dm644 gvis.desktop $(DESTDIR)$(DESKTOPDIR)/gvis.desktop

# User installation
install-user: compile mkconfig
	mkdir -p ~/.local/bin ~/.local/share/applications
	cp $(OUTPUT_DIR)/gvis.bin ~/.local/bin/gvis
	chmod +x ~/.local/bin/gvis
	cp gvis.desktop ~/.local/share/applications/

# Uninstall
uninstall:
	rm -f $(DESTDIR)$(BINDIR)/gvis
	rm -f $(DESTDIR)$(DESKTOPDIR)/gvis.desktop

mkconfig:
	mkdir -p ~/.config/gvis
	python3 src/config/configmaker.py
	
# Help target
help:
	@echo "Available targets:"
	@echo "  all/compile - Auto-detect architecture and compile"
	@echo "  install     - Install system-wide (requires sudo)"
	@echo "  install-user - Install for current user only"
	@echo "  uninstall   - Remove installed files"
	@echo "  clean       - Remove build artifacts"
	@echo "  help        - Show this help message"
	@echo ""
	@echo "Current architecture: $(ARCH)"
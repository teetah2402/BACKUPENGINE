# Changelog

All notable changes to the **Flowork Hybrid AI Operating System** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

ai training sudah normal semua
---

## [1.0.0] - 2025-10-21
### 🎉 Initial Release: "The Awakening"

Welcome to the first public release of Flowork! This release introduces the world's first **Hybrid AI Operating System**, bridging the gap between Cloud convenience and Local privacy.

### 🚀 New Features (Core)
- **Hybrid Architecture:** Released the core engine that runs on `localhost` but is controlled via a secure Cloudflare Tunnel from the web.
- **Limitless Visual Designer:**
  - Added drag-and-drop workflow builder with 50+ logic nodes.
  - Implemented `WebWorker` based layout engine for high-performance rendering of complex graphs.
- **Time-Travel Debugger:** Added the ability to step back through execution history and inspect variable states at any tick.
- **Dashboard:** Real-time monitoring of local CPU/GPU usage, active jobs, and tunnel health.

### 🧠 New Features (AI Suite)
- **AI Council Orchestrator:**
  - Added multi-agent collaboration system where specialized agents (Planner, Coder, Reviewer) work together.
  - Implemented `Episodic Memory` using local Vector Database for long-term agent context.
- **Local AI Factory:**
  - **Model Forge:** Added tools to fine-tune LLMs using LoRA adapters on local hardware.
  - **GGUF Converter:** Integrated `llama.cpp` bindings to convert and quantize PyTorch models automatically.
  - **Dataset Manager:** Added tools to clean and format raw text/JSONL for training.
- **Agent Host:** Capability to run autonomous agents that persist and run in the background even when the GUI is closed.

### 🔌 New Features (System & Connectivity)
- **Flowork Gateway:**
  - Released the Python-based router handling secure WebSockets and HTTP traffic.
  - Implemented **Fine-Grained Access Control (FAC)** for granular permission management.
  - Added `env_guard.py` to strip sensitive environment variables from API responses.
- **Cloudflare Tunnel Integration:** Native support for `cloudflared` to expose the local engine securely without port forwarding.
- **Docker Support:** Full containerization support for the Engine (`flowork-gateway` + `flowork-core`).

### 📦 Widgets & Modules
- **Neural Music Gen:** Widget to generate audio using local models.
- **Sora Video Preview:** Interface for video generation tasks.
- **Code Review Guardian:** Capsule module for automated code auditing.

### 🛠️ Improvements
- **Performance:** Optimized WebSocket payload compression for faster token streaming.
- **UI/UX:** Implemented "Glassmorphism" design system with dark mode support by default.
- **Security:** Hardened local database encryption (SQLCipher support ready).

---

> *"The future is local, but the control is global."*
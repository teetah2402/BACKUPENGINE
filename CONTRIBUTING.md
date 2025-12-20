# Contributing to Flowork

First off, thank you for considering contributing to Flowork! It's people like you that make the open-source community such an amazing place to learn, inspire, and create.

Flowork is an ambitious project combining a **Cloud GUI** and a **Local AI Engine**. We welcome contributions to both parts of the ecosystem.

---

## 🧭 How Can I Contribute?

### 1. Reporting Bugs
This section guides you through submitting a bug report.
* **Check existing issues:** Before creating a new issue, please search to see if the problem has already been reported.
* **Use a clear title:** Describe the problem in a few words.
* **Provide reproduction steps:** How can we reproduce the bug? (e.g., "1. Go to Designer, 2. Drag a 'Start' node, 3. Click 'Run'").
* **Include logs:** Since Flowork runs locally, please check your `flowork-gateway/logs/` or Docker logs and paste relevant errors.

### 2. Suggesting Enhancements
Have a crazy idea for a new AI Agent or a UI widget?
* Open a **Feature Request** issue.
* Describe the feature in detail.
* If possible, include mockups or diagrams.

### 3. Pull Requests (Code Contributions)
We love PRs! Here's the workflow:

1.  **Fork the repository** to your GitHub account.
2.  **Clone your fork** locally.
3.  **Create a branch** for your fix/feature: `git checkout -b feature/amazing-new-widget`.
4.  **Commit your changes** using descriptive messages (see below).
5.  **Push** to your branch.
6.  **Open a Pull Request** targeting the `main` branch of the official repository.

---

## 🛠️ Development Setup

Flowork is a monorepo containing both the GUI and the Engine. You can choose to work on one or both.

### Prerequisites
* **Node.js** v18+ (For GUI)
* **Python** 3.10+ (For Engine)
* **Docker** (Optional but recommended)

### A. Working on the GUI (Frontend)
The GUI is built with **Vue 3 + Vite**.

```bash
cd flowork-gui
npm install
npm run dev

```

* Access the local dev server at `http://localhost:5173`.

### B. Working on the Engine (Backend)

The Engine handles the heavy lifting (AI, Filesystem, Tunnels).

```bash
cd flowork-gateway
# Create virtual environment (Recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run the Gateway
python run_gateway.py

```

---

## 🎨 Coding Guidelines

### General

* **English:** Please write all code comments, variable names, and commit messages in English.
* **Clean Code:** Keep functions small and focused.

### Frontend (Vue.js)

* Use the **Composition API** (`<script setup>`).
* Follow the [Vue Style Guide](https://vuejs.org/style-guide/) (Priority A & B).
* Components should be atomic and reusable.

### Backend (Python)

* Follow **PEP 8** style guidelines.
* Use Type Hints (`def my_func(a: int) -> str:`) where possible.
* If you modify the database models, ensure you include migration steps (if applicable).

---

## 📝 Commit Messages

We follow the **Conventional Commits** specification to automate our changelogs.

* `feat: add new AI Council panel`
* `fix: resolve websocket disconnection issue`
* `docs: update README with architecture diagram`
* `style: formatting changes (white-space, missing semi-colons)`
* `refactor: code change that neither fixes a bug nor adds a feature`
* `perf: code change that improves performance`

---

## 🧪 Testing

* If you add a new feature, please try to include a test case or verify it doesn't break existing flows.
* For the **Designer**, verify that nodes can still be dragged, connected, and executed.
* For **AI Providers**, ensure API keys are handled securely (never committed to git!).

---

## ⚖️ License

By contributing, you agree that your contributions will be licensed under its **MIT License**.

Thank you for building the future of Hybrid AI with us! 🚀

```


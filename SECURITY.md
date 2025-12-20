# Security Policy

At **Flowork**, security is not an afterthought; it is the foundation of our Hybrid Architecture. Because our engine runs on your local infrastructure, we treat security and privacy as our highest priority.

This document outlines our security philosophy, supported versions, and how to report vulnerabilities.

---

## 1. Supported Versions

We provide security updates for the latest major version.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## 2. Reporting a Vulnerability

We take all security reports seriously. If you discover a vulnerability in Flowork (Gateway, Core, or GUI), please **DO NOT** open a public issue.

### How to Report
Please email us privately at **security@flowork.cloud**.

In your email, please include:
* **Type of Issue:** (e.g., XSS, Remote Code Execution, Auth Bypass)
* **Full paths/URLs:** Where the issue occurs.
* **Proof of Concept:** Step-by-step instructions to reproduce the issue.
* **Impact:** How this vulnerability could be exploited.

### Our Response
1.  **Acknowledgment:** We will respond within 48 hours.
2.  **Assessment:** We will confirm the vulnerability and determine its severity.
3.  **Fix:** We will release a patch (e.g., v1.0.1) as soon as possible.
4.  **Disclosure:** Once fixed, we will publicly acknowledge your contribution (unless you prefer anonymity).

---

## 3. Security Architecture (The "Hybrid Shield")

Flowork is designed to be secure by default. Here is how we protect your local machine:

### A. No Open Ports (Cloudflare Tunnel)
Flowork uses `cloudflared` to create an outbound-only encrypted tunnel to Cloudflare's Edge.
* **Benefit:** You do **NOT** need to open any ports (Port Forwarding) on your router.
* **Protection:** Your public IP address remains hidden. Attacks targeting your IP will fail.

### B. Engine Token Authentication
Just having the Tunnel URL is not enough. Every request from the Cloud GUI to your Local Engine must carry a valid **Engine Token** (JWT-based).
* **Mechanism:** The Gateway verifies the token signature before processing any request.
* **Result:** Unauthorized users cannot execute commands on your machine, even if they guess your tunnel URL.

### C. Environment Guard (`env_guard.py`)
We implemented a strict filter in the Gateway specifically to prevent accidental leaks of sensitive keys.
* **Mechanism:** Any API response containing strings that look like API Keys (e.g., `sk-proj-...`, `ghp_...`) is automatically redacted or masked before leaving the engine.

### D. Fine-Grained Access Control (FAC)
Every module and tool in Flowork operates under a permission system.
* **Example:** A "File System Trigger" cannot read files outside the allowed directory unless explicitly authorized by the user config.

---

## 4. Privacy & Data Residency

**"Your Data Stays Home."**

* **Local Processing:** AI Inference, Vector Database storage, and file manipulation happen exclusively on your machine (`localhost` or Docker container).
* **Zero-Knowledge Cloud:** The Flowork Cloud GUI acts only as a "Remote Control". It does not store your datasets, API keys, or generated content. These are streamed directly to your browser via the secure tunnel.

---

## 5. User Responsibilities

While we secure the software, you are responsible for the environment it runs in:
1.  **Keep Docker Updated:** Ensure your Docker Desktop or Engine is patched.
2.  **Protect Your Token:** Never share your **Engine Token** or **Tunnel URL** publicly. Treat them like passwords.
3.  **Audit Agents:** When downloading community Agents/Workflows from the Marketplace, review their logic nodes before running them.

---

<p align="center">
  <em>Thank you for helping us keep the Flowork ecosystem safe.</em>
</p>
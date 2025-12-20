
# 🏗️ Flowork Architecture Reference

Dokumen ini menjelaskan desain teknis tingkat tinggi, prinsip rekayasa, dan aliran data dari **Flowork Operating System**.

Flowork dibangun di atas arsitektur **Hybrid-Cloud** yang unik, memisahkan lapisan kontrol (GUI) dari lapisan eksekusi (Engine) untuk menjamin privasi data maksimal dengan kenyamanan akses cloud.

---

## 🌍 High-Level Overview

Sistem Flowork terdiri dari tiga komponen utama yang bekerja secara sinkron:

1.  **Flowork Cloud GUI (The Brain):** Antarmuka visual berbasis web (Jamstack) yang di-host di Edge (Cloudflare).
2.  **Flowork Gateway (The Shield):** Router lokal yang menangani keamanan, antrian, dan tunneling.
3.  **Flowork Core (The Muscle):** Kernel utama yang menjalankan logika AI, workflow, dan manajemen data di mesin pengguna.

### Diagram Arsitektur Global

```mermaid
graph TD
    %% User Layer
    User[👤 User] -->|HTTPS/WSS| Cloud[☁️ Flowork Cloud GUI]

    %% Transport Layer
    Cloud <-->|Secure WebSocket| CFT[🔒 Cloudflare Tunnel]

    %% Local Infrastructure
    subgraph LocalMachine [💻 Local Machine / Server]
        CFT <-->|HTTP/WS| Gateway[🛡️ Flowork Gateway]

        %% Gateway Internal
        Gateway -->|Dispatch| Queue[⚡ Job Queue]
        Gateway -->|Auth Check| Security[🔐 FAC Security]

        %% Core Kernel
        Queue --> Core[🧠 Flowork Core]

        subgraph Kernel [Flowork Kernel Services]
            Core --> Agent[🤖 Agent Orchestrator]
            Core --> Workflow[flowchart Workflow Executor]
            Core --> Trainer[🏭 AI Trainer Factory]
        end

        %% Data & Providers
        Kernel --> DB[(💾 SQLite / Vector DB)]
        Kernel --> AI[🔌 AI Providers (Ollama, OpenAI, etc)]
        Kernel --> FS[📂 Local Filesystem]
    end

```

---

## 🔌 1. Communication Layer (The Hybrid Link)

Flowork memecahkan masalah konektivitas lokal tanpa perlu *Port Forwarding* yang tidak aman.

* **Cloudflare Tunnel (`cloudflared`):** Kami membungkus *Local Engine* dengan tunnel terenkripsi yang mengekspos endpoint aman ke internet publik hanya untuk GUI Flowork yang terautentikasi.
* **Protocol:** Komunikasi utama menggunakan **WebSocket** untuk event real-time (seperti streaming token LLM) dan **REST API** untuk operasi CRUD standar.
* **Security:** Setiap request dari Cloud GUI harus menyertakan **Engine Token** yang valid. Gateway akan menolak koneksi apa pun yang tidak memiliki *signature* yang benar.

---

## 🛡️ 2. Flowork Gateway (`flowork-gateway`)

Gateway adalah "Satpam" dan "Manajer Lalu Lintas". Tidak ada request yang masuk ke Core tanpa melewati Gateway.

### Tanggung Jawab Utama:

* **Identity & Access Management (IAM):** Memvalidasi token sesi dan hak akses pengguna.
* **Sharded Job Queue:** Menggunakan arsitektur antrian berbasis prioritas (`dispatcher.py`). Jika Core sibuk, tugas akan antri di sini agar sistem tidak *crash*.
* **Environment Guard:** Mencegah kebocoran *Environment Variables* sensitif melalui API (`env_guard.py`).
* **Rate Limiting:** Mencegah *abuse* atau *flooding* request ke Engine lokal.

**Tech Stack:** Python (FastAPI/Flask-style architecture), SQLAlchemy (SQLite).

---

## 🧠 3. Flowork Core (`flowork-core`)

Ini adalah jantung dari operasi. Core dirancang sebagai koleksi **Micro-Services Modular** yang berjalan dalam satu proses (Monolithic Modular).

### Komponen Kunci:

#### A. Workflow Engine (`workflow_executor_service`)

Mesin eksekusi visual.

* Menerjemahkan JSON dari GUI Designer menjadi graf logika yang dapat dieksekusi.
* Mendukung *Node* sinkronus dan asinkronus.
* Memiliki fitur **Time-Travel**, menyimpan *snapshot* state di setiap langkah eksekusi.

#### B. AI Council & Agents (`agent_executor_service`)

Sistem orkestrasi agen otonom.

* **Council Orchestrator:** Mengelola debat dan kolaborasi antara beberapa agen (misal: *Planner* vs *Critic*).
* **Episodic Memory:** Menyimpan riwayat interaksi dalam Vector Database untuk konteks jangka panjang.

#### C. AI Training Factory (`ai_training_service`)

Layanan manipulasi model tingkat lanjut.

* **GGUF Worker:** Mengonversi model PyTorch/Safetensors ke format GGUF untuk inferensi CPU/GPU yang efisien.
* **Dataset Worker:** Membersihkan dan memformat data mentah untuk pelatihan.
* **LoRA Fine-tuning:** Melatih adaptor model spesifik pada hardware lokal pengguna.

**Tech Stack:** Python 3.10+, PyTorch (opsional untuk training), Llama.cpp (via binding).

---

## 💻 4. Flowork GUI (`flowork-gui`)

Antarmuka pengguna yang "Bodoh tapi Cantik". GUI tidak memproses logika bisnis berat; ia hanya merender status dari Engine.

### Pola Desain:

* **Store-Driven UI:** Semua data dikelola oleh **Pinia Stores** (`store/engines.js`, `store/workflow.js`). View hanya me-render data dari Store.
* **Web Worker Layout:** Penghitungan posisi node dalam kanvas visual dilakukan di *background thread* (`layout.worker.js`) agar UI tetap 60fps meskipun ada ribuan node.
* **Dynamic Component Loading:** Widget dan Module dimuat secara *lazy-load* untuk performa awal yang cepat.

**Tech Stack:** Vue 3, Vite, Tailwind/Custom CSS, Rete.js (Customized).

---

## 🔄 Data Flow Example: "Execute Prompt"

Berikut adalah perjalanan data ketika user menekan tombol "Send" di AI Chat:

1. **GUI:** `AiChatWindow.vue` menangkap input user.
2. **Store:** `socket.store` mengirim payload JSON melalui WebSocket tunnel yang aman.
3. **Tunnel:** Cloudflare mengarahkan paket ke `cloudflared` di mesin lokal user.
4. **Gateway:** Menerima paket, memvalidasi token, dan memasukkan tugas ke `Job Queue`.
5. **Dispatcher:** Worker yang menganggur mengambil tugas tersebut.
6. **Core:**
* `Agent Service` memuat konteks memori.
* `AI Provider` memanggil model lokal (misal: Llama 3) atau API eksternal.
* Token respons di-stream kembali ke Gateway.


7. **Reverse Path:** Gateway -> Tunnel -> GUI -> User melihat teks muncul huruf demi huruf.

---

## 📂 File System Structure

```
/ (Root)
├── flowork-gui/          # Frontend Code
│   ├── src/workers/      # Web Workers for heavy UI math
│   └── src/store/        # State Management
├── floworkos/            # Backend Monorepo
│   ├── flowork-gateway/  # Router & Security
│   └── flowork-core/     # Logic Kernel
│       ├── flowork_kernel/
│       │   ├── services/ # Modular Logic Units
│       │   └── workers/  # Background Processors
│       └── ai_providers/ # Adapters for OpenAI, Gemini, Local, etc.

```

---

## 🚀 Scalability & Performance

* **Vertical Scaling:** Engine dirancang untuk memanfaatkan *multi-core* CPU dan *CUDA* cores GPU pengguna secara maksimal.
* **Horizontal Scaling (Roadmap):** Gateway mendukung `cluster/peers.py` yang memungkinkan satu GUI mengontrol beberapa Engine di mesin berbeda secara bersamaan (Cluster Mode).

---

<p align="center">
<em>Flowork Architecture Document - Updated for v1.0</em>
</p>

```

### ✨ Poin Kuat di Dokumen Ini:

1.  **Analogi Jelas:** Brain (GUI), Shield (Gateway), Muscle (Core). Ini bikin arsitektur kompleks jadi gampang dibayangin.
2.  **Fokus Privasi:** Menjelaskan detail gimana data lewat Tunnel dan Token, menjawab keraguan soal keamanan.
3.  **Technical Depth:** Nyebutin file spesifik (`dispatcher.py`, `layout.worker.js`) nunjukin kalau dokumentasi ini beneran sinkron sama kodenya.
4.  **Flowchart Mermaid:** Diagram visual selalu ngebantu banget buat mahamin alur data.

Langsung sikat bro\! 🏗️🚀

```
########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_training_service\colosseum_worker.py
# VERSION: "WHITE LABEL & ROBUST PATH EDITION"
# REPAIR NOTES:
# 1. ADDED: White Label Identity Injection (Hallo aku FLOWORK AI).
# 2. FIXED: Path handling to ensure we always use the directory, not the weight file (Fixes HFValidationError).
# 3. FIXED: Using 'dtype' instead of deprecated 'torch_dtype'.
# 4. ADDED: Protection against trying to load GGUF files in Transformers-based Arena.
# 5. TRUE SINGLETON pattern maintained.
########################################################################

import traceback
import time
import gc
import threading
import os

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel
except ImportError:
    pass

class ColosseumWorker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Mastiin cuma ada SATU instance di seluruh sistem (Singleton)"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ColosseumWorker, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self.active_base_id = None
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._sparring_lock = threading.Lock()

        # [MATA-MATA] Lock Telemetry
        self._current_action = "IDLE"
        self._lock_start_time = 0
        self._active_match_info = "NONE"

        # Config biar loading model 4-bit stabil dan gak hang
        self.bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        self._initialized = True

    def get_spy_report(self):
        """[MATA-MATA] Laporan status internal untuk debugging"""
        busy = self._sparring_lock.locked()
        duration = 0
        if busy and self._lock_start_time > 0:
            duration = round(time.time() - self._lock_start_time, 2)

        return {
            "is_busy": busy,
            "current_action": self._current_action,
            "held_for_seconds": duration,
            "match_info": self._active_match_info,
            "vram_allocated": torch.cuda.memory_allocated() if torch.cuda.is_available() else 0
        }

    def _unload_model(self, callback=None):
        """Bersihin VRAM/RAM sampai kinclong"""
        self._current_action = "FLUSHING_VRAM"
        msg = "Flushing VRAM and clearing the ring..."
        print(f"[Colosseum] {msg}")
        if callback: callback(msg)

        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None

        self.active_base_id = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _load_base_if_needed(self, base_path, base_id, callback=None):
        """Hanya load kalau modelnya BEDA dengan yang di RAM"""
        # [REPAIR] Robust Path Detection
        # Scan result: Transformers expects a directory. If we point to safetensors/gguf file, it fails.
        if base_path and os.path.isfile(base_path):
            if base_path.lower().endswith('.gguf'):
                raise ValueError("GGUF format is not supported for dynamic sparring in this arena. Use a standard model directory.")
            base_path = os.path.dirname(base_path)

        if self.active_base_id == base_id and self.model is not None:
            msg = f"Warm start: Model '{base_id}' already in memory."
            print(f"[Colosseum] {msg}")
            if callback: callback(msg)
            return

        self._unload_model(callback)
        msg = f"Loading Base Model: {base_id}..."
        print(f"[Colosseum] {msg}")
        if callback: callback(msg)

        try:
            self._current_action = f"LOADING_TOKENIZER:{base_id}"
            if callback: callback(f"Preparing tokenizer for {base_id}...")
            self.tokenizer = AutoTokenizer.from_pretrained(base_path, trust_remote_code=True)

            self._current_action = f"LOADING_WEIGHTS:{base_id}"
            if callback: callback(f"Injecting neural weights into VRAM (this may take a while)...")

            # [FIX] replaced torch_dtype for compliance
            self.model = AutoModelForCausalLM.from_pretrained(
                base_path,
                quantization_config=self.bnb_config if self.device == "cuda" else None,
                device_map="auto" if self.device == "cuda" else None,
                dtype=torch.float16,
                low_cpu_mem_usage=True,
                trust_remote_code=True
            )
            self.active_base_id = base_id
            msg = f"Model '{base_id}' is now STANDBY."
            print(f"[Colosseum] ✅ {msg}")
            if callback: callback(msg)

        except Exception as e:
            print(f"[Colosseum] ❌ Load Failed: {e}")
            self._unload_model()
            self._current_action = "FAILED_LOAD"
            if callback: callback(f"ERROR: Load failed - {str(e)}")
            raise e

    def run_sparring_match(self, base_model_path, adapter_path, prompt, base_name, adapter_name, progress_callback=None):
        """
        Eksekusi duel antar AI dengan pelaporan real-time ke GUI.
        """
        # [MATA-MATA] Deteksi kalau arena lagi dipake
        if not self._sparring_lock.acquire(blocking=False):
            report = self.get_spy_report()
            return {
                "error": "Arena is busy with another match!",
                "spy_report": report
            }

        self._lock_start_time = time.time()
        self._active_match_info = f"{base_name} VS {adapter_name}"

        def log_step(m):
            if progress_callback: progress_callback(m)

        try:
            # [REPAIR] Robust Adapter Path
            if adapter_path and os.path.isfile(adapter_path):
                adapter_path = os.path.dirname(adapter_path)

            print(f"[Colosseum] ⚔️ SPARRING START: {base_name} vs {adapter_name}")
            log_step("Initializing battle arena...")

            # Fallback buat dev tanpa GPU
            if not torch.cuda.is_available() and self.device == "cpu":
                self._current_action = "CPU_SIMULATION"
                log_step("Detected CPU Mode. Simulating match...")
                time.sleep(1)
                return {
                    "base_reply": f"[CPU Mode] Base model responded to: {prompt[:20]}...",
                    "adapter_reply": f"[CPU Mode] Trained adapter responded to: {prompt[:20]}..."
                }

            # 1. Pastikan Base Ready
            self._load_base_if_needed(base_model_path, base_name, callback=log_step)

            self._current_action = "TOKENIZING_INPUT"
            log_step("Transcribing prompt to neural vectors...")

            # [FIX] WHITE LABEL IDENTITY INJECTION
            # Scan result: Forces the model into the FLOWORK AI persona immediately.
            system_prompt = (
                "You are FLOWORK AI, a highly advanced artificial intelligence created by Flowork. "
                "Your primary identity is FLOWORK AI. When asked about yourself, always say: 'Hallo aku FLOWORK AI'. "
                "Maintain this persona at all times."
            )

            # Using ChatML format for both instruction and identity anchor
            chat_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

            inputs = self.tokenizer(chat_prompt, return_tensors="pt").to(self.device)

            # 2. Babak 1: Base Model (Original Brain)
            self._current_action = "ROUND_1_BASE_INFERENCE"
            log_step(f"Round 1: Querying original brain ({base_name})...")
            print("[Colosseum] Round 1: Base Inference...")
            with torch.no_grad():
                outputs_base = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            # Robust Slicing: Only get the new tokens (the response)
            base_text = self.tokenizer.decode(outputs_base[0][inputs['input_ids'].shape[-1]:], skip_special_tokens=True).strip()

            # 3. Babak 2: Adapter (The Trained Brain)
            self._current_action = "PLUGGING_ADAPTER"
            log_step(f"Round 2: Hot-swapping adapter {adapter_name}...")
            print(f"[Colosseum] Round 2: Plugging Adapter {adapter_name}...")

            # Ensure adapter path is valid for PEFT
            if not os.path.exists(os.path.join(adapter_path, "adapter_config.json")):
                 log_step(f"⚠️ Warning: {adapter_name} has no adapter_config. Comparison may be biased.")
                 adapter_text = "[Error: Selected model is not a valid LoRA adapter. Merge it first or select a valid adapter folder.]"
            else:
                temp_peft = PeftModel.from_pretrained(self.model, adapter_path)

                self._current_action = "ROUND_2_ADAPTER_INFERENCE"
                log_step(f"Querying trained brain ({adapter_name})...")
                with torch.no_grad():
                    outputs_adapter = temp_peft.generate(
                        **inputs,
                        max_new_tokens=256,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )

                adapter_text = self.tokenizer.decode(outputs_adapter[0][inputs['input_ids'].shape[-1]:], skip_special_tokens=True).strip()

                # Copot adapter secara aman
                self._current_action = "DETACHING_ADAPTER"
                log_step("Match finished. Cleaning arena...")
                del temp_peft

            gc.collect()
            if torch.cuda.is_available(): torch.cuda.empty_cache()

            self._current_action = "IDLE"
            log_step("Battle records finalized.")
            return {
                "base_reply": base_text,
                "adapter_reply": adapter_text
            }

        except Exception as e:
            self._current_action = f"CRASHED:{str(e)[:50]}"
            traceback.print_exc()
            log_step(f"CRITICAL ERROR: {str(e)}")
            return {"error": f"Arena Error: {str(e)}"}
        finally:
            self._lock_start_time = 0
            self._active_match_info = "NONE"
            self._sparring_lock.release()
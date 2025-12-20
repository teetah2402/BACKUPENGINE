########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_training_service\merge_worker.py
# VERSION: "HIGH-PRECISION NEURAL MERGE"
# REPAIR NOTES:
# 1. FIXED: Added Base Model remapping to prevent merging into 4-bit (Fixes Indo-Chinese language mixing).
# 2. FIXED: Replaced 'torch_dtype' with 'dtype' for modern transformers compatibility.
# 3. ADDED: Robust base model detection from adapter_config.
# 4. ENHANCED: Explicit garbage collection after merge to keep the engine lightweight.
########################################################################

import os
import datetime
import traceback
import json
import threading
import gc # [NEW] Added for memory cleanup

try:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError:
    pass

class MergeWorker:
    def __init__(self, data_path, models_root, logs_dir):
        self.data_path = data_path
        self.models_root = models_root
        self.logs_dir = logs_dir

    def _log(self, job_id, msg):
        print(f"[{job_id}] {msg}", flush=True)
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_file = os.path.join(self.logs_dir, f"{job_id}.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {msg}\n")
        except: pass

    def run_job(self, job_id, adapter_model_id, new_model_name, cb):
        try:
            cb(job_id, {"status": "PREPARING", "message": f"Starting Merge..."})
            self._execute_merge(job_id, adapter_model_id, new_model_name, cb)
        except Exception as e:
            err_msg = f"Merge Crash: {str(e)}"
            tb = traceback.format_exc()
            print(f"[Merge] ERROR job {job_id}: {tb}")
            cb(job_id, {"status": "FAILED", "message": err_msg, "progress": 0})

    def _execute_merge(self, job_id, adapter_model_id, new_model_name, cb):
        self._log(job_id, "--- STARTING MERGE JOB ---")

        adapter_path = os.path.join(self.models_root, "text", adapter_model_id)
        if not os.path.exists(adapter_path):
             raise Exception(f"Adapter {adapter_model_id} not found.")

        config_file = os.path.join(adapter_path, "adapter_config.json")

        # [REPAIR] Default to FP16 model instead of 4bit to ensure language quality
        # base_model_path = "unsloth/Qwen2.5-7B-bnb-4bit" # Old 4-bit fallback
        base_model_path = "unsloth/Qwen2.5-7B" # New high-precision fallback

        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    conf = json.load(f)
                    raw_base = conf.get("base_model_name_or_path", base_model_path)

                    # [REPAIR] AUTO-REMAPPER LOGIC
                    # If the training used a 4-bit model, we MUST use the full-precision equivalent for merging.
                    # Merging into 4-bit causes weights corruption (the "Indo-Chinese" mixing bug).
                    if "-bnb-4bit" in raw_base:
                        base_model_path = raw_base.replace("-bnb-4bit", "")
                        self._log(job_id, f"Detected 4-bit base. Remapping to High-Precision: {base_model_path}")
                    else:
                        base_model_path = raw_base
            except: pass

        self._log(job_id, f"Adapter Path: {adapter_path}")
        self._log(job_id, f"Base Model (FP16): {base_model_path}")

        cb(job_id, {"progress": 20, "message": "Loading Base Model in FP16 (CPU)..."})

        # [FIX] Modernizing the call: replaced 'torch_dtype' with 'dtype'
        # base = AutoModelForCausalLM.from_pretrained(
        #     base_model_path, device_map="cpu", torch_dtype=torch.float16, low_cpu_mem_usage=True
        # )
        base = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            device_map="cpu",
            dtype=torch.float16,
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )

        self._log(job_id, "Loading LoRA Adapter...")
        model = PeftModel.from_pretrained(base, adapter_path)

        self._log(job_id, "Merging weights (Neural Unification)...")
        # This creates a standalone model with the knowledge integrated
        model = model.merge_and_unload()

        save_path = os.path.join(self.models_root, "text", new_model_name)
        os.makedirs(save_path, exist_ok=True)

        self._log(job_id, f"Saving merged model to: {save_path}")
        model.save_pretrained(save_path)

        self._log(job_id, "Syncing Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        tokenizer.save_pretrained(save_path)

        # [NEW] Cleanup to prevent engine bloat
        self._log(job_id, "Cleaning memory cache...")
        del base
        del model
        gc.collect()

        self._log(job_id, "Merge Complete! Model is now 100% standalone.")
        cb(job_id, {"status": "COMPLETED", "message": "Model Merged Successfully (High-Precision)", "progress": 100})
########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_training_service\gguf_worker.py total lines 267 
########################################################################

import os
import datetime
import traceback
import json
import shutil
import gc
import sys
import subprocess
import re
import psutil
import importlib.util
import stat

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
except ImportError:
    pass

UNSLOTH_AVAILABLE = False
try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError:
    pass

class GgufWorker:
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

    def run_job(self, job_id, adapter_model_id, quantization, new_model_name, cb, strategy="auto"):
        try:
            self._ensure_conversion_libs(job_id)
            self._ensure_llama_cpp_binaries(job_id)

            cb(job_id, {"status": "PREPARING", "message": f"Initializing Manual GGUF Pipeline..."})
            self._execute_manual_pipeline(job_id, adapter_model_id, quantization, new_model_name, cb)
        except Exception as e:
            err_msg = f"GGUF Failure: {str(e)}"
            tb = traceback.format_exc()
            print(f"[GGUF] ERROR job {job_id}: {tb}")
            self._log(job_id, f"CRITICAL ERROR: {err_msg}")
            cb(job_id, {"status": "FAILED", "message": err_msg, "progress": 0})

    def _ensure_conversion_libs(self, job_id):
        required = ['gguf', 'sentencepiece', 'google.protobuf', 'scipy']
        pip_names = {'google.protobuf': 'protobuf'}
        missing = []

        for pkg in required:
            if importlib.util.find_spec(pkg) is None:
                missing.append(pip_names.get(pkg, pkg))

        if missing:
            self._log(job_id, f"⚠️ Missing {missing}! Installing now...")
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            self._log(job_id, "✅ Dependencies installed.")

    def _ensure_llama_cpp_binaries(self, job_id):
        """Memastikan script convert dan binary quantize ada."""
        script_path = "llama.cpp/unsloth_convert_hf_to_gguf.py"
        if not os.path.exists(script_path):
             self._log(job_id, "⚠️ llama.cpp script missing. Triggering Unsloth fetch...")
             try:
                 from unsloth.save import _install_llama_cpp
                 _install_llama_cpp()
             except: pass

        if not os.path.exists(script_path):
            raise FileNotFoundError("Gagal mendownload llama.cpp/convert script.")

        quantize_candidates = [
            "llama.cpp/llama-quantize",
            "llama.cpp/quantize",
            "llama.cpp/build/bin/quantize",
            "/usr/local/bin/llama-quantize"
        ]

        self.quantize_bin = None
        for path in quantize_candidates:
            if os.path.exists(path):
                self.quantize_bin = os.path.abspath(path)
                st = os.stat(self.quantize_bin)
                os.chmod(self.quantize_bin, st.st_mode | stat.S_IEXEC)
                break

        if not self.quantize_bin:
            self._log(job_id, "⚠️ Binary 'llama-quantize' not found. Attempting to compile...")
            try:
                subprocess.check_call(["make", "-C", "llama.cpp", "quantize"])
                self.quantize_bin = os.path.abspath("llama.cpp/llama-quantize")
            except Exception as e:
                self._log(job_id, f"❌ Compilation failed: {e}")
                pass

        self._log(job_id, f"✅ Quantize Binary: {self.quantize_bin}")

    def _run_subprocess(self, job_id, cmd, description):
        """Helper buat jalanin command dengan logging realtime & path injection"""
        self._log(job_id, f"🚀 Executing {description}...")
        self._log(job_id, f"CMD: {' '.join(cmd)}")

        env = os.environ.copy()
        venv_site = next((p for p in sys.path if "site-packages" in p), None)
        if venv_site:
            env["PYTHONPATH"] = venv_site + os.pathsep + env.get("PYTHONPATH", "")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        stderr_log = ""
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self._log(job_id, f"[OUT] {output.strip()}")

        stderr_output = process.stderr.read()
        if stderr_output:
            self._log(job_id, f"[ERR] {stderr_output.strip()}")
            stderr_log += stderr_output

        rc = process.poll()
        if rc != 0:
            raise RuntimeError(f"{description} failed (Code {rc}). Error: {stderr_log}")

    def _execute_manual_pipeline(self, job_id, adapter_model_id, quantization, new_model_name, cb):
        """
        Pipeline Manual:
        1. Merge Model (Python)
        2. Convert ke f16 GGUF (Python Script)
        3. Quantize ke q4/q8 (C++ Binary)
        """

        output_dir = os.path.join(self.models_root, "gguf")
        os.makedirs(output_dir, exist_ok=True)

        safe_name = re.sub(r'\W+', '', new_model_name)
        temp_dir = os.path.abspath(os.path.join(output_dir, f"temp_manual_{safe_name}"))

        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        cb(job_id, {"status": "MERGING", "progress": 20, "message": "Merging weights..."})

        clean_adapter_id = re.sub(r'[^\w\s\-\.]', '', adapter_model_id).strip().replace(' ', '_')
        adapter_path = os.path.join(self.models_root, "text", adapter_model_id)
        if not os.path.exists(adapter_path):
            adapter_path = os.path.join(self.models_root, "text", clean_adapter_id)
            if not os.path.exists(adapter_path):
                adapter_path = adapter_model_id

        vram_gb = 8.0
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        merge_device = "cpu" if vram_gb < 16.0 else "cuda"

        self._log(job_id, f"Loading & Merging model (Device: {merge_device})...")


        base_model_path = "unsloth/Qwen2.5-7B"
        try:
            with open(os.path.join(adapter_path, "adapter_config.json"), "r") as f:
                acfg = json.load(f)
                orig_base = acfg.get("base_model_name_or_path", "")
                if orig_base:
                    base_model_path = orig_base.replace("-bnb-4bit", "").replace("-4bit", "")
                    self._log(job_id, f"Auto-targeted high precision base: {base_model_path}")
        except: pass

        model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            device_map=merge_device,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        model = PeftModel.from_pretrained(model, adapter_path)
        model = model.merge_and_unload()

        tokenizer = AutoTokenizer.from_pretrained(base_model_path)

        self._log(job_id, "Saving HF model to temp...")
        model.save_pretrained(temp_dir)
        tokenizer.save_pretrained(temp_dir)

        config_path = os.path.join(temp_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_data = json.load(f)
            if "quantization_config" in config_data:
                del config_data["quantization_config"]
                self._log(job_id, "🛡️ Cleaned bitsandbytes traces from config.json")
            config_data["torch_dtype"] = "float16"
            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=4)

        del model
        gc.collect()
        torch.cuda.empty_cache()

        cb(job_id, {"status": "CONVERTING", "progress": 50, "message": "Converting to GGUF F16..."})

        f16_outfile = os.path.join(temp_dir, "model_f16.gguf")
        convert_script = os.path.abspath("llama.cpp/unsloth_convert_hf_to_gguf.py")

        convert_cmd = [
            sys.executable,
            convert_script,
            "--outfile", f16_outfile,
            "--outtype", "f16",
            temp_dir
        ]

        self._run_subprocess(job_id, convert_cmd, "Conversion to F16")

        q_methods = quantization if isinstance(quantization, list) else quantization.split(",")
        q_methods = [q.strip() for q in q_methods if q.strip()]

        if not self.quantize_bin:
            self._log(job_id, "⚠️ Quantize binary missing. Skipping quantization step.")
            final_path = os.path.join(output_dir, f"{new_model_name}.f16.gguf")
            shutil.move(f16_outfile, final_path)
            self._log(job_id, f"✅ Exported unquantized F16 model: {final_path}")
        else:
            for q_method in q_methods:
                cb(job_id, {"status": "QUANTIZING", "progress": 75, "message": f"Quantizing to {q_method}..."})

                final_path = os.path.join(output_dir, f"{new_model_name}.{q_method}.gguf")

                quantize_cmd = [
                    self.quantize_bin,
                    f16_outfile,
                    final_path,
                    q_method
                ]

                self._run_subprocess(job_id, quantize_cmd, f"Quantization to {q_method}")
                self._log(job_id, f"✅ Created: {final_path}")

        try: shutil.rmtree(temp_dir)
        except: pass

        cb(job_id, {"status": "COMPLETED", "message": "All Done!", "progress": 100})

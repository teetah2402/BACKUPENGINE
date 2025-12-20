########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\vocal_isolator_module\processor.py total lines 165 
########################################################################

import os
import shutil
import subprocess
import sys
import logging
import importlib.util # NOTE: Used for lightweight package detection
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer

class VocalIsolatorModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "free"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.ffmpeg_path = self._find_ffmpeg()
        self._ensure_icon()

    def _ensure_icon(self):
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(module_dir, "icon.png")
            if not os.path.exists(icon_path):
                default_icon = os.path.join(self.kernel.project_root_path, "assets", "default_module.png")
                if os.path.exists(default_icon):
                    shutil.copy(default_icon, icon_path)
        except:
            pass

    def _find_ffmpeg(self):
        ffmpeg_exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        vendor_path = os.path.join(self.kernel.project_root_path, "vendor", "ffmpeg", "bin", ffmpeg_exe)
        if os.path.exists(vendor_path):
            os.environ["PATH"] += os.pathsep + os.path.dirname(vendor_path)
            return vendor_path
        if shutil.which("ffmpeg"):
            return "ffmpeg"
        return None

    def _install_package(self, package_name, status_updater):
        try:
            status_updater(f"Installing missing requirement: {package_name}...", "INFO")
            module_dir = os.path.dirname(os.path.abspath(__file__))
            req_file = os.path.join(module_dir, "requirements.txt")

            if os.path.exists(req_file) and "audio-separator" in package_name:
                cmd = [sys.executable, "-m", "pip", "install", "-r", req_file]
            else:
                cmd = [sys.executable, "-m", "pip", "install", package_name]

            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            importlib.invalidate_caches()
            return True
        except Exception as e:
            self.logger(f"Failed to auto-install {package_name}: {e}", "ERROR")
            return False

    def execute(self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs):
        if mode == "SIMULATE":
            status_updater("Simulating MDX separation...", "INFO")
            return {"payload": payload, "output_name": "success"}

        importlib.invalidate_caches()
        module_dir = os.path.dirname(os.path.abspath(__file__))
        sentinel_path = os.path.join(module_dir, ".deps_installed")

        lib_found = importlib.util.find_spec("audio_separator") is not None

        if not lib_found or not os.path.exists(sentinel_path):
            status_updater("Library 'audio-separator' not found. Auto-installing...", "WARN")
            if not self._install_package("audio-separator[cpu]", status_updater):
                status_updater("Failed to install audio-separator. Check logs.", "ERROR")
                return {"payload": payload, "output_name": "error"}
            with open(sentinel_path, "w") as f: f.write("ok")
            importlib.invalidate_caches()

        from audio_separator.separator import Separator

        audio_path = config.get("audio_path")
        output_folder = config.get("output_folder")
        model_name = config.get("model_name", "UVR_MDXNET_KARA_2")
        output_format = config.get("output_format", "wav").lower()

        if not audio_path or not os.path.exists(audio_path):
            status_updater(f"File audio tidak ditemukan: {audio_path}", "ERROR")
            return {"payload": payload, "output_name": "error"}

        if not output_folder:
            default_storage = os.path.join(self.kernel.project_root_path, "storage", "separated_audio")
            os.makedirs(default_storage, exist_ok=True)
            output_folder = default_storage
            status_updater(f"Folder output kosong. Otomatis menyimpan ke: {output_folder}", "WARN")
        else:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder, exist_ok=True)

        try:
            logging.getLogger("audio_separator").setLevel(logging.ERROR)
            logging.getLogger("onnxruntime").setLevel(logging.ERROR)

            status_updater(f"Initializing Engine (Hybrid API Mode)...", "INFO")

            cache_dir = os.path.join(self.kernel.project_root_path, "cache", "models")
            os.makedirs(cache_dir, exist_ok=True)

            sep_kwargs = {
                "output_dir": output_folder,
                "model_file_dir": cache_dir,
                "output_format": output_format
            }

            try:
                separator = Separator(torch_device='cpu', **sep_kwargs)
            except TypeError:
                separator = Separator(use_cuda=False, **sep_kwargs)

            status_updater(f"Loading Model: {model_name}...", "INFO")
            separator.load_model(model_filename=f"{model_name}.onnx")

            status_updater("Separating... (CPU intensive, mohon tunggu)", "INFO")
            output_files = separator.separate(audio_path)

            if not output_files:
                raise ValueError("Separation engine failed to produce any files.")

            final_vocals = None
            final_music = None

            for f in output_files:
                full_path = os.path.join(output_folder, f)
                if not os.path.exists(full_path):
                    continue

                lower_name = f.lower()
                if "vocal" in lower_name:
                    final_vocals = full_path
                elif "instrumental" in lower_name or "music" in lower_name:
                    final_music = full_path
                else:
                    if not final_music: final_music = full_path
                    elif not final_vocals: final_vocals = full_path

            status_updater(f"Selesai! Disimpan di: {output_folder}", "SUCCESS")

            if "data" not in payload or not isinstance(payload["data"], dict):
                payload["data"] = {}

            payload["data"]["vocals_path"] = final_vocals
            payload["data"]["accompaniment_path"] = final_music

            return {"payload": payload, "output_name": "success"}

        except Exception as e:
            err_msg = str(e)
            self.logger(f"Separation failed: {err_msg}", "ERROR")
            status_updater(f"Separation Error: {err_msg}", "ERROR")
            return {"payload": payload, "output_name": "error"}

    def get_data_preview(self, config: dict):
        return [{"status": "preview_not_available"}]

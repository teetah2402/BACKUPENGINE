########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\tools\prompt_template_plugin\processor.py total lines 95 
########################################################################

import os
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer
from flowork_kernel.utils.payload_helper import get_nested_value

class ImageGeneratorModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "pro"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.ai_manager = self.services.get("ai_provider_manager_service")

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        prompt_var = config.get('prompt_source_variable', 'data.prompt_gambar')
        provider_id = config.get('provider_override', '').strip() or None

        prompt_text = get_nested_value(payload, prompt_var)

        if not prompt_text:
            prompt_text = get_nested_value(payload, 'data.prompt')
            if prompt_text:
                self.logger(f"Prompt not found in '{prompt_var}', used 'data.prompt' instead.", "WARN")

        if mode == 'SIMULATE':
            status_updater("Simulating image generation...", "INFO")
            sim_prompt = prompt_text if prompt_text else "[No Prompt Provided]"
            self.logger(f"SIMULATION: Would generate image for: {sim_prompt[:50]}...", "INFO")

            dummy_path = os.path.join(self.kernel.project_root_path, "assets", "default_module.png")

            if 'data' not in payload: payload['data'] = {}
            payload['data']['generated_image_path'] = dummy_path

            status_updater("Image simulated successfully.", "SUCCESS")
            return {"payload": payload, "output_name": "success"}

        if not prompt_text or not isinstance(prompt_text, str):
            return self._error(f"No valid text prompt found in '{prompt_var}'.", payload)

        if not self.ai_manager:
            self.ai_manager = self.kernel.get_service("ai_provider_manager_service")
            if not self.ai_manager:
                return self._error("AI Provider Manager Service unavailable.", payload)

        try:
            status_label = f"Generating with {provider_id}..." if provider_id else "Generating image..."
            status_updater(status_label, "INFO")

            response = self.ai_manager.query_ai_by_task(
                task_type='image',
                prompt=prompt_text,
                endpoint_id=provider_id
            )

            if "error" in response:
                raise Exception(response["error"])

            image_path = response.get('data')
            if not image_path:
                raise Exception("Provider returned success but no image path.")

            status_updater("Image generated successfully.", "SUCCESS")

            if 'data' not in payload or not isinstance(payload['data'], dict):
                payload['data'] = {}

            payload['data']['generated_image_path'] = image_path

            return {"payload": payload, "output_name": "success"}

        except Exception as e:
            return self._error(f"Generation failed: {str(e)}", payload)

    def _error(self, msg, payload):
        self.logger(msg, "ERROR")
        if 'data' not in payload: payload['data'] = {}
        payload['data']['error'] = msg
        return {"payload": payload, "output_name": "error"}

    def get_dynamic_output_schema(self, config):
        return [{
            "name": "data.generated_image_path",
            "type": "string",
            "description": "Path to the generated image."
        }]

    def get_data_preview(self, config: dict):
        prov = config.get('provider_override', 'System Default')
        return [{'status': 'ready', 'message': f"Provider: {prov}"}]

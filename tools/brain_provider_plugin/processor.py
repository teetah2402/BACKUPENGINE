########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\tools\brain_provider_plugin\processor.py total lines 77 
########################################################################

from flowork_kernel.api_contract import BaseBrainProvider, IExecutable, IDataPreviewer

class BrainProviderPlugin(BaseBrainProvider, IExecutable, IDataPreviewer):

    TIER = "pro"

    def __init__(self, module_id: str, services: dict):
        super().__init__(module_id, services)
        self.ai_manager = self.services.get("ai_provider_manager_service")

    def get_provider_name(self) -> str:
        return "AI Brain Provider"

    def is_ready(self) -> tuple[bool, str]:
        return (True, "")

    def think(self, objective: str, tools_string: str, history: list, last_observation: str) -> dict:
        self.logger("The 'think' method should be called on the Agent Host, not the Provider node.", "WARN")
        return {"error": "Configuration Node Only"}

    def execute(self, payload, config, status_updater, mode='EXECUTE', **kwargs):
        provider_id = config.get("selected_ai_provider", "").strip()
        sys_instruction = config.get("system_instruction_override", "")

        if not provider_id:
            msg = "No AI Provider ID specified."
            self.logger(msg, "ERROR")
            status_updater(msg, "ERROR")
            return {"payload": payload, "output_name": "brain_output"} # Return anyway to not block flow? Or block?

        if mode == "SIMULATE":
            status_updater(f"Simulating Brain: {provider_id}", "INFO")
            self._inject_config(payload, provider_id, sys_instruction)
            return {"payload": payload, "output_name": "brain_output"}

        if self.ai_manager:
            provider = self.ai_manager.get_provider(provider_id)
            if not provider:
                status_updater(f"Provider '{provider_id}' not found!", "WARN")
            else:
                status_updater(f"Brain Selected: {provider_id}", "SUCCESS")
        else:
            status_updater("AI Manager Service unavailable.", "WARN")

        self._inject_config(payload, provider_id, sys_instruction)

        return {"payload": payload, "output_name": "brain_output"}

    def _inject_config(self, payload, provider_id, sys_instruction):
        if "data" not in payload: payload["data"] = {}

        brain_conf = {
            "provider_id": provider_id,
            "source_node": self.module_id
        }
        if sys_instruction:
            brain_conf["system_instruction"] = sys_instruction

        payload["data"]["_dynamic_brain_config"] = brain_conf
        self.logger(f"Injected brain config: {provider_id}", "DEBUG")

    def create_properties_ui(self, parent_frame, get_current_config, available_vars):
        pass

    def get_data_preview(self, config: dict):
        pid = config.get("selected_ai_provider", "None")
        return [{
            'status': 'ready',
            'message': f"Brain: {pid}",
            'details': {'provider_id': pid}
        }]

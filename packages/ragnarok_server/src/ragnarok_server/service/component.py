from typing import Any, Dict

from ragnarok_core.components import ComponentManager, component_manager


class ComponentService:
    component_manager: ComponentManager

    def __init__(self) -> None:
        self.component_manager = component_manager

    def list_components(self) -> Dict[str, Dict[str, Any]]:
        return self.component_manager.list_details()


component_service = ComponentService()

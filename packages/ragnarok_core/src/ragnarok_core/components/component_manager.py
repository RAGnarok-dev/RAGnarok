from typing import Dict, Type

from ragnarok_core.exceptions import DuplicateComponentError, InvalidComponentHintError
from ragnarok_toolkit.component import RagnarokComponent


class ComponentInfo:
    """
    the info of the component, would be stored in manager once registered
    """

    def __init__(self, *, name: str, is_official: bool, component_class: Type[RagnarokComponent]) -> None:
        self.name = name
        self.is_official = is_official
        self.component_class = component_class


class ComponentManager:
    """
    manager of the components, should be used as a singleton
    """

    def __init__(self) -> None:
        self.components: Dict[str, ComponentInfo] = {}

    def register_component(self, component_info: ComponentInfo, *, check_duplication: bool = True) -> None:
        """register a component to manager"""
        if check_duplication and component_info.name in self.components:
            raise DuplicateComponentError(component_name=component_info.name)

        if component_info.component_class.ENABLE_HINT_CHECK and not component_info.component_class.validate():
            raise InvalidComponentHintError(component_name=component_info.name)

        self.components[component_info.name] = component_info

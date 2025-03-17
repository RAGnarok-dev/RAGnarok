import importlib
import logging
import os
import sys

from ragnarok_core.components.component_manager import ComponentInfo, ComponentManager
from ragnarok_toolkit.component import RagnarokComponent

logger = logging.getLogger(__name__)

component_manager = ComponentManager()


def register_official_components() -> None:
    """
    register all the official components
    """
    package_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(package_dir)
    official_components_path = os.path.join(os.path.dirname(__file__), "official_components")
    for filename in os.listdir(official_components_path):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"official_components.{filename[:-3]}"
            module = importlib.import_module(module_name)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, RagnarokComponent) and attr != RagnarokComponent:
                    component_info = ComponentInfo(name=attr_name, is_official=True, component_class=attr)
                    component_manager.register_component(component_info)
                    logger.info(f"Registered {attr_name} component successfully")


# TODO register custom components

register_official_components()

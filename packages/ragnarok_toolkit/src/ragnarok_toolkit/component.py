from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Dict, Optional, Set, Tuple, TypedDict, Union, get_type_hints


class ComponentIOType(StrEnum):
    """the supported input and output types for a component"""

    STRING = "STRING"
    INT = "INT"
    FLOAT = "FLOAT"

    @property
    def python_type(self):
        return TYPE_MAPPING[self]


TYPE_MAPPING = {
    ComponentIOType.INT: int,
    ComponentIOType.FLOAT: float,
    ComponentIOType.STRING: str,
}


class ComponentInputTypeOption(TypedDict):
    """represent an input variable options"""

    name: str
    allowed_types: Set[ComponentIOType]
    required: bool


class ComponentOutputTypeOption(TypedDict):
    """represent an output variable options"""

    name: str
    type: ComponentIOType


class RagnarokComponent(ABC):
    """
    base class for a Ragnarök component,
    designed to standardize component code format
    """

    # the description of the component's functionality
    DESCRIPTION: str

    # whether to enable type annotation check for identification
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    @abstractmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        """the options of all the input value"""
        return ()

    @classmethod
    @abstractmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        """the options of all the output value"""
        return ()

    @classmethod
    @abstractmethod
    def execute(cls, *args, **kwargs) -> Dict[str, Any]:
        """
        execute the component function, could be either sync or async
        """
        pass

    @classmethod
    def validate(cls) -> bool:
        """check if the 'execute' function corresponds to the INPUT_OPTIONS and OUTPUT_OPTIONS"""
        execute_params = get_type_hints(cls.execute)
        execute_params.pop("return")

        input_options = cls.input_options()
        input_option_names = {option["name"] for option in input_options}

        # check input name set
        if set(execute_params.keys()) != input_option_names:
            return False

        # check input type
        for option in input_options:
            param_name = option["name"]
            allowed_types = {io_type.python_type for io_type in option["allowed_types"]}
            param_type = execute_params.get(param_name)

            if option["required"]:
                if param_type not in allowed_types:
                    return False
            else:
                # optional param
                if (
                    param_type is not None
                    and hasattr(param_type, "__origin__")
                    and (param_type.__origin__ is Optional or param_type.__origin__ is Union)
                ):
                    # extract the inner type from Optional
                    actual_types = {arg for arg in param_type.__args__ if arg is not type(None)}
                    if not actual_types.issubset(allowed_types):
                        return False
                else:
                    return False

        output_options = cls.output_options()
        output_type_mapping = {option["name"]: option["type"].python_type for option in output_options}

        execute_return_type = get_type_hints(cls.execute).get("return")
        if execute_return_type is None:
            return False

        if not (hasattr(execute_return_type, "__origin__") and execute_return_type.__origin__ in [dict, Dict]):
            return False

        return_type_keys = set(output_type_mapping.keys())
        if return_type_keys != set(output_type_mapping.keys()):
            return False

        return True

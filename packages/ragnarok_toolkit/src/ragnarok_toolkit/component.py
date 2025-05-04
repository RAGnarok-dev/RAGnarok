from abc import ABC, abstractmethod
from enum import StrEnum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypedDict,
    Union,
    get_type_hints,
)

from ragnarok_toolkit.vdb.qdrant_client import QdrantPoint, SearchPayloadDict


class ComponentIOType(StrEnum):
    """the supported input and output types for a component"""

    STRING = "STRING"
    STRING_LIST = "STRING_LIST"
    INT = "INT"
    FLOAT = "FLOAT"
    FLOAT_LIST = "FLOAT_LIST"
    FLOAT_LIST_LIST = "FLOAT_LIST_LIST"
    BYTES = "BYTES"
    BYTES_LIST = "BYTES_LIST"
    VEC_POINT = "VEC_POINT"
    VEC_POINT_LIST = "VEC_POINT_LIST"
    SEARCH_PAYLOAD_DICT = "SEARCH_PAYLOAD_DICT"
    SEARCH_PAYLOAD_DICT_LIST = "SEARCH_PAYLOAD_DICT_LIST"

    @property
    def python_type(self):
        return TYPE_MAPPING[self]


TYPE_MAPPING = {
    ComponentIOType.INT: int,
    ComponentIOType.FLOAT: float,
    ComponentIOType.STRING: str,
    ComponentIOType.STRING_LIST: List[str],
    ComponentIOType.BYTES: bytes,
    ComponentIOType.BYTES_LIST: List[bytes],
    ComponentIOType.FLOAT_LIST: List[float],
    ComponentIOType.FLOAT_LIST_LIST: List[List[float]],
    ComponentIOType.VEC_POINT: QdrantPoint,
    ComponentIOType.VEC_POINT_LIST: List[QdrantPoint],
    ComponentIOType.SEARCH_PAYLOAD_DICT: SearchPayloadDict,
    ComponentIOType.SEARCH_PAYLOAD_DICT_LIST: List[SearchPayloadDict],
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
    def get_detail(cls) -> Dict[str, Tuple[ComponentInputTypeOption, ...] | tuple[ComponentOutputTypeOption, ...]]:
        return {
            "input_options": cls.input_options(),
            "output_options": cls.output_options(),
        }

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
        for input_option in input_options:
            param_name = input_option["name"]
            hint_type = execute_params.get(param_name)
            allowed_types = {io_type.python_type for io_type in input_option.get("allowed_types")}

            if input_option.get("required"):
                if hint_type not in allowed_types:
                    return False
            else:
                # optional param
                if (
                    hint_type is not None
                    and hasattr(hint_type, "__origin__")
                    and (hint_type.__origin__ is Optional or hint_type.__origin__ is Union)
                ):
                    # extract the inner type from Optional
                    actual_types = {arg for arg in hint_type.__args__ if arg is not type(None)}
                    if not actual_types.issubset(allowed_types):
                        return False
                else:
                    return False

        # TODO is it possible to validate output value here
        return True

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"Class {cls.__name__} and its subclasses cannot be instantiated.")

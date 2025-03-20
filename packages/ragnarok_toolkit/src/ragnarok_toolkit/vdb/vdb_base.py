from abc import ABC


class VdbBase(ABC):
    """
    base class for a vector database
    """

    def __init__(self, name: str):
        object.__setattr__(self, "_name", name)

    def __setattr__(self, name, value):
        if name == "_name":
            raise AttributeError("can't modify name once it's set")
        object.__setattr__(self, name, value)

    @property
    def name(self):
        return self._name

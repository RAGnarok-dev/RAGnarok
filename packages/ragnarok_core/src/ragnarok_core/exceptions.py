class DuplicateComponentError(Exception):
    def __init__(self, *, component_name: str) -> None:
        self.message = f"component {component_name} is already registered"
        super().__init__(self.message)


class InvalidComponentHintError(Exception):
    def __init__(self, *, component_name: str) -> None:
        self.message = f"component {component_name} hint is invalid"
        super().__init__(self.message)

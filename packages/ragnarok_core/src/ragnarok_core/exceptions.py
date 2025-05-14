class DuplicateComponentError(Exception):
    def __init__(self, *, component_name: str) -> None:
        self.message = f"component {component_name} is already registered"
        super().__init__(self.message)


class InvalidComponentHintError(Exception):
    def __init__(self, *, component_name: str) -> None:
        self.message = f"component {component_name} hint is invalid"
        super().__init__(self.message)


class PipelineNotFoundError(Exception):
    def __init__(self, pipeline_id: int) -> None:
        self.message = f"pipeline with the id {pipeline_id} not does not exists"
        super().__init__(self.message)

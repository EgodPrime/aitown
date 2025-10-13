from typing import Protocol, TypeVar, Generic, List, Optional

T = TypeVar('T', covariant=True)

class Model(Protocol, Generic[T]):
    def model_dump(self) -> dict: ...
    def model_validate(self, data: dict) -> T: ...
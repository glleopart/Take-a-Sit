from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Seat:
    id: int
    row: int
    col: int
    purchase_id: Optional[int] = None

    @property
    def assigned(self) -> bool:
        return self.purchase_id is not None


@dataclass
class Purchase:
    id: int
    num_seats: int
    order: int


@dataclass
class AssignmentResult:
    algorithm_name: str
    assignments: dict
    metrics: dict
    elapsed_time: float = 0.0
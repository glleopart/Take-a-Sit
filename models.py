from dataclasses import dataclass
from typing import Optional


@dataclass
class Seat:
    id: int
    row: int
    col: int
    occupied: bool = False
    purchase_id: Optional[int] = None

    @property
    def available(self) -> bool:
        return not self.occupied and self.purchase_id is None


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
from dataclasses import dataclass
from typing import Optional


@dataclass
class Promokod:
    id: Optional[int] = None
    phrase: str = ''
    amount: int = 0
    bonus: int = 0
    badge_number: int = 0
    date_created: Optional[str] = None
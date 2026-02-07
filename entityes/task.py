from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Taski:
    id: Optional[int] = None
    description: str = ''
    price: int = 0
    bonus: int = 0
    status: str = 'new'
    creator: int = 0
    us: int = 0
    date_created: Optional[str] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
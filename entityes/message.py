from datetime import datetime

class Message:
    def __init__(
        self,
        id: int = None,
        user_id: int = None,
        adresat: str = None,
        badge_number: int = 0,
        text: str = None,
        status: str = "new",
        date_created: str = None
    ):
        self.id = id
        self.user_id = user_id
        self.adresat = adresat
        self.badge_number = badge_number
        self.text = text
        self.status = status if status in ("new", "answered") else "new"
        self.date_created = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if date_created is None
            else date_created
        )

    def update(self, new_message: "Message"):
        self.user_id = new_message.user_id
        self.adresat = new_message.adresat
        self.badge_number = new_message.badge_number
        self.text = new_message.text
        self.status = new_message.status

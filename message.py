def generate_message_id() -> str:
    from shortuuid import uuid

    return uuid()


# Enum for message sender
class Sender:
    HUMAN = "Human"
    CHATGPT = "ChatGPT"


class Message:
    def __init__(self, content: str, sender: str):
        self.id = generate_message_id()
        self.content = content
        self.sender = sender


class HumanMessage(Message):
    def __init__(self, content: str):
        super().__init__(content, Sender.HUMAN)


class AgentMessage(Message):
    def __init__(self, content: str):
        super().__init__(content, Sender.CHATGPT)

from enum import Enum

class Effect(Enum):
    NONE = 0
    ITALIC = 1
    BOLD = 2
    UNDERLINE = 3
    STRIKETHROUGH = 4
class Message:
    def __init__(self) -> None:
        self.message = ""
        self.effects = {
            Effect.NONE: "{}",
            Effect.ITALIC: "*{}*",
            Effect.BOLD: "**{}**",
            Effect.STRIKETHROUGH: "~~{}~~",
            Effect.UNDERLINE: "__{}__"
        }
        
    def getString(self):
        return self.message
    
    def addText(self, text: str, effect = Effect.NONE):
        self.message += self.effects[effect].format(text)
        return self
    
    def addLine(self, text: str, effect = Effect.NONE):
        self.message += self.effects[effect].format(text)
        self.message += "\n"
        return self
    
    def nextLine(self):
        self.message += "\n"
        return self
    
from nextcord.ext.commands import Bot

class BotTypeError (TypeError):
    def __init__(self, obj, *args: object) -> None:
        message = f"Expected an object of type `{type(Bot)}`, but received: {type(obj).__name__}"
        super().__init__(message, *args)

# class TableNameError (NameError):
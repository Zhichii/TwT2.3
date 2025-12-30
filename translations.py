lang = "zh"

def translate(key: str = ""):
    if key in translation:
        if lang in translation[key]:
            return translation[key][lang]
        else:
            return translation[key]["zh"]
    else:
        return key

translation = {
    "error": {
        "zh": "错误：",
        "en": "Error: ",
    },
    "error.chat.load": {
        "zh": "加载对话时`KEY`有问题",
        "en": "Failed to load chat because `KEY` was wrong",
    },
    "error.config.load": {
        "zh": "加载配置`CONFIG`时有问题",
        "en": "Failed to load config `CONFIG`",
    },
    "error.config.save": {
        "zh": "保存配置`CONFIG`时有问题",
        "en": "Failed to save config `CONFIG`",
    },
    "error.config.not_valid": {
        "zh": "配置中的`VAR`有问题",
        "en": "`VAR` in config is not valid"
    },
    "error.message.load": {
        "zh": "加载消息时`KEY`有问题",
        "en": "Failed to load message because `KEY` was wrong",
    },
    "error.message.type_unknown": {
        "zh": "我不认识消息类型`TYPE`",
        "en": "Unknown message type `TYPE`"
    },
    "whisper": {
        "zh": "……",
        "en": "... ",
    },
    "welcome": {
        "zh": "欢迎来到TwT2.3！",
        "en": "Welcome to TwT2.3! "
    },
    "chat.title": {
        "zh": "（TITLE）",
        "en": "(TITLE)"
    },
    "chat.new": {
        "zh": "新对话",
        "en": "New Chat"
    }
}
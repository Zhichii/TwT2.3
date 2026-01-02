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
        "ja": "エラー："
    },
    "error.config.load": {
        "zh": "加载配置`CONFIG`时有问题",
        "en": "Failed to load config `CONFIG`",
        "ja": "設定`CONFIG`の読み込みに失敗しました"
    },
    "error.config.save": {
        "zh": "保存配置`CONFIG`时有问题",
        "en": "Failed to save config `CONFIG`",
        "ja": "設定`CONFIG`の保存に失敗しました"
    },
    "error.config.not_valid": {
        "zh": "配置中的`VAR`有问题",
        "en": "`VAR` in config was not valid",
        "ja": "設定内の`VAR`が無効です"
    },
    "error.chat.load": {
        "zh": "加载对话时`KEY`有问题",
        "en": "Failed to load chat because `KEY` was wrong",
        "ja": "`KEY`が正しくないため、チャットの読み込みに失敗しました"
    },
    "error.message.load": {
        "zh": "加载消息时`KEY`有问题",
        "en": "Failed to load message because `KEY` was wrong",
        "ja": "`KEY`が正しくないため、メッセージの読み込みに失敗しました"
    },
    "error.message.type_unknown": {
        "zh": "我不认识消息类型`TYPE`",
        "en": "Unknown message type `TYPE`",
        "ja": "不明なメッセージタイプ`TYPE`です"
    },
    "error.provider.load": {
        "zh": "加载提供商时`KEY`有问题",
        "en": "Failed to load provider because `KEY` was wrong",
        "ja": "`KEY`が正しくないため、プロバイダーの読み込みに失敗しました"
    },
    "whisper": {
        "zh": "……",
        "en": "... ",
        "ja": "……"
    },
    "welcome": {
        "zh": "欢迎来到TwT2.3！",
        "en": "Welcome to TwT2.3! ",
        "ja": "TwT2.3へようこそ！"
    },
    "help": {
        "zh": "/new - 创建新的对话\n/models - 添加服务提供商或模型\n/exit - 退出",
        "en": "/new - Create a new chat\n/models - Add service providers or models\n/exit - Exit the program",
        "ja": "/new - 新しいチャットを作成\n/models - サービスプロバイダーまたはモデルを追加\n/exit - プログラムを終了"
    },
    "chat.title": {
        "zh": "（TITLE）",
        "en": "(TITLE)",
        "ja": "（TITLE）"
    },
    "chat.new": {
        "zh": "新对话",
        "en": "New Chat",
        "ja": "新規チャット"
    }
}
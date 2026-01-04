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
    "error.load": {
        "zh": "加载CATEGORY时`KEY`有问题，以`DEFAULT`代替",
        "en": "Failed to load CATEGORY because `KEY` was wrong, replacing with `DEFAULT`",
        "ja": "`KEY`が正しくないため、CATEGORYの読み込みに失敗しました"
    },
    "error.load.message": {
        "zh": "消息",
        "en": "message",
        "ja": "メッセージ",
    },
    "error.load.provider": {
        "zh": "提供商",
        "en": "provider",
        "ja": "プロバイダー"
    },
    "error.load.chat": {
        "zh": "对话",
        "en": "chat",
        "ja": "チャット"
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
        "zh": "/new - 创建新的对话\n/models - 添加提供商或选择当前模型\n/providers - 添加服务提供商或选择默认模型\n/exit - 退出",
        "en": "/new - Create a new chat\n/models - Add service providers or select a current model\n/providers - Add service providers or select a default model\n/exit - Exit the program",
        "ja": "/new - 新しいチャットを開始\n/models - サービスプロバイダーを追加、または利用モデルを選択\n/providers - サービスプロバイダーを追加、またはデフォルトモデルを選択\n/exit - プログラムを終了"
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
    },
    "providers.empty": {
        "zh": "（无）",
        "en": " (Empty) "
    }
}
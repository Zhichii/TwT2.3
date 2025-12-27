import translations
translations.lang = "zh"
from translations import translate as t

import os, json, copy
import log, msgs, providers
# 不要问我为什么不遵循规范

def log_test():
    log.error(t("error.config.load").replace("CONFIG","666"))
    log.whisper(t("error.config.load").replace("CONFIG","666"))
    log.hint(t("error.config.load").replace("CONFIG","666"))
    translations.lang = "en"
    log.error(t("error.config.load").replace("CONFIG","666"))
    log.whisper(t("error.config.load").replace("CONFIG","666"))
    log.hint(t("error.config.load").replace("CONFIG","666"))
    translations.lang = "zh"

def msg_test():
    c = msgs.Conversation("你是一个有帮助的助手。")
    c.append(msgs.UserMsg("你好"))
    c.append(msgs.AssistantMsg("你好。"))
    c.append(msgs.UserMsg("你是谁"))
    return c

def provider_test():
    c = msg_test()
    client1 = providers.OpenAIProvider("https://api.deepseek.com/v1", os.environ["DEEPSEEK_API_KEY"])
    client2 = providers.AnthropicProvider("https://api.deepseek.com/anthropic", os.environ["DEEPSEEK_API_KEY"])
    for client in (client1, client2, ):
        for i in client("deepseek-chat", c):
            print(i, end="", flush=True)

class Config:
    def __init__(self, path: str = "", default: dict = {}):
        self.path = path
        self.default = dict(default)
        self.data = dict(self.default)
        if (os.path.exists(path)):
            self.load()
        self.save() # 格式化
    def load(self):
        try:
            with open(self.path, "r") as fp:
                self.data = json.load(fp)
        except Exception as e:
            log.error(t("error.config.load").replace("CONFIG", self.path), e)
    def save(self):
        try:
            with open(self.path, "w") as fp:
                json.dump(self.data, fp, ensure_ascii=False, indent=4)
        except Exception as e:
            log.error(t("error.config.save").replace("CONFIG", self.path), e)
    def __repr__(self):
        return repr(self.data)
    def __getitem__(self, key: str = ""): # Returns a shallow copy
        if key in self.data:
            return self.data[key]
        # else: return None
    def __setitem__(self, key: str = "", value = None):
        self.data[key] = copy.deepcopy(value)
class Chats:
    def __init__(self, config : Config):
        self.config = config
    def verify(self):
        pass

class App:
    new_chat : bool = True
    def __init__(self):
        self.cfg = Config("config.json", {"providers":[],"model":[],"chat":None,"chats":[]})
    def run(self):
        self.load_chat()
    def load_chat(self):
        # 验证变量
        if isinstance(self.cfg["chat"], int) or self.cfg["chat"] is None: pass
        else:
            log.error(t("error.config.not_valid").replace("VAR", "chat"))
            self.cfg["chat"] = None
        if isinstance(self.cfg["chats"], list): pass
        else: 
            log.error(t("error.config.not_valid").replace("VAR", "chats"))
            self.cfg["chats"] = []
            self.cfg["chat"] = None
        if isinstance(self.cfg["chat"], int):
            if (self.cfg["chat"] < 0) or (self.cfg["chat"] >= len(self.cfg["chats"])):
                log.error(t("error.config.not_valid").replace("VAR", "chat"))
                self.cfg["chat"] = None

        if self.cfg["chat"] is None:
            log.hint(t("chat.name").replace("NAME", t("new_chat")))
        else:
            self.new_chat = False
            if isinstance(self.cfg["chat"], int):
                a_chat = self.cfg["chats"][self.cfg["chat"]]
                if not isinstance(a_chat, dict):
                    log.error(t("error.config.not_valid").replace("VAR", "chats.%d"%(self.cfg["chat"],)))
                    del self.cfg["chats"][self.cfg["chat"]]
                    self.cfg["chat"] = None
                else:
                    if ("name" not in a_chat):
                        log.error(t("error.config.not_valid").replace("VAR", "chats.%d.name"%(self.cfg["chat"],)))
                        a_chat["name"] = t("new_chat")
                    if (not isinstance(a_chat["name"], str)):
                        a_chat["name"] = repr(a_chat["name"])
                    log.hint(t("chat.name").replace("NAME", a_chat["name"]))
        self.cfg.save()

app = App()
app.run()

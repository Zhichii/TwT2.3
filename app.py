import translations
translations.lang = "zh"
from translations import translate as t

import os, json, copy, readline
import log, msgs, providers
# from my_io import linux_input # deprecated. use readline instead (wait for me to test on Windows)
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
    c = msgs.MsgTree("你是一个有帮助的助手。")
    c.append(msgs.UserMsg("你好"))
    c.append(msgs.AssistantMsg("你好。"))
    c.append(msgs.UserMsg("你是谁"))
    #print(c)
    c = c.store()
    c = msgs.MsgTree.load(c)
    #print(c)
    return c

def provider_test():
    c = msg_test()
    client1 = providers.OpenAIProvider("https://api.deepseek.com/v1", os.environ["DEEPSEEK_API_KEY"])
    client2 = providers.AnthropicProvider("https://api.deepseek.com/anthropic", os.environ["DEEPSEEK_API_KEY"])
    for client in (client1, client2, ):
        print(client._to_format(c))
        for i in client("deepseek-chat", c):
            print(i, end="", flush=True)

class Config:
    def __init__(self, path: str = "", default: dict = {}):
        self.path = path
        self.default = copy.deepcopy(default)
        self.data = copy.deepcopy(self.default)
        if (os.path.exists(path)):
            self.load()
        self.save() # 格式化
    def load(self):
        try:
            if not self.path: raise ValueError("path is nullstr")
            with open(self.path, "r") as fp:
                self.data = json.load(fp)
        except Exception as e:
            log.error(t("error.config.load").replace("CONFIG", self.path), e)
    def save(self):
        try:
            if not self.path: raise ValueError("path is nullstr")
            with open(self.path+".tmp", "w") as fp:
                json.dump(self.data, fp, ensure_ascii=False, indent=4)
            os.replace(self.path+".tmp",self.path)
        except Exception as e:
            log.error(t("error.config.save").replace("CONFIG", self.path), e)
    def __repr__(self):
        return repr(self.data)
    def has(self, key : str = ""):
        return key in self.data
    def __getitem__(self, key : str = ""): # Returns a shallow copy
        if key in self.data:
            return self.data[key]
        # else: return None
    def __setitem__(self, key: str = "", value = None):
        self.data[key] = copy.deepcopy(value)
class Chat:
    title : str
    msg_tree : msgs.MsgTree
    def __init__(self):
        self.title = t("chat.new")
        self.msg_tree = msgs.MsgTree()
    @staticmethod
    def load(data : dict):
        the_chat = Chat()
        if "title" not in data:
            log.error(t("error.chat.load").replace("KEY", "title"))
            the_chat.title = t("chat.new")
        elif (not isinstance(data["title"], str)):
            the_chat.title = repr(data["title"])
        else:
            the_chat.title = data["title"]
        if "msg_tree" not in data:
            log.error(t("error.chat.load").replace("KEY", "msg_tree"))
            the_chat.msg_tree = msgs.MsgTree()
        else:
            the_chat.msg_tree = msgs.MsgTree.load(data["msg_tree"])
        return the_chat
    def store(self):
        return {"title": self.title, "msg_tree": self.msg_tree.store()}
    def append(self, msg : msgs.MsgBase):
        self.msg_tree.append(msg)
    
class Chats:
    cfg : Config
    chat_index : int | None # 若为None则是新对话
    the_chat : Chat | None # 当前的对话
    def __init__(self, cfg : Config):
        self.cfg = cfg
        if cfg.has("chat_index") and (isinstance(self.cfg["chat_index"], int) or self.cfg["chat_index"] is None): pass
        else:
            log.error(t("error.config.not_valid").replace("VAR", "chat_index"))
            self.cfg["chat_index"] = None
        if not isinstance(self.cfg["chats"], list):
            log.error(t("error.config.not_valid").replace("VAR", "chats"))
            self.cfg["chats"] = []
            self.cfg["chat_index"] = None
        if isinstance(self.cfg["chat_index"], int):
            if (self.cfg["chat_index"] < 0) or (self.cfg["chat_index"] >= len(self.cfg["chats"])):
                log.error(t("error.config.not_valid").replace("VAR", "chat_index"))
                self.cfg["chat_index"] = None
        self.chat_index = self.cfg["chat_index"]
        self.cfg.save()
    def load_chat(self):
        if isinstance(self.chat_index, int): # 不是None
            chat_dict = self.cfg["chats"][self.chat_index]
            if not isinstance(chat_dict, dict):
                log.error(t("error.config.not_valid").replace("VAR", "chats.%d"%(self.chat_index,)))
                del self.cfg["chats"][self.chat_index]
                self.chat_index = None
                self.the_chat = None
                self.cfg["chat_index"] = self.chat_index
            else:
                self.the_chat = Chat.load(chat_dict)
                self.cfg["chats"][self.chat_index] = self.the_chat.store() # 修复可能的错误
        else: # 是None
            self.the_chat = None
        self.cfg.save()
        if not self.the_chat:
            log.hint(t("chat.title").replace("TITLE", t("chat.new")))
        else:
            log.hint(t("chat.title").replace("TITLE", self.the_chat.title))
    def user_msg_send(self, msg : str):
        if self.the_chat is None: # 创建新的对话
            self.the_chat = Chat()
            self.chat_index = len(self.cfg["chats"])
            self.cfg["chats"].append({})
            self.cfg["chat_index"] = self.chat_index
        self.the_chat.append(msgs.UserMsg(msg))
        self.cfg["chats"][self.chat_index] = self.the_chat.store()
        self.cfg.save()
        # post
        client = providers.AnthropicProvider("https://api.deepseek.com/anthropic", os.environ["DEEPSEEK_API_KEY"])
        for i in client("deepseek-chat", self.the_chat.msg_tree):
            print(i, end="", flush=True)

class App:
    cfg : Config
    chats : Chats
    def __init__(self):
        self.cfg = Config("config.json", {"providers":[],"model":[],"chat_index":None,"chats":[]})
        self.chats = Chats(self.cfg)
    def run(self):
        self.load_chat()
        self.chats.user_msg_send(input(">>> "))
    def load_chat(self):
        self.chats.load_chat()

app = App()
app.run()

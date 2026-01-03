import translations
translations.lang = "zh"

import os, json, readline
import log, msgs, providers
from copy import deepcopy
from getch import getkey
from tools import safe_get, merge
from typing import Literal, Any
from translations import translate as t
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
        self.default = deepcopy(default)
        self.data = deepcopy(self.default)
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
        self.data[key] = deepcopy(value)

# 内置一些预设的思考
siliconflow_think_on = {"enable_thinking": True}
siliconflow_think_on = {"enable_thinking": False}
deepseek_think_on = {"thinking": {"type": "enabled"}}
deepseek_think_off = {"thinking": {"type": "disabled"}}
class Model:
    name : str
    id : str
    support_thinking : bool
    support_thinking_control : bool
    support_vision : bool
    default_thinking : bool
    default_temperature : float | None
    default_max_tokens : int
    def __init__(self, name : str, id : str):
        self.name = name
        self.id = id
        self.support_thinking = False
        self.default_thinking = False
        self.default_temperature = None
        self.default_max_tokens = 4096
        self.think_on = {}
        self.think_off = {}
    def config_thinking(self, on : dict[str, Any], off : dict[str, Any], support_thinking_control : bool = False):
        self.support_thinking = True
        self.think_on = deepcopy(on)
        self.think_off = deepcopy(off)
        self.support_thinking_control = support_thinking_control
    def config_vision(self, support_vision : bool = True):
        self.support_vision = support_vision
    def set_default_thinking(self, thinking : bool = False): self.default_thinking = thinking
    def set_default_temperature(self, temperature : float | None = None): self.default_temperature = temperature
    def set_default_max_tokens(self, max_tokens : int = 4096): self.default_max_tokens = max_tokens
    def generate(self, thinking : bool | None = None,
                       temperature : float | None = None,
                       max_tokens : int | None = None):
        data : dict[str, Any] = {}
        if self.support_thinking and self.support_thinking_control:
            if thinking is None: k = self.default_thinking
            else: k = thinking
            if k: merge(data, self.think_on)
            else: merge(data, self.think_off)
        if temperature is not None: data["temperature"] = temperature
        elif self.default_temperature is not None: data["temperature"] = self.default_temperature
        # else: 不加入
        if max_tokens is not None: real_max_tokens = max_tokens
        else: real_max_tokens = self.default_max_tokens
        real_max_tokens = max(real_max_tokens, 0) # 确保大于0
        return (self.id, real_max_tokens, data)
    def store(self) -> dict[str, Any]:
        data = {"name": self.name,
                "id": self.id,
                "default_thinking": self.default_thinking,
                "default_temperature": self.default_temperature,
                "default_max_tokens": self.default_max_tokens,
                "support_thinking": self.support_thinking,
                "support_thinking_control": self.support_thinking_control,
                "think_on": deepcopy(self.think_on),
                "think_off": deepcopy(self.think_off),
                "support_vision": self.support_vision}
        return data
    @staticmethod
    def load(data : dict) -> "Model":
        name = safe_get(data, str, "name", "model", "GPT-4")
        id = safe_get(data, str, "id", "model", "gpt-4")
        a : Model = Model(name, id)
        a.default_thinking = safe_get(data, bool, "default_thinking", "model", False)
        a.default_temperature = safe_get(data, (float, type(None), ), "default_temperature", "model", None)
        a.default_max_tokens = safe_get(data, int, "default_max_tokens", "model", 4096)
        a.support_thinking = safe_get(data, bool, "support_thinking", "model", False)
        a.support_thinking_control = safe_get(data, bool, "support_thinking_control", "model", False)
        if a.support_thinking:
            a.think_on = deepcopy(safe_get(data, dict, "think_on", "model", {}))
            a.think_off = deepcopy(safe_get(data, dict, "think_off", "model", {}))
        a.support_vision = safe_get(data, bool, "support_vision", "model", False)
        return a

class Provider:
    name : str
    base_url : str
    api_key : str
    models : list[Model]
    def __init__(self, name : str, base_url : str, api_key : str, type : Literal["openai", "anthropic"]):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        if type == "anthropic":
            self.type = type
            self.client = providers.AnthropicProvider(base_url, api_key)
        else: #if (type == "openai"): # Fallback to OpenAI
            self.type = "openai"
            self.client = providers.OpenAIProvider(base_url, api_key)
        self.models = []
    @staticmethod
    def load(data : dict):
        name = safe_get(data, str, "name", "provider", "OpenAI")
        base_url = safe_get(data, str, "base_url", "provider", "https://api.openai.com/v1")
        api_key = safe_get(data, str, "api_key", "provider", "sk-?")
        type = safe_get(data, str, "type", "provider", "openai")
        a = Provider(name, base_url, api_key, type)
        models_ = safe_get(data, list, "models", "provider", [])
        models = []
        for model in models_:
            models.append(Model.load(model))
        a.models = models
        return a
    def store(self) -> dict[str, Any]:
        return {"name": self.name,
                "base_url": self.base_url,
                "api_key": self.api_key,
                "type": self.type, 
                "models": [model.store() for model in self.models]}
    def __len__(self) -> int: return len(self.models)
    def generate(self, model : int, **kwargs):
        if 0 <= model <= len(self):
            return self.models[model].generate(**kwargs)
        else:
            log.error("model index out of bound")

class Providers:
    cfg : Config
    providers : list[Provider]
    # TODO: self.cfg["provider_index"], self.cfg["provider_model"]
    def __init__(self, cfg : Config):
        self.cfg = cfg
        self.providers = []
        if cfg.has("providers"):
            providers_ = cfg["providers"]
            if isinstance(providers_, list):
                providers = []
                for provider in providers_:
                    if isinstance(provider, dict):
                        p = Provider.load(provider)
                        self.providers.append(p)
                        providers.append(p.store())
                cfg["providers"] = providers
        else:
            log.error(t("error.config.not_valid").replace("VAR", "providers"))
            cfg["providers"] = []
        self.cfg.save()
    def __len__(self) -> int: return len(self.providers)
    def generate(self, provider : int, model : int, **kwargs):
        if 0 <= provider <= len(self):
            return self.providers[provider].generate(model, **kwargs)
        else:
            log.error("provider index out of bound")
    def choose(self):
        groups = []
        for provider in self.providers:
            group = []
            for model in provider.models:
                thinking = " 🤔" if model.support_thinking else ""
                vision = " 👁️" if model.support_vision else ""
                group.append(f"{model.name} ({model.id}){thinking}{vision}")
            groups.append(Menu.ItemGroup(f"{provider.name} ({provider.base_url})", *group))
        menu = Menu.from_groups(groups, 0, 0)
        menu.show()
        getkey()

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
    def get_last_msg_id(self) -> None | int:
        return self.msg_tree.get_last_msg_id()
    def ends_with_assistant(self):
        return self.msg_tree.ends_with_assistant()
    def complete_last_assistant(self, idx : int, msg : msgs.AssistantMsg | msgs.ReasonAssistantMsg):
        self.msg_tree.complete_last_assistant(idx, msg)
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
        if msg:
            self.the_chat.append(msgs.UserMsg(msg))
            self.cfg["chats"][self.chat_index] = self.the_chat.store()
            self.cfg.save()
        # post
        #client = providers.AnthropicProvider("https://api.deepseek.com/anthropic", os.environ["DEEPSEEK_API_KEY"])
        #client = providers.OpenAIProvider("https://api.deepseek.com/v1", os.environ["DEEPSEEK_API_KEY"])
        ends_with_assistant = self.the_chat.ends_with_assistant()
        reasons = []
        contents = []
        interrupt = False
        #print(client._to_format(self.the_chat.msg_tree))
        #deepseek_chat = Model("DeepSeek Chat", "deepseek-chat")
        #deepseek_chat.config_thinking(deepseek_think_on, deepseek_think_off)
        provider = Provider.load({
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": os.environ["DEEPSEEK_API_KEY"],
            "type": "openai",
            "models": [
                {
                    "name": "DeepSeek",
                    "id": "deepseek-chat",
                    "default_thinking": False,
                    "default_temperature": None,
                    "default_max_tokens": 4096,
                    "support_thinking": True,
                    "think_on": {"thinking":{"type":"enabled"}},
                    "think_off": {"thinking":{"type":"disabled"}},
                    "support_vision": False
                }
            ]
        })
        gen = provider.generate(0)
        try:
            for i in provider.client(gen[0], self.the_chat.msg_tree, gen[1], True, **gen[2]):
                print(i[1], end="", flush=True)
                import sys
                sys.stdout.flush()
                sys.stdin.flush()
                if i[0] == "reason":
                    reasons.append(i[1])
                if i[0] == "content":
                    contents.append(i[1])
        except KeyboardInterrupt as e:
            interrupt = True
        reason = "".join(reasons)
        content = "".join(contents)
        # 因为续写似乎并不是都支持
        if False and ends_with_assistant:
            last_msg_id = self.the_chat.get_last_msg_id()
            if reason: self.the_chat.complete_last_assistant(last_msg_id, msgs.ReasonAssistantMsg(content, reason, interrupt))
            else: self.the_chat.complete_last_assistant(last_msg_id, msgs.AssistantMsg(content, interrupt))
        else:
            if reason: self.the_chat.append(msgs.ReasonAssistantMsg(content, reason, interrupt))
            else: self.the_chat.append(msgs.AssistantMsg(content, interrupt))
        self.cfg["chats"][self.chat_index] = self.the_chat.store()
        self.cfg.save()

class Menu:
    class Item:
        content : str
        is_group_title : bool
        def __init__(self, content : str, is_group_title : bool = False):
            self.content = content
            self.is_group_title = is_group_title
    class ItemGroup:
        title : str
        items : list[str]
        def __init__(self, title : str, *args : str):
            self.title = title
            self.items = []
            for i in args:
                self.items.append(i)
    def __init__(self, items : list[Item | str], index : int | None):
        self.items = []
        if len(items) > 0:
            for i in items:
                if isinstance(i, str):
                    self.items.append(Menu.Item(i))
                elif isinstance(i, Menu.Item):
                    self.items.append(deepcopy(i))
        self.index = index
    @staticmethod
    def from_groups(items : list[ItemGroup], group_index : int, group_item : int):
        _items = []
        idx = 0
        index  = None
        gidx = 0
        for item_group in items:
            gitm = 0
            _items.append(Menu.Item(item_group.title, True))
            for item in item_group.items:
                _items.append(Menu.Item(item))
                if (gidx == group_index) and (gitm == group_item):
                    index = idx
                gitm += 1
                idx += 1
            gidx+=1
        return Menu(_items, index)
    def show(self):
        if len(self.items) == 0:
            print("(Empty)")
        else:
            if (self.index is None):
                self.index = 0
            idx = 0
            for i in self.items:
                if (i.is_group_title):
                    print(i.content)
                else:
                    if idx == self.index:
                        print(f" * {i.content}")
                    else:
                        print(f"   {i.content}")
                    idx += 1

class App:
    cfg : Config
    chats : Chats
    def __init__(self):
        self.cfg = Config("config.json", {"providers":[],"provider_index":None,"provider_model":None,"chat_index":None,"chats":[]})
        self.chats = Chats(self.cfg)
        self.providers = Providers(self.cfg)
    def run(self):
        self.load_chat()
        while True:
            try:
                i = input(">>> ")
            except (KeyboardInterrupt, EOFError):
                i = "/exit"
            if i.startswith("/new"):
                self.chats.chat_index = None
                self.chats.load_chat()
            elif i.startswith("/model"):
                self.providers.choose()
            elif i.startswith("/exit"):
                break
            elif i.startswith("/"):
                print(t("help"))
            else:
                msg = i
                self.chats.user_msg_send(msg)
                print()
    def load_chat(self):
        self.chats.load_chat()

if __name__ == "__main__":
    app = App()
    app.run()
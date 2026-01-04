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

# 处理一下，不然会出现莫名其妙的问题。
for name in os.environ.keys():
    if len(name) > 5 and name[-6] == "_" and name[-5:].lower() == "proxy":
        del os.environ[name]

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
    support_tools : bool
    default_thinking : bool
    default_temperature : float | None
    default_max_tokens : int
    def __init__(self, name : str, id : str):
        self.name = name
        self.id = id
        self.support_thinking = False
        self.support_thinking_control = False
        self.support_vision = False
        self.support_tools = False
        self.default_thinking = False
        self.default_temperature = None
        self.default_max_tokens = 4096
        self.think_on = {}
        self.think_off = {}
    def mark_support_thinking(self, on : dict[str, Any], off : dict[str, Any], support_thinking_control : bool = False):
        self.support_thinking = True
        self.think_on = deepcopy(on)
        self.think_off = deepcopy(off)
        self.support_thinking_control = support_thinking_control
    def mark_support_vision(self): self.support_vision = True
    def mark_support_tools(self): self.support_tools = True
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
                "support_vision": self.support_vision,
                "support_tools": self.support_tools}
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
        a.support_tools = safe_get(data, bool, "support_tools", "model", False)
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
    provider_index : int | None
    provider_model : int | None
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
        if cfg.has("provider_index") and isinstance(cfg["provider_index"], (int, type(None),)):
            self.provider_index = cfg["provider_index"]
        else:
            log.error(t("error.config.not_valid").replace("VAR", "provider_index"))
            self.provider_index = None
        if cfg.has("provider_model") and isinstance(cfg["provider_model"], (int, type(None),)):
            self.provider_model = cfg["provider_model"]
        else:
            log.error(t("error.config.not_valid").replace("VAR", "provider_model"))
            self.provider_model = None
        self.cfg.save()
    def __len__(self) -> int: return len(self.providers)
    def generate(self, provider : int, model : int, **kwargs):
        if 0 <= provider <= len(self):
            return self.providers[provider].generate(model, **kwargs)
        else:
            log.error("that can't be true")
            return None
    def choose(self, provider_index : int | None, provider_model : int | None):
        # 先确认provider_index和provider_model在合法区间内
        if len(self.providers) == 0:
            provider_index = None
            provider_model = None
        else:
            if provider_index is not None:
                provider_index = max(provider_index, 0)
                provider_index = min(provider_index, len(self.providers)-1)
            provideri = 0
            for provider in self.providers:
                if len(provider.models) == 0:
                    if provider_index == provideri:
                        provider_model = None
                else:
                    if provider_index == provideri:
                        if provider_model is None:
                            provider_model = 0
                        else:
                            provider_model = max(provider_model, 0)
                            provider_model = min(provider_model, len(provider.models)-1)
                    if provider_index is None:
                        provider_index = provideri
                        provider_model = 0
                provideri += 1
            if provider_index is None: # 逛了一圈没找到模型
                provider_index = 0
                provider_model = None # 这实际上是那个providers.empty占位符\
        # 在由provider_index和provider_model找到对应的index
        target = None
        index = 0
        provideri = 0
        for provider in self.providers:
            if len(provider.models) == 0:
                if provider_index == provideri:
                    target = index
                    break
                index += 1
            else:
                if provider_index == provideri:
                    target = index + provider_model
                    break
                index += len(provider.models)
            provideri += 1
        # 开始循环
        while True:
            # 渲染
            index = 0
            cache = []
            if len(self.providers) == 0:
                cache.append(t("providers.empty"))
                provider_index = None
                provider_model = None
            else:
                # 因为此时至少有一个提供商
                provideri = 0
                for provider in self.providers:
                    cache.append(f"{provider.name} ({provider.base_url})")
                    modeli = 0
                    if len(provider.models) == 0:
                        choose = "   "
                        if index == target:
                            choose = " * "
                            provider_index = provideri
                            provider_model = None
                        cache.append(f"{choose}{t("providers.empty")}")
                        index += 1
                    else:
                        for model in provider.models:
                            choose = "   "
                            if index == target:
                                choose = " * "
                                provider_index = provideri
                                provider_model = modeli
                            thinking = " 🤔" if model.support_thinking else ""
                            vision = " 👁️" if model.support_vision else ""
                            tools = " 🔧" if model.support_tools else ""
                            cache.append(f"{choose}{model.name} ({model.id}){thinking}{vision}{tools}")
                            modeli += 1
                            index += 1
                    provideri += 1
            cache = "\n".join(cache)
            print("\033c", end=cache+"\n"+t("help.models"))
            k = getkey()
            if k in ['z', 'Z', '\x04', '\r', '\n', '\x03','x','X']:
                break
            if k in ['w','W',('UP',b'\x1b[A')]:
                if isinstance(target, int):
                    if target > 0: target -= 1
            if k in ['s','S',('DOWN',b'\x1b[B')]:
                if isinstance(target, int):
                    if target + 1 < index: target += 1 # index实际上作为所有可选中的总数
        print("\033c", end="")
        return provider_index, provider_model

class Chat:
    title : str
    msg_tree : msgs.MsgTree
    provider_index : int | None
    provider_model : int | None
    def __init__(self):
        self.title = t("chat.new")
        self.msg_tree = msgs.MsgTree()
    @staticmethod
    def load(data : dict):
        the_chat = Chat()
        the_chat.title = safe_get(data, str, "title", "chat", t("chat.new"))
        msg_tree_json = safe_get(data, dict, "msg_tree", "chat", None)
        if msg_tree_json is None:
            the_chat.msg_tree = msgs.MsgTree()
        else:
            the_chat.msg_tree = msgs.MsgTree.load(msg_tree_json)
        the_chat.provider_index = safe_get(data, (int,type(None),), "provider_index", "chat", None)
        the_chat.provider_model = safe_get(data, (int,type(None),), "provider_model", "chat", None)
        return the_chat
    def store(self):
        return {"title": self.title,
                "msg_tree": self.msg_tree.store(),
                "provider_index": self.provider_index,
                "provider_model": self.provider_model}
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
    providers : Providers
    chat_index : int | None # 若为None则是新对话
    the_chat : Chat | None # 当前的对话
    ready_provider_index : int | None
    ready_provider_model : int | None
    def __init__(self, cfg : Config, providers : Providers):
        self.cfg = cfg
        self.providers = providers
        self.ready_provider_index = self.providers.provider_index
        self.ready_provider_model = self.providers.provider_model
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
    # 向**the_chat（当前对话）**发送消息
        if self.the_chat is None: # 创建新的对话
            self.the_chat = Chat()
            self.the_chat.provider_index = self.ready_provider_index
            self.the_chat.provider_model = self.ready_provider_model
            self.chat_index = len(self.cfg["chats"])
            self.cfg["chats"].append({})
            self.cfg["chat_index"] = self.chat_index
        if msg:
            self.the_chat.append(msgs.UserMsg(msg))
            self.cfg["chats"][self.chat_index] = self.the_chat.store()
            self.cfg.save()
        ends_with_assistant = self.the_chat.ends_with_assistant()
        reasons = []
        contents = []
        interrupt = False
        #print(client._to_format(self.the_chat.msg_tree))
        if (self.the_chat.provider_index is None) or (self.the_chat.provider_model is None):
            log.error(t("error.provider.no"))
            return
        gen = self.providers.generate(self.the_chat.provider_index, self.the_chat.provider_model)
        if gen is None:
            log.error("that can't be true! ")
            return
        state : Literal["content", "reason"] = "content"
        try:
            for i in self.providers.providers[self.the_chat.provider_index].client(gen[0], self.the_chat.msg_tree, gen[1], True, **gen[2]):
                if (i[0] != state):
                    if i[0] == "reason": log.console.print("Thinking...", style="bold #808080")
                    else:
                        print()
                        log.console.print("... done thinking", style="bold #808080")
                        print()
                    state = i[0]
                if state == "reason": log.console.print(i[1], style="#808080", end="")
                if state == "content": print(i[1], end="", flush=True)
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
    def get_model(self) -> tuple[int|None, int|None]:
    # 获取**the_chat（当前对话）**的模型
        if self.the_chat is not None:
            return self.the_chat.provider_index, self.the_chat.provider_model
        else:
            return self.ready_provider_index, self.ready_provider_model
    def set_model(self, provider_index : int | None, provider_model : int | None):
    # 获取**the_chat（当前对话）**的模型
        if self.the_chat is not None:
            self.the_chat.provider_index = provider_index
            self.the_chat.provider_model = provider_model
        else:
            self.ready_provider_index = provider_index
            self.ready_provider_model = provider_model

class App:
    cfg : Config
    providers : Providers
    chats : Chats
    def __init__(self):
        self.cfg = Config("config.json", {"providers":[],"provider_index":None,"provider_model":None,"chat_index":None,"chats":[]})
        self.providers = Providers(self.cfg)
        self.chats = Chats(self.cfg, self.providers)
    def run(self):
        self.load_chat()
        ready_model = (self.cfg["provider_index"], self.cfg["provider_model"])
        while True:
            try:
                i = input(">>> ")
            except (KeyboardInterrupt, EOFError):
                i = "/exit"
            if i.startswith("/new"):
                self.chats.chat_index = None
                self.chats.load_chat()
                self.chats.ready_provider_index = self.providers.provider_index
                self.chats.ready_provider_model = self.providers.provider_model
            elif i.startswith("/model"):
                model = self.chats.get_model()
                if model is not None:
                    self.chats.set_model(*(self.providers.choose(*model)))
            elif i.startswith("/provider"):
                self.cfg["provider_index"], self.cfg["provider_model"] = self.providers.choose(self.cfg["provider_index"], self.cfg["provider_model"])
                self.cfg.save()
            elif i.startswith("/exit"):
                break
            elif i.startswith("/"):
                print(t("help"))
            else:
                msg = i
                self.chats.user_msg_send(msg)
                print()
        print()
    def load_chat(self):
        self.chats.load_chat()

if __name__ == "__main__":
    app = App()
    app.run()
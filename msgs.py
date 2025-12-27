import json
import log
import time
from translations import translate as t

class MsgBase:
    role: str = ""
    content: str = ""
    def __init__(self, role: str = "", content = ""):
        self.role = role
        self.content = content
    def __repr__(self):
        return str(self.store())
    def store(self):
        return {"role": self.role, "content": self.content}
    @staticmethod
    def load(data : dict):
        return MsgBase(data["role"], data["content"])
class UserMsg(MsgBase):
    def __init__(self, content: str = ""):
        super().__init__("user", content)
    @staticmethod
    def load(data : dict):
        return UserMsg(data["content"])
class AssistantMsg(MsgBase):
    def __init__(self, content: str = ""):
        super().__init__("assistant", content)
    def store(self):
        data = super().store()
        return data
    @staticmethod
    def load(data : dict):
        return AssistantMsg(data["content"])
class ReasonAssistantMsg(MsgBase):
    reason: str = ""
    def __init__(self, content: str = "", reason: str = ""):
        super().__init__("assistant", content)
        self.reason = reason
    def store(self):
        data = super().store()
        data["reason"] = self.reason
        return data
    @staticmethod
    def load(data : dict):
        return ReasonAssistantMsg(data["content"], data["reason"])
class Conversation:
    class MsgWrapper:
        type : str
        msg : MsgBase
        parnet : int | None
        children : list[int]
        child : int | None
        time : float
        def __init__(self, msg : MsgBase, parent : int | None):
            self.type = type(msg).__name__
            self.msg = msg
            self.parent = parent
            self.children = []
            self.child = None
            self.time = time.time()
        def __repr__(self):
            return str(self.store())
        def store(self):
            return {"type": self.type, "msg": self.msg.store(), "time": self.time, "parent": self.parent, "children": list(self.children), "child": self.child}
        @staticmethod
        def load(data : dict):
            msg_type = MsgBase
            if (data["type"] == "MsgBase"): msg_type = MsgBase
            if (data["type"] == "UserMsg"): msg_type = UserMsg
            if (data["type"] == "AssistantMsg"): msg_type = AssistantMsg
            if (data["type"] == "ReasonAssistantMsg"): msg_type = ReasonAssistantMsg
            if (data["type"] not in ("MsgBase", "UserMsg", "AssistantMsg", "ReasonAssistantMsg",)):
                log.error(t("error.msgs.type_unknown").replace("TYPE", data["type"]))
            msg = Conversation.MsgWrapper(msg_type.load(data["msg"]), data["parent"])
            msg.time = data["time"]
            msg.children = list(data["children"])
            msg.child = data["child"]
            return msg
    conversation : list[MsgWrapper]
    def __init__(self, system : str = ""):
        self.conversation = []
        self.append(MsgBase()) # 根消息
        if system:
            self.append(MsgBase("system", system))
    def __repr__(self):
        return str(self.store())
    def store(self):
        return {'conversation': self.conversation}
    @staticmethod
    def load(data : dict):
        conversation = Conversation()
        conversation.conversation = data["conversation"]
        return conversation
    def append(self, msg : MsgBase):
        if len(self.conversation) == 0:
            self.conversation.append(Conversation.MsgWrapper(msg, None))
        else:
            cur = 0
            while self.conversation[cur].child is not None:
                cur = self.conversation[cur].children[self.conversation[cur].child]
            self.conversation[cur].children.append(len(self.conversation))
            self.conversation.append(Conversation.MsgWrapper(msg, cur))
            self.conversation[cur].child = len(self.conversation[cur].children)-1


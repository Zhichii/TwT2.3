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
        if "content" not in data:
            raise ValueError("`content` not in data")
        if "role" not in data:
            log.error(t("error.message.load").replace("KEY", "role"))
            return MsgBase("user", data["content"])
        return MsgBase(data["role"], data["content"])
class UserMsg(MsgBase):
    def __init__(self, content: str = ""):
        super().__init__("user", content)
    @staticmethod
    def load(data : dict):
        if "content" not in data:
            raise ValueError("`content` not in data")
        return UserMsg(data["content"])
class AssistantMsg(MsgBase):
    def __init__(self, content: str = ""):
        super().__init__("assistant", content)
    def store(self):
        data = super().store()
        return data
    @staticmethod
    def load(data : dict):
        if "content" not in data:
            raise ValueError("`content` not in data")
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
        if "content" not in data:
            raise ValueError("`content` not in data")
        if "reason" not in data:
            log.error(t("error.message.load").replace("KEY", "reason"))
            return AssistantMsg(data["content"])
        return ReasonAssistantMsg(data["content"], data["reason"])
class MsgTree:
    class MsgWrapper:
        type : str
        msg : MsgBase
        parent : int | None
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
            if "type" not in data:
                log.error(t("error.message.load").replace("KEY", "type"))
            msg_type = MsgBase
            if (data["type"] == "MsgBase"): msg_type = MsgBase
            if (data["type"] == "UserMsg"): msg_type = UserMsg
            if (data["type"] == "AssistantMsg"): msg_type = AssistantMsg
            if (data["type"] == "ReasonAssistantMsg"): msg_type = ReasonAssistantMsg
            if (data["type"] not in ("MsgBase", "UserMsg", "AssistantMsg", "ReasonAssistantMsg",)):
                log.error(t("error.message.type_unknown").replace("TYPE", data["type"]))
            msg = MsgTree.MsgWrapper(msg_type.load(data["msg"]), data["parent"])
            if ("time" not in data) or (not isinstance(data["time"], float)):
                log.error(t("error.message.load").replace("KEY", "time"))
                msg.time = 0.
            else: msg.time = data["time"]
            if ("children" not in data) or (not isinstance(data["children"], list)):
                log.error(t("error.message.load").replace("KEY", "children"))
                msg.children = list()
            else:
                flag = True
                for i in range(len(data["children"])):
                    if (not isinstance(data["children"][i], int)) or (data["children"][i] < 0):
                        log.error(t("error.message.load").replace("KEY", "children.%d"%(i,)))
                        flag = False
                        break
                if flag:
                    msg.children = list(data["children"])
                else:
                    log.error(t("error.message.load").replace("KEY", "children"))
                    msg.children = list()
            if ("child" not in data) or (not isinstance(data["child"], (int, type(None),))):
                log.error(t("error.message.load").replace("KEY", "child"))
                msg.child = len(msg.children)-1
                if (msg.child < 0): msg.child = None
            elif (isinstance(data["child"], int)) and ((data["child"] < 0) or (data["child"] >= len(data["children"]))):
                log.error(t("error.message.load").replace("KEY", "child"))
                msg.child = len(msg.children)-1
                if (msg.child < 0): msg.child = None
            else:
                msg.child = data["child"]
            return msg
    msg_list : list[MsgWrapper]
    def __init__(self, system : str = ""):
        self.msg_list = []
        self.append(MsgBase()) # 根消息
        self.append(MsgBase("system", system))
    def __repr__(self):
        return str(self.store())
    def store(self):
        return {'conversation': [i.store() for i in self.msg_list]}
    @staticmethod
    def load(data : dict):
        msg_tree = MsgTree()
        msg_tree.msg_list = [MsgTree.MsgWrapper.load(i) for i in data["conversation"]]
        return msg_tree
    def append(self, msg : MsgBase):
        if len(self.msg_list) == 0:
            self.msg_list.append(MsgTree.MsgWrapper(msg, None))
        else:
            cur = 0
            while self.msg_list[cur].child is not None:
                cur = self.msg_list[cur].children[self.msg_list[cur].child]
            self.msg_list[cur].children.append(len(self.msg_list))
            self.msg_list.append(MsgTree.MsgWrapper(msg, cur))
            self.msg_list[cur].child = len(self.msg_list[cur].children)-1

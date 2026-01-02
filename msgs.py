import json
import log
import time
from translations import translate as t

class MsgBase:
    role: str = ""
    content: str = ""
    def __init__(this, role: str = "", content = ""):
        this.role = role
        this.content = content
    def __repr__(this):
        return str(this.store())
    def store(this):
        return {"role": this.role, "content": this.content}
    @staticmethod
    def load(data : dict):
        if "content" not in data:
            log.error(t("error.message.load").replace("KEY", "content"))
            content = ""
        else: content = data["content"]
        if "role" not in data:
            log.error(t("error.message.load").replace("KEY", "role"))
            role = "user"
        else: role = data["role"]
        return MsgBase(role, content)
class UserMsg(MsgBase):
    def __init__(this, content: str = ""):
        super().__init__("user", content)
    @staticmethod
    def load(data : dict):
        if "content" not in data:
            return UserMsg("")
        return UserMsg(data["content"])
class AssistantMsg(MsgBase):
    def __init__(this, content: str = "", interrupted : bool = False):
        super().__init__("assistant", content)
        this.interrupted = interrupted
    def store(this):
        data = super().store()
        data["interrupted"] = this.interrupted
        return data
    @staticmethod
    def load(data : dict):
        if ("content" not in data) or (not isinstance(data["content"], str)):
            log.error(t("error.message.load").replace("KEY", "content"))
            content = ""
        else: content = data["content"]
        if ("interrupted" not in data) or (not isinstance(data["interrupted"], bool)):
            log.error(t("error.message.load").replace("KEY", "interrupted"))
            interrupted = False
        else: interrupted = data["interrupted"]
        if ("reason" in data) and (isinstance(data["reason"], str)):
            return ReasonAssistantMsg(content, data["reason"], interrupted)
        return AssistantMsg(content, interrupted)
class ReasonAssistantMsg(MsgBase):
    reason: str = ""
    def __init__(this, content: str = "", reason: str = "", interrupted : bool = False):
        super().__init__("assistant", content)
        this.reason = reason
        this.interrupted = interrupted
    def store(this):
        data = super().store()
        data["reason"] = this.reason
        return data
    @staticmethod
    def load(data : dict):
        if ("content" not in data) or (not isinstance(data["content"], str)):
            log.error(t("error.message.load").replace("KEY", "content"))
            content = ""
        else: content = data["content"]
        if ("interrupted" not in data) or (not isinstance(data["interrupted"], bool)):
            log.error(t("error.message.load").replace("KEY", "interrupted"))
            interrupted = False
        else: interrupted = data["interrupted"]
        if ("reason" not in data) or (not isinstance(data["reason"], str)):
            log.error(t("error.message.load").replace("KEY", "reason"))
            return AssistantMsg(content, interrupted)
        else:
            return ReasonAssistantMsg(content, data["reason"], interrupted)
class MsgTree:
    class MsgWrapper:
        type : str
        msg : MsgBase
        parent : int | None
        children : list[int]
        child : int | None
        time : float
        def __init__(this, msg : MsgBase, parent : int | None):
            this.type = type(msg).__name__
            this.msg = msg
            this.parent = parent
            this.children = []
            this.child = None
            this.time = time.time()
        def __repr__(this):
            return str(this.store())
        def store(this):
            return {"type": this.type, "msg": this.msg.store(), "time": this.time, "parent": this.parent, "children": list(this.children), "child": this.child}
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
    def __init__(this, system : str = ""):
        this.msg_list = []
        this.append(MsgBase()) # 根消息
        this.append(MsgBase("system", system))
    def __repr__(this):
        return str(this.store())
    def store(this):
        return {'conversation': [i.store() for i in this.msg_list]}
    @staticmethod
    def load(data : dict):
        msg_tree = MsgTree()
        msg_tree.msg_list = [MsgTree.MsgWrapper.load(i) for i in data["conversation"]]
        return msg_tree
    def get_last_msg_id(this) -> None | int:
        if len(this.msg_list) == 0:
            return None
        else:
            cur = 0
            while this.msg_list[cur].child is not None:
                cur = this.msg_list[cur].children[this.msg_list[cur].child]
            return cur
    def append(this, msg : MsgBase):
        if len(this.msg_list) == 0:
            this.msg_list.append(MsgTree.MsgWrapper(msg, None))
        else:
            cur = 0
            while this.msg_list[cur].child is not None:
                cur = this.msg_list[cur].children[this.msg_list[cur].child]
            this.msg_list[cur].children.append(len(this.msg_list))
            this.msg_list.append(MsgTree.MsgWrapper(msg, cur))
            this.msg_list[cur].child = len(this.msg_list[cur].children)-1
    def complete_last_assistant(this, idx : int, msg : AssistantMsg | ReasonAssistantMsg):
        if not this.ends_with_assistant():
            return
        if 0 <= idx < len(this.msg_list):
            this.msg_list[idx].msg.content += msg.content
            if this.msg_list[idx].type == "ReasonAssistantMsg":
                if isinstance(msg, ReasonAssistantMsg):
                    this.msg_list[idx].msg.reason += msg.reason
            this.msg_list[idx].time = time.time()
            this.msg_list[idx].msg.interrupted = msg.interrupted
        else:
            raise ValueError("message list index out of range")
    def ends_with_assistant(this):
        last_msg_id = this.get_last_msg_id()
        if last_msg_id is None:
            return False
        else:
            return this.msg_list[last_msg_id].type in ("AssistantMsg","ReasonAssistantMsg",)

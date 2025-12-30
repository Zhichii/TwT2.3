import msgs
import openai
import anthropic
import log

class OpenAIProvider:
    def __init__(self, base_url : str, api_key : str):
        self.client = openai.OpenAI(base_url = base_url, api_key = api_key)
    def _to_format(self, msg_tree : msgs.MsgTree):
        cur = 0
        messages = []
        while msg_tree.msg_list[cur].child is not None:
            cur = msg_tree.msg_list[cur].children[msg_tree.msg_list[cur].child]
            msg = msg_tree.msg_list[cur]
            if (msg.type == "MsgBase"):
                if msg.msg.role in ["user", "system", "assistant", "tool"]:
                    messages.append({"role": msg.msg.role, "content": msg.msg.content})
            if (msg.type == "UserMsg"):
                messages.append({"role": "user", "content": msg.msg.content})
            if (msg.type == "AssistantMsg"):
                messages.append({"role": "assistant", "content": msg.msg.content})
            if (msg.type == "ReasonAssistantMsg"):
                if isinstance(msg.msg, msgs.ReasonAssistantMsg): # 不然IDE报错
                    messages.append({"role": "assistant", "content": msg.msg.content, "reasoning_content": msg.msg.reason})
                else:
                    log.error("the tag and the type are not the same")
        return messages
    def __call__(self, model : str, msg_tree : msgs.MsgTree, max_tokens : int = 4096, stream : bool = True):
        messages = self._to_format(msg_tree)
        for chunk in self.client.chat.completions.create(model=model, messages=messages, stream=stream):
            yield chunk.choices[0].delta.content

class AnthropicProvider:
    def __init__(self, base_url : str, api_key : str):
        self.client = anthropic.Anthropic(base_url = base_url, api_key = api_key)
    def _to_format(self, msg_tree : msgs.MsgTree):
        cur = 0
        system = []
        messages = []
        while msg_tree.msg_list[cur].child is not None:
            cur = msg_tree.msg_list[cur].children[msg_tree.msg_list[cur].child]
            msg = msg_tree.msg_list[cur]
            if (msg.type == "MsgBase"):
                if msg.msg.role in ["user", "assistant", "tool"]:
                    messages.append({"role": msg.msg.role, "content": msg.msg.content})
                if msg.msg.role == "system":
                    system.append(msg.msg.content)
            if (msg.type == "UserMsg"):
                messages.append({"role": "user", "content": msg.msg.content})
            if (msg.type == "AssistantMsg"):
                messages.append({"role": "assistant", "content": msg.msg.content})
            if (msg.type == "ReasonAssistantMsg"):
                if isinstance(msg.msg, msgs.ReasonAssistantMsg): # 不然IDE报错
                    messages.append({"role": "assistant", "content": msg.msg.content, "reasoning_content": msg.msg.reason})
                else:
                    log.error("the tag and the type are not the same")
        return (messages, "\n".join(system), )
    def __call__(self, model : str, msg_tree : msgs.MsgTree, max_tokens : int = 4096, stream : bool = True):
        messages, system = self._to_format(msg_tree)
        for chunk in self.client.messages.create(max_tokens=max_tokens, messages=messages, model=model, stream=stream):
            if chunk.type == "content_block_delta":
                if chunk.delta.type == "text_delta":
                    text = chunk.delta.text
                    yield text
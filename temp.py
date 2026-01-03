from app import Provider, Model, deepseek_think_on, deepseek_think_off
deepseek = Provider.load({"name":"DeepSeek","base_url":"https://api.deepseek.com/v1","models":[{"name":"DeepSeek V3.2", "id":"deepseek-chat", "can_think":True, "think_on":{"thinking":{"type":"enabled"}}, "think_off":{"thinking":{"type":"disabled"}}}]})
deepseek_v32 = deepseek.models[0]
print(deepseek.store())
print(Provider.load(deepseek.store()).store())
print(deepseek_v32.generate())
print(deepseek_v32.store())
print(Model.load(deepseek_v32.store()).store())

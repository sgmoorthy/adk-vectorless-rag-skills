def skill(name):
    def decorator(func):
        func.__skill_name__ = name
        return func
    return decorator

class SkillProvider:
    def __init__(self, service_script, env):
        self.service_script = service_script
        self.env = env
        
    def get_skills(self):
        return ["search_lexical", "search_structured", "retrieve_context"]

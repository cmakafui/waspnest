from enum import Enum


class HookPoint(Enum):
    PRE_EXECUTE = "pre_execute"
    POST_EXECUTE = "post_execute"
    SKILL_START = "skill_start"
    SKILL_END = "skill_end"
    ERROR = "error"
    LLM_REQUEST = "llm_request"  # Maps to instructor's completion:kwargs


class Hooks:
    def __init__(self):
        self.hooks: dict[HookPoint, list[callable]] = {point: [] for point in HookPoint}

    def on(self, point: HookPoint, callback: callable):
        self.hooks[point].append(callback)

    def trigger(self, point: HookPoint, **kwargs):
        """Trigger all callbacks for a hook point"""
        for hook in self.hooks[point]:
            try:
                hook(**kwargs)
            except Exception as e:
                self.trigger(HookPoint.ERROR, exception=e, hook=hook)

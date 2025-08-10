from api.constraints import config
from api.models.core.interface import CoreModelInterface

if config.get("Models", {}).get("core_model", "google") == "google":
    from api.models.core.google import GoogleModel as CoreModel
else:
    from api.models.core.openai import OpenAIModel as CoreModel # type:ignore

core_model : CoreModelInterface = CoreModel()
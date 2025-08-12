from api.constraints import config
from api.models.core.interface import CoreModelInterface

models_settings = config.get("Models", {})

if models_settings.get('multi_models', False):
    from api.models.core.multi import MultiModels as CoreModel
else:
    if models_settings.get("core_model", "google") == "google":
        from api.models.core.google import GoogleModel as CoreModel # type:ignore
    else:
        from api.models.core.openai import OpenAIModel as CoreModel # type:ignore

core_model : CoreModelInterface = CoreModel()
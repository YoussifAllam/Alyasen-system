from config.env import ENVIRONMENT

if ENVIRONMENT == "test":
    from .test import *  # noqa: F403 F401

elif ENVIRONMENT == "Production":
    from .production import *  # noqa: F403 F401

else:
    from .local import *  # noqa: F403 F401

# Make ENVIRONMENT available as a module-level variable
__all__ = ["ENVIRONMENT"]

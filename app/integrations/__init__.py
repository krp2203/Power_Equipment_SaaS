from .base import BaseIntegration

# Dictionary to hold active integration instances
# Key: integration_name (str), Value: Integration Instance
_REGISTRY = {}

def register_integration(integration_cls):
    """Decorator or function to register an integration class."""
    instance = integration_cls()
    if not isinstance(instance, BaseIntegration):
        raise ValueError(f"Integration {instance} must inherit from BaseIntegration")
    
    _REGISTRY[instance.name] = instance
    return integration_cls

def get_integration(name):
    """Retrieve an integration instance by name."""
    return _REGISTRY.get(name)

def get_all_integrations():
    """Return all registered integrations."""
    return _REGISTRY.values()

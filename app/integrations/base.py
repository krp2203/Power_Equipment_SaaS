from abc import ABC, abstractmethod

class BaseIntegration(ABC):
    """
    Abstract Base Class for Manufacturer Integrations.
    """
    
    @property
    @abstractmethod
    def name(self):
        """Unique identifier for the integration (e.g., 'scag')."""
        pass

    @abstractmethod
    def parse_bulletin(self, file_path):
        """
        Parses a PDF bulletin and returns structured data:
        {
            'models': [{'model': '...', 'serial_start': '...', 'serial_end': '...'}],
            'parts': [...],
            'labor_hours': ...
        }
        """
        pass

    def get_parts_pricing(self, part_numbers):
        """Optional: Fetch real-time pricing if API available."""
        return {}

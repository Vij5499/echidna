import os
from dataclasses import dataclass

@dataclass
class Config:
    # Learning parameters
    MAX_LEARNING_ATTEMPTS: int = int(os.getenv('MAX_LEARNING_ATTEMPTS', '5'))
    CONVERGENCE_WINDOW_SIZE: int = int(os.getenv('CONVERGENCE_WINDOW_SIZE', '3'))
    MIN_CONFIDENCE_THRESHOLD: float = float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.7'))
    
    # LLM settings
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'gemini-1.5-flash')
    GOOGLE_API_KEY: str = os.getenv('GOOGLE_API_KEY', '')
    
    # File paths
    DEFAULT_SPEC_PATH: str = os.getenv('SPEC_PATH', 'specs/spec_flawed.yaml')
    OUTPUT_DIR: str = os.getenv('OUTPUT_DIR', 'output')
    
    # Execution settings
    TEST_TIMEOUT: int = int(os.getenv('TEST_TIMEOUT', '30'))
    CLEANUP_TEMP_FILES: bool = os.getenv('CLEANUP_TEMP_FILES', 'true').lower() == 'true'
    
    def __post_init__(self):
        if not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

# Global config instance
config = Config()

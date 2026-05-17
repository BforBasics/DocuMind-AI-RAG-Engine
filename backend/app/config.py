from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuMind AI Corporate"
    ENVIRONMENT: str = "development"
    VERSION: str = "1.0.0"
    
    PINECONE_API_KEY: str
    GROQ_API_KEY: str  # Add this line right here
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
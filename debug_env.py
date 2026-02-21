#!/usr/bin/env python3
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    docker_host: str = "unix:///var/run/docker.sock"

    class Config:
        env_prefix = "SERVICE_MANAGER_"
        case_sensitive = False

    @classmethod
    def from_env(cls):
        settings = cls()
        if os.getenv("DOCKER_HOST"):
            settings.docker_host = os.getenv("DOCKER_HOST")
        return settings

if __name__ == "__main__":
    print("DOCKER_HOST:", os.getenv("DOCKER_HOST", "Not set"))
    print("SERVICE_MANAGER_DOCKER_HOST:", os.getenv("SERVICE_MANAGER_DOCKER_HOST", "Not set"))

    settings = Settings()
    print("Settings.docker_host (default):", settings.docker_host)

    settings2 = Settings.from_env()
    print("Settings.docker_host (from_env):", settings2.docker_host)

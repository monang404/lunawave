import yaml
from pathlib import Path

def test_docker_compose_mounts_cache():
    compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml not found"
    
    with open(compose_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    lunawave_service = config.get("services", {}).get("lunawave", {})
    volumes = lunawave_service.get("volumes", [])
    
    has_cache_mount = any(
        "/app/cache" in vol or "/app/cache" == vol.split(":")[-1] 
        for vol in volumes if isinstance(vol, str)
    )
    
    assert has_cache_mount, "Volume /app/cache must be mounted in docker-compose.yml"

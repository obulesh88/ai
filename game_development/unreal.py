"""Unreal Engine project integration: C++ class generation, build commands, log parsing."""
import re
from pathlib import Path
from typing import Dict, List, Optional

HEADER = '''#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "{name}.generated.h"

UCLASS()
class {api} A{name} : public AActor
{{
    GENERATED_BODY()

public:
    A{name}();
}};
'''

SOURCE = '''#include "{name}.h"

A{name}::A{name}()
{{
    PrimaryActorTick.bCanEverTick = false;
}}
'''

BUILD_ERROR_RE = re.compile(r"(error\s+C\d+:[^\n]*)")


class UnrealProject:
    def __init__(self, uproject):
        self.uproject = Path(uproject).resolve()
        if self.uproject.suffix.lower() != ".uproject":
            raise ValueError(f"Not a .uproject file: {self.uproject}")
        self.root = self.uproject.parent

    @staticmethod
    def find(root) -> Optional[Path]:
        found = sorted(Path(root).glob("*.uproject"))
        return found[0] if found else None

    def modules(self) -> List[str]:
        src = self.root / "Source"
        if not src.is_dir():
            return []
        return sorted(p.name for p in src.iterdir() if (p / f"{p.name}.Build.cs").is_file())

    def create_cpp_class(self, name: str, module: str, api: str = None) -> Dict[str, Path]:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid C++ class name: {name}")
        mod_dir = self.root / "Source" / module
        if not mod_dir.is_dir():
            raise FileNotFoundError(f"Module '{module}' not found under Source/")
        api = api or module.upper() + "_API"
        public = mod_dir / "Public"
        private = mod_dir / "Private"
        public.mkdir(exist_ok=True)
        private.mkdir(exist_ok=True)
        header = public / f"{name}.h"
        source = private / f"{name}.cpp"
        if header.exists() or source.exists():
            raise FileExistsError(f"{name} already exists; refusing to overwrite")
        header.write_text(HEADER.format(name=name, api=api), encoding="utf-8")
        source.write_text(SOURCE.format(name=name), encoding="utf-8")
        return {"header": header, "source": source}

    def build_command(self, engine_root, target: str = None, config: str = "Development",
                      platform: str = "Win64") -> str:
        target = target or self.uproject.stem
        ubt = Path(engine_root) / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"
        return (f'"{ubt}" BuildCookRun -project="{self.uproject}" -noP4 -platform={platform} '
                f'-clientconfig={config} -build -cook -stage -pak')

    @staticmethod
    def parse_build_errors(log_text: str) -> List[str]:
        return [m.strip() for m in BUILD_ERROR_RE.findall(log_text)][:50]

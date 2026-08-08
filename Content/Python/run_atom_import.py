# C:\Users\User\Documents\UnrealProjects\Constellation\Content\Python\run_atom_import.py
"""언리얼 에디터 Python 콘솔에서 실행하는 부트스트랩.
1회 실행: `import run_atom_import`
재실행(같은 에디터 세션 안에서, 모듈 캐시 때문에 재-import는 아무것도 안 함):
    `run_atom_import.main()`
실제 로직은 3D Model Creation 저장소의 atom_import 패키지에 있다."""
import sys

REPO_ROOT = r"C:\Users\User\Desktop\Portfolio\3D Model Creation"


def main():
    if REPO_ROOT not in sys.path:
        sys.path.append(REPO_ROOT)
    from atom_import import import_atoms
    import_atoms.run(config_path=REPO_ROOT + r"\unreal_config.yaml")


main()

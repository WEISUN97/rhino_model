import sys
import traceback

import scriptcontext as sc

# RunPythonScript in Rhino

try:
    # Rhino 8 CPython provides reload through importlib.
    from importlib import reload as reload_module
except ImportError:
    # Older Rhino Python environments expose reload as a built-in.
    reload_module = reload


PROJECT_DIR = r"/Users/bubble/Desktop/Model/Rhino/rhino_model"
BUILD_MODULE = "builds.build_demo"


def ensure_project_path():
    if PROJECT_DIR not in sys.path:
        sys.path.insert(0, PROJECT_DIR)


def run():
    try:
        ensure_project_path()

        import tools

        build_module = __import__(BUILD_MODULE, fromlist=["build_model"])
        reload_module(tools)
        build_module = reload_module(build_module)

        build_module.build_model()
        sc.doc.Views.Redraw()
        print("Rhino model rebuilt with:", BUILD_MODULE)
    except Exception:
        print("Error while running launcher.py")
        traceback.print_exc()


run()

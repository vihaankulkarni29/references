import playwright_stealth
import inspect

def search(obj, path="playwright_stealth"):
    for name in dir(obj):
        if name.startswith("_"): continue
        try:
            val = getattr(obj, name)
            if callable(val):
                print(f"Callable: {path}.{name} -> {val}")
            elif inspect.ismodule(val):
                print(f"Module: {path}.{name}")
        except:
            pass

search(playwright_stealth)

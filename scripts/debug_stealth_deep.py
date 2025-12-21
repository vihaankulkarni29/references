import playwright_stealth
import inspect

print("ROOT DIR:", dir(playwright_stealth))

if hasattr(playwright_stealth, 'stealth'):
    print("stealth attribute exists.")
    s = playwright_stealth.stealth
    print("Type of s:", type(s))
    print("S DIR:", dir(s))
    
    if hasattr(s, 'stealth'):
         print("s.stealth exists!")

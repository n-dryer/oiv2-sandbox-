#!/usr/bin/env python3
import os, shutil, platform

def check():
    sys = 'wayland' if os.environ.get('WAYLAND_DISPLAY') else 'x11' if os.environ.get('DISPLAY') else 'windows' if os.name == 'nt' else 'macos' if 'darwin' in platform.system().lower() else 'unknown'
    print(f"🔍 System: {sys} | OS: {platform.system()}")
    
    if sys == 'wayland':
        tools = {'grim': shutil.which('grim'), 'dotool': shutil.which('dotool'), 'ydotool': shutil.which('ydotool')}
        print(f"Tools: {[k for k,v in tools.items() if v]}")
        if not any(tools.values()): print("📦 Install: sudo apt install grim dotool")
        
    elif sys == 'x11':
        tools = {'scrot': shutil.which('scrot'), 'xdotool': shutil.which('xdotool')}
        print(f"Tools: {[k for k,v in tools.items() if v]}")
        if not any(tools.values()): print("📦 Install: sudo apt install scrot xdotool")
        
    elif sys in ['windows', 'macos']:
        try: import pyautogui; print("✅ pyautogui available")
        except: print("📦 Install: pip install pyautogui pillow")
    
    print("🚀 Run: uv run cli.py")

if __name__ == "__main__": check()
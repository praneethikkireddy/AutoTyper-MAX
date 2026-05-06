"""
AutoTyper MAX - Modern Auto Typing Application
Beautiful, simple, macOS-native auto-typer
"""

import tkinter as tk
from tkinter import messagebox
import os
import json
import threading
import time
import random
import platform
import subprocess

try:
    import pyautogui
    # Disable PyAutoGUI's built-in pause for faster typing
    pyautogui.PAUSE = 0
except ImportError:
    raise SystemExit("PyAutoGUI required: pip install pyautogui")

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    from pynput.keyboard import Controller, Key
    keyboard = Controller()
    USE_PYNPUT = True
except ImportError:
    USE_PYNPUT = False


class AutoTyperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoTyper MAX")
        self.geometry("800x750")
        self.minsize(700, 600)
        
        self.is_macos = platform.system() == "Darwin"
        self.config_path = os.path.expanduser("~/.autotyper_config.json")
        self.config = self.load_config()
        
        self._is_typing = False
        self._stop_event = threading.Event()
        
        # Colors
        self.bg = "#0f1419"
        self.bg2 = "#1a1f2e"
        self.accent = "#00d4ff"
        self.text = "#ffffff"
        self.text_dim = "#b0b8c8"
        
        self.configure(bg=self.bg)
        
        # Check macOS accessibility permissions on startup
        if self.is_macos:
            self.check_accessibility_permissions()
        
        self.build_ui()
        self.load_settings()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def check_accessibility_permissions(self):
        """Check if app has accessibility permissions on macOS"""
        try:
            # Try a simple test command
            result = subprocess.run(
                ["osascript", "-e", "tell application \"System Events\" to keystroke \"\""],
                capture_output=True,
                timeout=2
            )
            if result.returncode != 0:
                messagebox.showwarning(
                    "Accessibility Permission",
                    "AutoTyper needs accessibility permissions.\n\n"
                    "Go to: System Settings → Privacy & Security → Accessibility\n"
                    "Add this app (or Terminal) to the list."
                )
        except:
            pass
    
    def build_ui(self):
        # Header
        header = tk.Frame(self, bg=self.bg, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="AutoTyper MAX",
            font=("Helvetica", 28, "bold"),
            bg=self.bg,
            fg=self.text
        ).pack(pady=(20, 5))
        
        tk.Label(
            header,
            text="Fast & realistic auto-typing for any application",
            font=("Helvetica", 11),
            bg=self.bg,
            fg=self.text_dim
        ).pack(pady=(0, 10))
        
        # Main container
        main = tk.Frame(self, bg=self.bg)
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tab buttons
        tab_frame = tk.Frame(main, bg=self.bg)
        tab_frame.pack(fill="x", pady=(0, 15))
        
        self.type_btn = tk.Button(
            tab_frame, text="  Type  ", bg=self.accent, fg="#000",
            font=("Helvetica", 11, "bold"), relief="flat", borderwidth=0,
            padx=20, pady=8, cursor="hand2",
            command=lambda: self.show_tab("type")
        )
        self.type_btn.pack(side="left", padx=(0, 10))
        
        self.settings_btn = tk.Button(
            tab_frame, text="  Settings  ", bg=self.bg2, fg=self.text,
            font=("Helvetica", 11), relief="flat", borderwidth=0,
            padx=20, pady=8, cursor="hand2",
            command=lambda: self.show_tab("settings")
        )
        self.settings_btn.pack(side="left", padx=10)
        
        self.help_btn = tk.Button(
            tab_frame, text="  Help  ", bg=self.bg2, fg=self.text,
            font=("Helvetica", 11), relief="flat", borderwidth=0,
            padx=20, pady=8, cursor="hand2",
            command=lambda: self.show_tab("help")
        )
        self.help_btn.pack(side="left", padx=10)
        
        # Content area
        self.content = tk.Frame(main, bg=self.bg)
        self.content.pack(fill="both", expand=True)
        
        self.build_type_tab()
        self.build_settings_tab()
        self.build_help_tab()
        self.show_tab("type")
    
    def build_type_tab(self):
        tab = tk.Frame(self.content, bg=self.bg, name="type_tab")
        tab.pack(fill="both", expand=True)
        
        # Text input
        tk.Label(tab, text="Text to Type", font=("Helvetica", 12, "bold"),
                bg=self.bg, fg=self.text).pack(anchor="w", pady=(0, 5))
        
        self.text_input = tk.Text(
            tab, height=8, bg=self.bg2, fg=self.text,
            font=("Menlo", 12), insertbackground=self.accent,
            relief="flat", borderwidth=0, padx=12, pady=12
        )
        self.text_input.pack(fill="both", expand=True, pady=(0, 20))
        
        # Speed
        tk.Label(tab, text="Speed (WPM)", font=("Helvetica", 11, "bold"),
                bg=self.bg, fg=self.text).pack(anchor="w", pady=(10, 5))
        
        speed_frame = tk.Frame(tab, bg=self.bg)
        speed_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(speed_frame, text="Min:", bg=self.bg, fg=self.text_dim).pack(side="left")
        self.min_speed = tk.Entry(speed_frame, width=8, bg=self.bg2, fg=self.text,
                                 font=("Menlo", 11), relief="flat", borderwidth=0)
        self.min_speed.insert(0, "30")
        self.min_speed.pack(side="left", padx=(5, 20))
        
        tk.Label(speed_frame, text="Max:", bg=self.bg, fg=self.text_dim).pack(side="left")
        self.max_speed = tk.Entry(speed_frame, width=8, bg=self.bg2, fg=self.text,
                                 font=("Menlo", 11), relief="flat", borderwidth=0)
        self.max_speed.insert(0, "60")
        self.max_speed.pack(side="left", padx=5)
        
        # Options
        tk.Label(tab, text="Options", font=("Helvetica", 11, "bold"),
                bg=self.bg, fg=self.text).pack(anchor="w", pady=(10, 5))
        
        self.random_var = tk.BooleanVar(value=True)
        tk.Checkbutton(tab, text="✓ Random delays (natural)", variable=self.random_var,
                      bg=self.bg, fg=self.text, selectcolor=self.bg2, relief="flat",
                      font=("Helvetica", 10)).pack(anchor="w", pady=3)
        
        self.breaks_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tab, text="Keep line breaks", variable=self.breaks_var,
                      bg=self.bg, fg=self.text, selectcolor=self.bg2, relief="flat",
                      font=("Helvetica", 10)).pack(anchor="w", pady=3)
        
        self.paste_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tab, text="Invisible paste (clipboard)", variable=self.paste_var,
                      bg=self.bg, fg=self.text, selectcolor=self.bg2, relief="flat",
                      font=("Helvetica", 10)).pack(anchor="w", pady=3)
        
        # Start button
        self.start_btn = tk.Button(
            tab, text="▶  Start Typing", command=self.start_typing,
            bg=self.accent, fg="#000", font=("Helvetica", 13, "bold"),
            relief="flat", borderwidth=0, padx=30, pady=12, cursor="hand2"
        )
        self.start_btn.pack(fill="x", pady=(20, 10))
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(tab, textvariable=self.status_var, bg=self.bg, fg=self.text_dim,
                font=("Helvetica", 10)).pack(anchor="w", pady=(5, 10))
        
        # Progress
        self.progress = tk.Canvas(tab, height=6, bg=self.bg2, highlightthickness=0, borderwidth=0)
        self.progress.pack(fill="x")
        self.progress_rect = self.progress.create_rectangle(0, 0, 0, 6, fill=self.accent, outline=self.accent)
    
    def build_settings_tab(self):
        tab = tk.Frame(self.content, bg=self.bg, name="settings_tab")
        tab.pack(fill="both", expand=True)
        
        tk.Label(tab, text="Delay Before Start", font=("Helvetica", 11, "bold"),
                bg=self.bg, fg=self.text).pack(anchor="w", pady=(0, 5))
        
        delay_frame = tk.Frame(tab, bg=self.bg)
        delay_frame.pack(fill="x", pady=(0, 20))
        tk.Label(delay_frame, text="Seconds:", bg=self.bg, fg=self.text_dim).pack(side="left")
        self.delay = tk.Entry(delay_frame, width=8, bg=self.bg2, fg=self.text,
                            font=("Menlo", 11), relief="flat", borderwidth=0)
        self.delay.insert(0, "3")
        self.delay.pack(side="left", padx=5)
        
        tk.Label(tab, text="Natural Pauses", font=("Helvetica", 11, "bold"),
                bg=self.bg, fg=self.text).pack(anchor="w", pady=(10, 5))
        
        pause_frame = tk.Frame(tab, bg=self.bg)
        pause_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(pause_frame, text="Min words:", bg=self.bg, fg=self.text_dim).pack(side="left")
        self.min_pause = tk.Entry(pause_frame, width=8, bg=self.bg2, fg=self.text,
                                 font=("Menlo", 11), relief="flat", borderwidth=0)
        self.min_pause.insert(0, "5")
        self.min_pause.pack(side="left", padx=(5, 20))
        
        tk.Label(pause_frame, text="Max words:", bg=self.bg, fg=self.text_dim).pack(side="left")
        self.max_pause = tk.Entry(pause_frame, width=8, bg=self.bg2, fg=self.text,
                                 font=("Menlo", 11), relief="flat", borderwidth=0)
        self.max_pause.insert(0, "15")
        self.max_pause.pack(side="left", padx=5)
        
        pause_len_frame = tk.Frame(tab, bg=self.bg)
        pause_len_frame.pack(fill="x", pady=(0, 20))
        tk.Label(pause_len_frame, text="Pause length (ms):", bg=self.bg, fg=self.text_dim).pack(side="left")
        self.pause_len = tk.Entry(pause_len_frame, width=8, bg=self.bg2, fg=self.text,
                                 font=("Menlo", 11), relief="flat", borderwidth=0)
        self.pause_len.insert(0, "800")
        self.pause_len.pack(side="left", padx=5)
        
        if self.is_macos:
            tk.Label(tab, text="✓ macOS Setup", font=("Helvetica", 11, "bold"),
                    bg=self.bg, fg=self.text).pack(anchor="w", pady=(20, 5))
            
            info = "For accessibility:\n1. System Settings\n2. Privacy & Security\n3. Accessibility\n4. Add Terminal/Python"
            tk.Label(tab, text=info, bg=self.bg, fg=self.text_dim,
                    justify="left", font=("Helvetica", 10)).pack(anchor="w")
    
    def build_help_tab(self):
        tab = tk.Frame(self.content, bg=self.bg, name="help_tab")
        tab.pack(fill="both", expand=True)
        
        help_text = """HOW TO USE:

1. Type or paste your text above
2. Adjust speed (30-60 WPM is natural)
3. Click "Start Typing"
4. Switch to target app during countdown
5. Watch it type automatically!

SETTINGS:

Speed (WPM)
• Min/Max words per minute
• Lower = slower, more readable

Delay Before Start
• Time in seconds before typing begins
• Use this to switch windows

Natural Pauses
• Pauses every few words
• Makes it look human-typed

Options
• Random delays: Varies speed
• Keep breaks: Preserves newlines
• Clipboard paste: Instant paste

TIPS:

✓ Start with 30-60 WPM
✓ Enable random delays
✓ Test with TextEdit first
✓ Use pauses for long text
✓ Give yourself time to switch apps
✓ Enable accessibility on macOS

MACOS REQUIREMENTS:

1. Install dependencies:
   pip install pyautogui pyperclip pynput

2. Grant accessibility permissions:
   System Settings → Privacy & Security
   → Accessibility → Add Terminal/Python

3. On M1/M2 Macs: May need to run from
   native Python (not Rosetta)

For questions or issues, check the GitHub repo!
"""
        tk.Label(tab, text=help_text, bg=self.bg, fg=self.text, justify="left",
                font=("Menlo", 9), wraplength=600).pack(anchor="nw", pady=10)
    
    def show_tab(self, tab_name):
        for child in self.content.winfo_children():
            child.pack_forget()
        
        if tab_name == "type":
            self.type_btn.config(bg=self.accent, fg="#000")
            self.settings_btn.config(bg=self.bg2, fg=self.text)
            self.help_btn.config(bg=self.bg2, fg=self.text)
            self.content.winfo_children()[0].pack(fill="both", expand=True)
        elif tab_name == "settings":
            self.type_btn.config(bg=self.bg2, fg=self.text)
            self.settings_btn.config(bg=self.accent, fg="#000")
            self.help_btn.config(bg=self.bg2, fg=self.text)
            self.content.winfo_children()[1].pack(fill="both", expand=True)
        else:
            self.type_btn.config(bg=self.bg2, fg=self.text)
            self.settings_btn.config(bg=self.bg2, fg=self.text)
            self.help_btn.config(bg=self.accent, fg="#000")
            self.content.winfo_children()[2].pack(fill="both", expand=True)
    
    def start_typing(self):
        text = self.text_input.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Empty", "Enter text to type")
            return
        
        try:
            min_wpm = float(self.min_speed.get())
            max_wpm = float(self.max_speed.get())
        except:
            messagebox.showerror("Error", "Invalid speed values")
            return
        
        if min_wpm <= 0 or max_wpm <= 0 or min_wpm > max_wpm:
            messagebox.showerror("Error", "Invalid WPM range")
            return
        
        if self._is_typing:
            messagebox.showinfo("Busy", "Already typing")
            return
        
        try:
            delay = float(self.delay.get())
        except:
            delay = 3
        
        try:
            min_pause_w = int(self.min_pause.get())
            max_pause_w = int(self.max_pause.get())
            pause_ms = int(self.pause_len.get())
        except:
            min_pause_w = max_pause_w = pause_ms = 0
        
        self._is_typing = True
        self._stop_event.clear()
        self.start_btn.config(state="disabled")
        
        t = threading.Thread(
            target=self._type,
            args=(text, min_wpm, max_wpm, min_pause_w, max_pause_w, pause_ms,
                  self.random_var.get(), self.breaks_var.get(), self.paste_var.get(), delay),
            daemon=True
        )
        t.start()
    
    def _type_character_mac(self, ch):
        """Type a character on macOS using the best available method"""
        if USE_PYNPUT:
            try:
                keyboard.type(ch)
                return True
            except:
                pass
        
        # Fallback to pyautogui
        try:
            if ch == "\n":
                pyautogui.press("enter")
            elif ch == "\t":
                pyautogui.press("tab")
            elif ch == " ":
                pyautogui.press("space")
            else:
                # Use AppleScript for better character support on macOS
                safe_char = ch.replace('"', '\\"').replace("'", "'")
                subprocess.run(
                    ["osascript", "-e", f'tell application "System Events" to keystroke "{safe_char}"'],
                    capture_output=True,
                    timeout=1
                )
            return True
        except:
            return False
    
    def _type(self, text, min_w, max_w, min_p, max_p, p_ms, random, breaks, paste, delay):
        try:
            total = 2.0 + max(0, delay)  # 2 second buffer + user delay
            start = time.time()
            self.status_var.set(f"Starting in {int(total)}s...")
            
            while time.time() - start < total:
                if self._stop_event.is_set():
                    return
                r = int(total - (time.time() - start))
                if r > 0:
                    self.status_var.set(f"Starting in {r}s...")
                time.sleep(0.1)
            
            if paste and pyperclip:
                try:
                    pyperclip.copy(text)
                    time.sleep(0.1)
                    pyautogui.hotkey("cmd", "v")
                    self.status_var.set("✓ Pasted!")
                    self._update_progress(100)
                    return
                except Exception as e:
                    self.status_var.set(f"Paste failed, typing instead...")
                    time.sleep(0.5)
            
            if not breaks:
                text = text.replace("\n", " ")
            
            total_chars = len(text)
            words_pause = 0
            next_pause = random.randint(min_p, max_p) if max_p > 0 else 999999
            
            for i, ch in enumerate(text):
                if self._stop_event.is_set():
                    return
                
                wpm = random.uniform(min_w, max_w) if random else (min_w + max_w) / 2
                delay_char = 60.0 / (wpm * 5.0)
                
                # Type character
                self._type_character_mac(ch)
                
                prog = (i + 1) / total_chars * 100
                self.status_var.set(f"Typing... {prog:.0f}%")
                self._update_progress(prog)
                
                if ch.isspace():
                    words_pause += 1
                    if words_pause >= next_pause and p_ms > 0:
                        time.sleep(p_ms / 1000.0)
                        words_pause = 0
                        if max_p > 0:
                            import random as r
                            next_pause = r.randint(min_p, max_p)
                
                time.sleep(delay_char)
            
            self.status_var.set("✓ Done!")
            self._update_progress(100)
        except Exception as e:
            self.status_var.set(f"Error: {str(e)[:40]}")
        finally:
            self._is_typing = False
            self.start_btn.config(state="normal")
            self.save_settings()
    
    def _update_progress(self, pct):
        if self.progress.winfo_exists():
            w = int(self.progress.winfo_width() * (pct / 100.0))
            self.progress.coords(self.progress_rect, 0, 0, w, 6)
    
    def load_config(self):
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except:
            return {}
    
    def load_settings(self):
        cfg = self.config
        self.min_speed.delete(0, tk.END)
        self.min_speed.insert(0, cfg.get("min_speed", "30"))
        self.max_speed.delete(0, tk.END)
        self.max_speed.insert(0, cfg.get("max_speed", "60"))
        self.delay.delete(0, tk.END)
        self.delay.insert(0, cfg.get("delay", "3"))
        self.min_pause.delete(0, tk.END)
        self.min_pause.insert(0, cfg.get("min_pause", "5"))
        self.max_pause.delete(0, tk.END)
        self.max_pause.insert(0, cfg.get("max_pause", "15"))
        self.pause_len.delete(0, tk.END)
        self.pause_len.insert(0, cfg.get("pause_len", "800"))
        self.random_var.set(cfg.get("random", True))
        self.breaks_var.set(cfg.get("breaks", False))
        self.paste_var.set(cfg.get("paste", False))
    
    def save_settings(self):
        self.config = {
            "min_speed": self.min_speed.get(),
            "max_speed": self.max_speed.get(),
            "delay": self.delay.get(),
            "min_pause": self.min_pause.get(),
            "max_pause": self.max_pause.get(),
            "pause_len": self.pause_len.get(),
            "random": self.random_var.get(),
            "breaks": self.breaks_var.get(),
            "paste": self.paste_var.get(),
        }
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f)
        except:
            pass
    
    def on_close(self):
        self.save_settings()
        self.destroy()


if __name__ == "__main__":
    app = AutoTyperApp()
    app.mainloop()

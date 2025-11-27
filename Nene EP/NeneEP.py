import miniupnpc
import atexit
import signal
import sys
import threading
import tkinter as tk
import os  # [추가됨] 아이콘 경로 찾기용
from tkinter import scrolledtext
from datetime import datetime

# ========================================================
# HELPER: RESOURCE PATH (For PyInstaller --onefile)
# ========================================================
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ========================================================
# LICENSE TEXT DATA
# ========================================================
LICENSE_TEXT = """Nene EasyPort
Copyright (c) 2025 Nene Launcher Team
Licensed under the MIT License.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

----------------------------------------------------------------

[ Third Party Library: miniupnpc ]
This software uses the miniupnpc library.
Copyright (c) 2005-2025, Thomas BERNARD
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. The name of the author may not be used to endorse or promote products derived
   from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED.

----------------------------------------------------------------

[ Python Standard Library ]
This software uses the Python Standard Library (sys, threading, datetime, atexit, signal).
Copyright (c) 2001-2025 Python Software Foundation; All Rights Reserved.

This software is licensed under the Python Software Foundation License Version 2.
Python is a registered trademark of the Python Software Foundation.

----------------------------------------------------------------

[ Tcl/Tk (used by tkinter) ]
This software uses Tcl/Tk via the tkinter module.
Copyright (c) Regents of the University of California, Sun Microsystems, Inc.,
Scriptics Corporation, and other parties.

This software is licensed under a BSD-style license.
"""

COLORS = {
    "bg_main": "#F3F3F3",
    "bg_card": "#FFFFFF",
    "accent": "#0067C0",
    "accent_hover": "#1975C5",
    "text_main": "#1A1A1A",
    "text_sub": "#5D5D5D",
    "border": "#E5E5E5",
    "error": "#C42B1C",
    "error_hover": "#D13425",
    "success": "#107C10",
    "log_bg": "#FFFFFF",
    "log_text": "#1A1A1A",
    "info_btn": "#E0E0E0",      # Color for info button
    "info_btn_hover": "#D0D0D0"
}

FONTS = {
    "header": ("Segoe UI", 20, "bold"),
    "label": ("Segoe UI", 10),
    "value": ("Segoe UI", 10, "bold"),
    "button": ("Segoe UI", 9, "bold"),
    "mono": ("Consolas", 9)
}

class FluentButton(tk.Button):
    def __init__(self, master, text, command, bg_color=COLORS['accent'], hover_color=COLORS['accent_hover'], **kwargs):
        super().__init__(master, **kwargs)
        self.bg_color = bg_color
        self.hover_color = hover_color
        
        # Determine padding based on kwargs to allow square buttons
        pad_x = kwargs.pop('padx', 20)
        
        self.configure(
            text=text,
            command=command,
            bg=self.bg_color,
            fg="white" if bg_color == COLORS['accent'] or bg_color == COLORS['error'] else COLORS['text_main'],
            relief=tk.FLAT,
            bd=0,
            activebackground=self.hover_color,
            activeforeground="white" if bg_color == COLORS['accent'] or bg_color == COLORS['error'] else COLORS['text_main'],
            cursor="hand2",
            padx=pad_x,
            pady=8,
            font=FONTS['button']
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        if self['state'] != tk.DISABLED:
            self['bg'] = self.hover_color

    def on_leave(self, e):
        if self['state'] != tk.DISABLED:
            self['bg'] = self.bg_color
            
    def set_state(self, enabled=True):
        if enabled:
            self.configure(state=tk.NORMAL, bg=self.bg_color, cursor="hand2")
        else:
            self.configure(state=tk.DISABLED, bg="#CCCCCC", cursor="arrow")

class InfoRow(tk.Frame):
    def __init__(self, master, label_text, variable):
        super().__init__(master, bg=COLORS['bg_card'])
        self.pack(fill=tk.X, pady=6)
        
        tk.Label(self, text=label_text, bg=COLORS['bg_card'], 
                 fg=COLORS['text_sub'], font=FONTS['label'], width=12, anchor="w")\
            .pack(side=tk.LEFT)
            
        tk.Label(self, textvariable=variable, bg=COLORS['bg_card'], 
                 fg=COLORS['text_main'], font=FONTS['value'], anchor="w")\
            .pack(side=tk.LEFT)

class UPnPAutoManager:
    def __init__(self, port=25565, protocol='TCP', description='Nene Launcher'):
        self.port = port
        self.protocol = protocol
        self.description = description
        self.upnp = miniupnpc.UPnP()
        self.upnp.discoverdelay = 200
        self.port_opened = False
        self.callback = None
        self.external_ip = "-"
        self.local_ip = "-"
        
        atexit.register(self._cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        self._cleanup()
        sys.exit(0)

    def _cleanup(self):
        if self.port_opened:
            try:
                self.upnp.deleteportmapping(self.port, self.protocol)
            except:
                pass

    def set_callback(self, callback):
        self.callback = callback

    def log(self, msg, t="info"):
        if self.callback:
            self.callback(msg, t)

    def refresh_ip_only(self):
        """Discover network and fetch IPs without opening ports"""
        try:
            self.log("Scanning network info...", "info")
            devices = self.upnp.discover()
            if devices > 0:
                self.upnp.selectigd()
                self.external_ip = self.upnp.externalipaddress()
                self.local_ip = self.upnp.lanaddr
                self.log(f"Network Found: {self.external_ip}", "success")
                return True
        except Exception as e:
            self.log(f"Scan Warning: {str(e)}", "error")
        return False

    def run_auto(self):
        """
        Returns:
            0: Success
            1: Error (Retry allowed)
            2: Conflict (Start disabled)
        """
        try:
            self.log("Searching for Gateway...", "info")
            devices = self.upnp.discover()
            if devices == 0:
                self.log("Error: No UPnP gateway found.", "error")
                return 1
            
            self.upnp.selectigd()
            self.log(f"Gateway found (Devices: {devices})", "success")

            external_ip = self.upnp.externalipaddress()
            local_ip = self.upnp.lanaddr

            self.external_ip = external_ip
            self.local_ip = local_ip

            self.log(f"External IP: {external_ip}", "info")
            self.log(f"Local IP: {local_ip}", "info")

            # [CONFLICT CHECK LOGIC]
            try:
                existing = self.upnp.getspecificportmapping(self.port, self.protocol)
                if existing:
                    # existing structure: (IP, Port, Description, Enabled, LeaseDuration)
                    mapped_ip = existing[0]
                    
                    if mapped_ip != local_ip:
                        # Case: Used by another PC -> Conflict!
                        self.log(f"Conflict: Port is used by {mapped_ip}", "error")
                        self.log("Operation stopped to prevent conflict.", "error")
                        return 2 # Return Conflict Code
                    else:
                        # Case: Used by this PC -> Refresh
                        self.log("Port is already open (This PC). Refreshing...", "info")
            except Exception:
                # Ignore errors during check (e.g. port not mapped)
                pass

            self.log(f"Opening Port {self.port}...", "info")
            result = self.upnp.addportmapping(
                self.port, self.protocol,
                local_ip, self.port,
                self.description, ''
            )
            
            if result is False:
                 self.log("Error: Router rejected the request.", "error")
                 return 1 # Error Code

            self.port_opened = True
            self.log("Success: Port Forwarding Active!", "success")
            return 0 # Success Code

        except Exception as e:
            error_msg = str(e)
            
            if error_msg.lower().strip() == 'success':
                 error_msg = "Unknown Error (Router sent mixed signals)"

            if "Miniupnpc" in error_msg or "miniupnpc" in error_msg:
                error_msg = error_msg.replace("Miniupnpc", "").replace("miniupnpc", "")
                error_msg = error_msg.replace("Exception", "Error")
                error_msg = error_msg.lstrip(" :.")
            
            self.log(f"Error: {error_msg}", "error")
            return 1 # Error Code

    def close_port(self):
        try:
            if not self.port_opened:
                return True
            
            result = self.upnp.deleteportmapping(self.port, self.protocol)
            self.log("Port Closed.", "info")
            self.port_opened = False
            return bool(result)
        except:
            self.port_opened = False
            return False

class Win11App:
    def __init__(self, root):
        self.root = root
        self.root.title("NeneEP")
        self.root.geometry("400x620")
        self.root.configure(bg=COLORS['bg_main'])
        self.root.resizable(False, False)

        # [추가됨] 아이콘 적용 코드
        try:
            icon_path = resource_path("NeneEP.ico")
            self.root.iconbitmap(icon_path)
        except Exception:
            pass # 아이콘이 없으면 기본값 사용

        self.manager = UPnPAutoManager()
        self.manager.set_callback(self.add_log)

        self.status_var = tk.StringVar(value="Waiting...")
        self.ext_var = tk.StringVar(value="-")
        self.local_var = tk.StringVar(value="-")

        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # [CHANGED] Auto-start forwarding service after 0.5s
        self.root.after(500, self.start_forwarding)

    def build_ui(self):
        header_frame = tk.Frame(self.root, bg=COLORS['bg_main'])
        header_frame.pack(fill=tk.X, padx=24, pady=(24, 10))

        tk.Label(
            header_frame, 
            text="Nene EasyPort",
            font=FONTS['header'],
            bg=COLORS['bg_main'], 
            fg=COLORS['text_main']
        ).pack(anchor="w")
        
        # [CHANGED] Subtitle text updated
        tk.Label(
            header_frame,
            text="Nene Launcher UPnP port forwarding tool",
            font=("Segoe UI", 10),
            bg=COLORS['bg_main'], 
            fg=COLORS['text_sub']
        ).pack(anchor="w")

        card_frame = tk.Frame(
            self.root, 
            bg=COLORS['bg_card'], 
            highlightbackground=COLORS['border'], 
            highlightthickness=1
        )
        card_frame.pack(fill=tk.X, padx=24, pady=10)

        inner_card = tk.Frame(card_frame, bg=COLORS['bg_card'], padx=16, pady=16)
        inner_card.pack(fill=tk.X)

        tk.Label(inner_card, text="Connection Status", font=("Segoe UI", 10, "bold"),
                 bg=COLORS['bg_card'], fg=COLORS['text_main']).pack(anchor="w", pady=(0, 8))

        InfoRow(inner_card, "Status", self.status_var)
        InfoRow(inner_card, "External IP", self.ext_var)
        InfoRow(inner_card, "Local IP", self.local_var)

        # Button Frame
        btn_frame = tk.Frame(self.root, bg=COLORS['bg_main'])
        btn_frame.pack(fill=tk.X, padx=24, pady=10)

        # Start Button
        self.btn_start = FluentButton(
            btn_frame, text="Start",
            command=self.start_forwarding,
            bg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover']
        )
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Stop Button
        self.btn_stop = FluentButton(
            btn_frame, text="Stop",
            command=self.stop_forwarding,
            bg_color=COLORS['error'],
            hover_color=COLORS['error_hover']
        )
        self.btn_stop.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.btn_stop.set_state(False)

        # Info/License Button (Small Square)
        self.btn_info = FluentButton(
            btn_frame, text="?", 
            command=self.show_license_window,
            bg_color=COLORS['info_btn'],
            hover_color=COLORS['info_btn_hover'],
            width=3,  # Small width for square shape
            padx=0    # Remove extra padding
        )
        self.btn_info.pack(side=tk.LEFT)

        log_frame = tk.Frame(
            self.root, 
            bg=COLORS['log_bg'],
            highlightbackground=COLORS['border'],
            highlightthickness=1
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(10, 24))

        tk.Label(log_frame, text="System Log", font=("Segoe UI", 9, "bold"),
                 bg=COLORS['log_bg'], fg=COLORS['text_sub']).pack(anchor="w", padx=10, pady=(10, 5))

        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            bg=COLORS['log_bg'],
            fg=COLORS['log_text'],
            font=FONTS['mono'],
            relief=tk.FLAT,
            padx=10, pady=5,
            height=8,
            state='normal'
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def show_license_window(self):
        win = tk.Toplevel(self.root)
        win.title("About & Licenses")
        
        # [추가됨] 팝업창에도 아이콘 적용
        try:
            icon_path = resource_path("NeneEP.ico")
            win.iconbitmap(icon_path)
        except:
            pass

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        width = int(screen_width * 0.85)
        height = int(screen_height * 0.8)
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        win.geometry(f"{width}x{height}+{x}+{y}")
        win.configure(bg=COLORS['bg_main'])
        
        tk.Label(
            win, text="Open Source Licenses", 
            font=("Segoe UI", 14, "bold"),
            bg=COLORS['bg_main'], fg=COLORS['text_main']
        ).pack(pady=(15, 5))

        txt_frame = tk.Frame(win, bg=COLORS['bg_card'], padx=2, pady=2)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        license_area = scrolledtext.ScrolledText(
            txt_frame,
            font=("Consolas", 10),
            bg=COLORS['bg_card'],
            fg=COLORS['text_main'],
            relief=tk.FLAT
        )
        license_area.pack(fill=tk.BOTH, expand=True)
        
        license_area.insert(tk.END, LICENSE_TEXT)
        license_area.configure(state='disabled')

    def add_log(self, message, typ="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {"info": "#005FB8", "success": "#107C10", "error": "#C42B1C"}
        color = colors.get(typ, COLORS['text_main'])

        self.log_area.tag_config(typ, foreground=color)
        full_msg = f"[{timestamp}] {message}\n"
        self.log_area.insert(tk.END, full_msg, typ)
        self.log_area.see(tk.END)

    def start_forwarding(self):
        if self.manager.port_opened:
            return

        self.btn_start.set_state(False)
        self.status_var.set("Opening... 25565 ")
        self.add_log("Starting service...", "info")

        def run():
            result_code = self.manager.run_auto()
            self.root.after(0, lambda: self.after_start(result_code))

        threading.Thread(target=run, daemon=True).start()

    def after_start(self, result_code):
        # Update IPs just in case they changed or weren't fetched yet
        self.ext_var.set(self.manager.external_ip)
        self.local_var.set(self.manager.local_ip)

        if result_code == 0: # SUCCESS
            self.status_var.set("Active 25565(Open)")
            self.btn_stop.set_state(True)
            self.btn_start.set_state(False) 
        
        elif result_code == 2: # CONFLICT
            self.status_var.set("Conflict (Used)")
            self.btn_start.set_state(False)
            self.btn_stop.set_state(False)
            
        else: # ERROR
            self.status_var.set("Failed")
            self.btn_start.set_state(True)
            self.btn_stop.set_state(False)

    def stop_forwarding(self):
        self.btn_stop.set_state(False)
        self.add_log("Stopping...", "info")

        def run():
            self.manager.close_port()
            self.root.after(0, self.after_stop)

        threading.Thread(target=run, daemon=True).start()

    def after_stop(self):
        self.status_var.set("Closed")
        # Keep IPs visible even after stop, just show closed status
        # self.ext_var.set("-") # Don't clear these
        # self.local_var.set("-")
        self.btn_start.set_state(True)
        self.add_log("Service stopped.", "info")

    def on_close(self):
        if self.manager.port_opened:
            self.manager.close_port()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = Win11App(root)
    root.mainloop()
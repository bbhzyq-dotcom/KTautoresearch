#!/usr/bin/env python3
"""
LLM Configuration Dialog
"""

import sys

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    print("Tkinter not available")
    sys.exit(1)


class LLMConfigDialog:
    def __init__(self, parent, current_config=None):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("LLM Configuration")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.current_config = current_config or {}

        self._create_widgets()
        self._load_current_config()

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        center_x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        center_y = parent.winfo_y() + (parent.winfo_height() - 450) // 2
        self.dialog.geometry(f"+{center_x}+{center_y}")

    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="LLM Provider Configuration",
            font=('Helvetica', 14, 'bold')
        ).pack(pady=(0, 20))

        provider_frame = ttk.LabelFrame(main_frame, text="Provider", padding=10)
        provider_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(provider_frame, text="Select Provider:").pack(anchor=tk.W)

        self.provider_var = tk.StringVar(value="ollama")

        providers = [
            ("Ollama (Local)", "ollama"),
            ("LM Studio (Local)", "lm_studio"),
            ("OpenAI API", "openai"),
            ("Groq", "groq"),
            ("Together AI", "together"),
            ("Anthropic (Claude)", "anthropic"),
            ("Custom (Other)", "custom"),
        ]

        for text, value in providers:
            ttk.Radiobutton(
                provider_frame,
                text=text,
                variable=self.provider_var,
                value=value,
                command=self._on_provider_change
            ).pack(anchor=tk.W)

        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        row = 0
        ttk.Label(settings_frame, text="API Base URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.api_base_entry = ttk.Entry(settings_frame, width=40)
        self.api_base_entry.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        row += 1
        ttk.Label(settings_frame, text="API Key:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.api_key_entry = ttk.Entry(settings_frame, width=40, show="*")
        self.api_key_entry.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        row += 1
        ttk.Label(settings_frame, text="Model Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.model_entry = ttk.Entry(settings_frame, width=40)
        self.model_entry.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        row += 1
        ttk.Label(settings_frame, text="Temperature:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.temp_var = tk.DoubleVar(value=0.7)
        ttk.Spinbox(
            settings_frame,
            from_=0.0, to=2.0, increment=0.1,
            textvariable=self.temp_var,
            width=38
        ).grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        row += 1
        ttk.Label(settings_frame, text="Max Tokens:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=4096)
        ttk.Spinbox(
            settings_frame,
            from_=256, to=32768, increment=256,
            textvariable=self.max_tokens_var,
            width=38
        ).grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))

        settings_frame.columnconfigure(1, weight=1)

        test_frame = ttk.Frame(main_frame)
        test_frame.pack(fill=tk.X, pady=(0, 10))

        self.test_btn = ttk.Button(
            test_frame,
            text="Test Connection",
            command=self._test_connection
        )
        self.test_btn.pack(side=tk.LEFT)

        self.test_status = ttk.Label(test_frame, text="", foreground="gray")
        self.test_status.pack(side=tk.LEFT, padx=(10, 0))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(
            btn_frame,
            text="Save",
            command=self._on_save
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT)

        self._on_provider_change()

    def _load_current_config(self):
        if not self.current_config:
            return

        self.provider_var.set(self.current_config.get("provider", "ollama"))
        self.api_base_entry.insert(0, self.current_config.get("api_base", ""))
        self.api_key_entry.insert(0, self.current_config.get("api_key", ""))
        self.model_entry.insert(0, self.current_config.get("model", ""))
        self.temp_var.set(self.current_config.get("temperature", 0.7))
        self.max_tokens_var.set(self.current_config.get("max_tokens", 4096))

        self._on_provider_change()

    def _on_provider_change(self):
        provider = self.provider_var.get()

        base_urls = {
            "ollama": "http://localhost:11434/v1",
            "lm_studio": "http://localhost:1234/v1",
            "openai": "https://api.openai.com/v1",
            "groq": "https://api.groq.com/openai/v1",
            "together": "https://api.together.ai/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "custom": "http://localhost:8000/v1"
        }

        models = {
            "ollama": "llama3",
            "lm_studio": "local-model",
            "openai": "gpt-4",
            "groq": "llama-3.1-70b-versatile",
            "together": "meta-llama/Llama-3-70b-chat-hf",
            "anthropic": "claude-3-opus-20240229",
            "custom": "your-model"
        }

        if not self.current_config or not self.current_config.get("api_base"):
            self.api_base_entry.delete(0, tk.END)
            self.api_base_entry.insert(0, base_urls.get(provider, ""))

        if not self.current_config or not self.current_config.get("model"):
            self.model_entry.delete(0, tk.END)
            self.model_entry.insert(0, models.get(provider, ""))

        if provider in ["ollama", "lm_studio"]:
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.insert(0, "not-needed")
            self.api_key_entry.config(state="readonly")
        else:
            self.api_key_entry.config(state="normal")

    def _test_connection(self):
        from core.llm_provider import LLMConfig, LLMProvider

        self.test_btn.config(state="disabled")
        self.test_status.config(text="Testing...", foreground="gray")

        try:
            config = self._get_config()
            provider = LLMProvider(config)

            if provider.is_available():
                models = provider.list_models()
                self.test_status.config(
                    text=f"OK! Found {len(models)} models",
                    foreground="green"
                )
            else:
                self.test_status.config(text="Failed to connect", foreground="red")
                messagebox.showwarning(
                    "Connection Failed",
                    "Could not connect to the LLM provider.\n\n"
                    "Please check:\n"
                    "1. The service is running\n"
                    "2. The API URL is correct\n"
                    "3. The API key is valid"
                )
        except Exception as e:
            self.test_status.config(text=f"Error: {str(e)[:30]}", foreground="red")
            messagebox.showerror("Error", str(e))
        finally:
            self.test_btn.config(state="normal")

    def _get_config(self):
        from core.llm_provider import LLMConfig
        return LLMConfig(
            provider=self.provider_var.get(),
            api_base=self.api_base_entry.get().strip(),
            api_key=self.api_key_entry.get().strip(),
            model=self.model_entry.get().strip(),
            temperature=self.temp_var.get(),
            max_tokens=self.max_tokens_var.get()
        )

    def _on_save(self):
        self.result = self._get_config()
        self.dialog.destroy()

    def _on_cancel(self):
        self.dialog.destroy()

    def show(self):
        self.dialog.wait_window()
        return self.result

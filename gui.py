#!/usr/bin/env python3
"""
KTautoresearch GUI - 图形化界面版本
Scientific Hypothesis Generation and Autonomous Experimentation System
"""

import json
import os
import sys
import threading
import webbrowser
from datetime import datetime
from typing import List, Optional

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
except ImportError:
    print("Tkinter not available. Please install Python with Tkinter support.")
    sys.exit(1)

from core import (
    HypothesisGenerator,
    ScientificHypothesis,
    HumanValidator,
    ValidationDecision,
    ExperimentExecutor,
    ExperimentDesign,
    Evaluator,
    EvaluationResult,
    EvaluationVerdict,
    EvidenceStrength,
    HypothesisStatus
)


class KTautoresearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KTautoresearch - AI科学假说生成与自动实验系统")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        self.workspace_path = "./workspace"
        self.research_question = ""
        self.hypothesis_generator = HypothesisGenerator()
        self.human_validator = HumanValidator(
            workspace_path=os.path.join(self.workspace_path, "validation")
        )
        self.experiment_executor = ExperimentExecutor(
            workspace_path=os.path.join(self.workspace_path, "experiments"),
            max_iterations=5,
            time_budget_per_experiment=60
        )
        self.evaluator = Evaluator(workspace_path=self.workspace_path)
        self.hypotheses: List[ScientificHypothesis] = []
        self.current_hypothesis_index = 0

        self._setup_workspace()
        self._setup_styles()
        self._create_widgets()
        self._setup_logging()
        self._try_load_llm_config()

    def _try_load_llm_config(self):
        config_path = "./llm_config.json"
        if os.path.exists(config_path):
            try:
                from core.llm_provider import LLMProvider
                provider = LLMProvider.from_config_file(config_path)
                if provider.is_available():
                    self.hypothesis_generator.set_llm_provider(provider)
                    models = provider.list_models()
                    self.llm_status_label.config(
                        text=f"[LLM: {provider.config.model}]",
                        foreground='green'
                    )
                    self._append_log(f"LLM loaded: {provider.config.model} ({len(models)} models available)")
            except Exception as e:
                self._append_log(f"LLM config load failed: {e}")

    def _setup_workspace(self):
        os.makedirs(os.path.join(self.workspace_path, "hypotheses"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_path, "experiments"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_path, "validation"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_path, "evaluation"), exist_ok=True)

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.colors = {
            'primary': '#2563eb',
            'success': '#16a34a',
            'warning': '#ea580c',
            'danger': '#dc2626',
            'bg': '#f8fafc',
            'card': '#ffffff',
            'text': '#1e293b',
            'text_secondary': '#64748b'
        }

        self.style.configure('Title.TLabel', font=('Helvetica', 18, 'bold'), foreground=self.colors['text'])
        self.style.configure('Heading.TLabel', font=('Helvetica', 14, 'bold'), foreground=self.colors['text'])
        self.style.configure('Body.TLabel', font=('Helvetica', 10), foreground=self.colors['text'])
        self.style.configure('Status.TLabel', font=('Helvetica', 9), foreground=self.colors['text_secondary'])

        self.style.configure('Primary.TButton', font=('Helvetica', 11), background=self.colors['primary'])
        self.style.configure('Success.TButton', font=('Helvetica', 11))
        self.style.configure('Danger.TButton', font=('Helvetica', 11))

    def _create_widgets(self):
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self._create_header()
        self._create_main_content()
        self._create_footer()

    def _create_header(self):
        header = ttk.Frame(self.main_container, height=80)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        header.pack_propagate(False)

        title_label = ttk.Label(
            header,
            text="KTautoresearch",
            style='Title.TLabel'
        )
        title_label.pack(side=tk.LEFT)

        subtitle = ttk.Label(
            header,
            text="AI科学假说生成与自动实验系统",
            style='Status.TLabel'
        )
        subtitle.pack(side=tk.LEFT, pady=(25, 0))

        github_btn = ttk.Button(
            header,
            text="View on GitHub",
            command=lambda: webbrowser.open("https://github.com/bbhzyq-dotcom/KTautoresearch")
        )
        github_btn.pack(side=tk.RIGHT, padx=(0, 10))

        self.llm_status_label = ttk.Label(
            header,
            text="[LLM: Not Configured]",
            style='Status.TLabel',
            foreground='gray'
        )
        self.llm_status_label.pack(side=tk.RIGHT, padx=(0, 10))

        llm_config_btn = ttk.Button(
            header,
            text="LLM Config",
            command=self._open_llm_config
        )
        llm_config_btn.pack(side=tk.RIGHT)

    def _create_main_content(self):
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.tab_research = ttk.Frame(self.notebook)
        self.tab_hypotheses = ttk.Frame(self.notebook)
        self.tab_validation = ttk.Frame(self.notebook)
        self.tab_experiments = ttk.Frame(self.notebook)
        self.tab_results = ttk.Frame(self.notebook)
        self.tab_log = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_research, text="1. 研究问题")
        self.notebook.add(self.tab_hypotheses, text="2. 假说生成")
        self.notebook.add(self.tab_validation, text="3. 人类验证")
        self.notebook.add(self.tab_experiments, text="4. 执行实验")
        self.notebook.add(self.tab_results, text="5. 评估结果")
        self.notebook.add(self.tab_log, text="日志")

        self._setup_research_tab()
        self._setup_hypotheses_tab()
        self._setup_validation_tab()
        self._setup_experiments_tab()
        self._setup_results_tab()
        self._setup_log_tab()

    def _setup_research_tab(self):
        container = ttk.Frame(self.tab_research, padding=30)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="定义你的研究问题",
            style='Heading.TLabel'
        ).pack(anchor=tk.W, pady=(0, 20))

        info_text = (
            "在下面输入你想要研究的问题。AI将基于这个问题生成多个科学假说，\n"
            "然后你可以筛选有价值的假说进行自动实验验证。"
        )
        ttk.Label(
            container,
            text=info_text,
            style='Body.TLabel'
        ).pack(anchor=tk.W, pady=(0, 20))

        ttk.Label(container, text="研究问题:", style='Body.TLabel').pack(anchor=tk.W, pady=(0, 5))

        self.question_text = scrolledtext.ScrolledText(
            container,
            height=5,
            font=('Helvetica', 11),
            wrap=tk.WORD,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.question_text.pack(fill=tk.X, pady=(0, 20))

        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X)

        self.btn_start = ttk.Button(
            button_frame,
            text="开始生成假说",
            command=self._on_generate_clicked,
            style='Primary.TButton'
        )
        self.btn_start.pack(side=tk.LEFT)

        ttk.Label(
            button_frame,
            text="提示: 点击后将生成5个候选假说供你筛选",
            style='Status.TLabel'
        ).pack(side=tk.RIGHT, pady=10)

        self.progress_label = ttk.Label(container, text="", style='Status.TLabel')
        self.progress_label.pack(anchor=tk.W, pady=(20, 0))

        self.progress_bar = ttk.Progressbar(
            container,
            mode='indeterminate',
            length=300
        )

    def _setup_hypotheses_tab(self):
        container = ttk.Frame(self.tab_hypotheses, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header,
            text="生成的假说列表",
            style='Heading.TLabel'
        ).pack(side=tk.LEFT)

        self.hypothesis_count_label = ttk.Label(
            header,
            text="0 个假说",
            style='Status.TLabel'
        )
        self.hypothesis_count_label.pack(side=tk.RIGHT)

        list_frame = ttk.Frame(container)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.hypothesis_listbox = tk.Listbox(
            list_frame,
            font=('Helvetica', 11),
            selectmode=tk.SINGLE,
            activestyle='underline',
            relief=tk.SOLID,
            borderwidth=1
        )
        self.hypothesis_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.hypothesis_listbox.bind('<<ListboxSelect>>', self._on_hypothesis_select)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.hypothesis_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hypothesis_listbox.config(yscrollcommand=scrollbar.set)

        detail_frame = ttk.LabelFrame(container, text="假说详情", padding=10)
        detail_frame.pack(fill=tk.X, pady=(10, 0))

        self.hypothesis_detail_text = scrolledtext.ScrolledText(
            detail_frame,
            height=12,
            font=('Helvetica', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.hypothesis_detail_text.pack(fill=tk.X)

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="刷新列表",
            command=self._refresh_hypothesis_list
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="查看所有详情",
            command=self._show_all_hypotheses_detail
        ).pack(side=tk.LEFT)

    def _setup_validation_tab(self):
        container = ttk.Frame(self.tab_validation, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header,
            text="人类验证",
            style='Heading.TLabel'
        ).pack(side=tk.LEFT)

        self.validation_progress = ttk.Label(
            header,
            text="0 / 0 已验证",
            style='Status.TLabel'
        )
        self.validation_progress.pack(side=tk.RIGHT)

        content = ttk.Frame(container)
        content.pack(fill=tk.BOTH, expand=True)

        self.validation_detail = scrolledtext.ScrolledText(
            content,
            font=('Helvetica', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.validation_detail.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        validation_btns = ttk.Frame(container)
        validation_btns.pack(fill=tk.X)

        ttk.Button(
            validation_btns,
            text="批准 (Worthy)",
            command=lambda: self._validate_current(ValidationDecision.WORTHY),
            style='Success.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            validation_btns,
            text="拒绝 (Unworthy)",
            command=lambda: self._validate_current(ValidationDecision.UNWORTHY),
            style='Danger.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            validation_btns,
            text="跳过 (Defer)",
            command=lambda: self._validate_current(ValidationDecision.DEFER)
        ).pack(side=tk.LEFT)

        ttk.Button(
            validation_btns,
            text="自动批准所有",
            command=self._auto_validate_all
        ).pack(side=tk.RIGHT)

        self._refresh_validation_list()

    def _setup_experiments_tab(self):
        container = ttk.Frame(self.tab_experiments, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header,
            text="自动实验执行 (LLM驱动)",
            style='Heading.TLabel'
        ).pack(side=tk.LEFT)

        self.experiment_status = ttk.Label(
            header,
            text="等待开始...",
            style='Status.TLabel'
        )
        self.experiment_status.pack(side=tk.RIGHT)

        config_frame = ttk.LabelFrame(container, text="实验配置", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))

        type_row = ttk.Frame(config_frame)
        type_row.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(type_row, text="实验类型:").pack(side=tk.LEFT)

        self.experiment_type_var = tk.StringVar(value="literature_search")

        experiment_types = [
            ("文献搜索", "literature_search"),
            ("案例分析", "case_study"),
            ("比较分析", "comparative_analysis"),
            ("批判性评论", "critical_review"),
            ("创意写作", "text_generation"),
            ("问卷设计", "survey_design"),
            ("访谈分析", "interview_analysis"),
            ("通用分析", "generic"),
        ]

        for text, value in experiment_types:
            ttk.Radiobutton(
                type_row,
                text=text,
                variable=self.experiment_type_var,
                value=value
            ).pack(side=tk.LEFT, padx=(0, 10))

        self.experiment_text = scrolledtext.ScrolledText(
            container,
            font=('Courier', 10),
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg='#f1f5f9'
        )
        self.experiment_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X)

        self.btn_run_experiments = ttk.Button(
            btn_frame,
            text="开始执行实验",
            command=self._run_experiments_thread,
            style='Primary.TButton'
        )
        self.btn_run_experiments.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            btn_frame,
            text="清空输出",
            command=lambda: self._clear_experiment_output()
        ).pack(side=tk.LEFT)

        llm_warning = ttk.Label(
            btn_frame,
            text="注意: 需要配置 LLM 才能执行真实实验",
            foreground="orange"
        )
        llm_warning.pack(side=tk.RIGHT)

        self._load_validated_hypotheses()

    def _setup_results_tab(self):
        container = ttk.Frame(self.tab_results, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header,
            text="评估结果",
            style='Heading.TLabel'
        ).pack(side=tk.LEFT)

        ttk.Button(
            header,
            text="刷新",
            command=self._refresh_results
        ).pack(side=tk.RIGHT)

        self.results_text = scrolledtext.ScrolledText(
            container,
            font=('Helvetica', 10),
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg='#f8fafc'
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)

        self._refresh_results()

    def _setup_log_tab(self):
        container = ttk.Frame(self.tab_log, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header,
            text="系统日志",
            style='Heading.TLabel'
        ).pack(side=tk.LEFT)

        ttk.Button(
            header,
            text="清空日志",
            command=self._clear_log
        ).pack(side=tk.RIGHT)

        self.log_text = scrolledtext.ScrolledText(
            container,
            font=('Courier', 9),
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg='#1e293b',
            fg='#e2e8f0'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self._append_log("KTautoresearch GUI 已启动")
        self._append_log("="*50)

    def _create_footer(self):
        footer = ttk.Frame(self.main_container, padding=(20, 10))
        footer.pack(fill=tk.X)

        self.status_label = ttk.Label(
            footer,
            text="就绪",
            style='Status.TLabel'
        )
        self.status_label.pack(side=tk.LEFT)

        ttk.Label(
            footer,
            text="Inspired by Karpathy's autoresearch",
            style='Status.TLabel'
        ).pack(side=tk.RIGHT)

    def _setup_logging(self):
        self.log_file = os.path.join(self.workspace_path, "ktautoresearch.log")
        handler = LogHandler(self)

    def _open_llm_config(self):
        try:
            from llm_config import LLMConfigDialog
            from core.llm_provider import LLMProvider, LLMConfig

            current_config = None
            config_path = "./llm_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)

            dialog = LLMConfigDialog(self.root, current_config)
            result = dialog.show()

            if result:
                provider = LLMProvider(result)
                provider.save_config(config_path)

                llm_provider = LLMProvider(result)

                if llm_provider.is_available():
                    models = llm_provider.list_models()
                    self.llm_status_label.config(
                        text=f"[LLM: {result.model}]",
                        foreground='green'
                    )
                    self._update_status(f"LLM configured successfully. Found {len(models)} models: {', '.join(models[:3])}...")

                    self.hypothesis_generator.set_llm_provider(llm_provider)

                    messagebox.showinfo(
                        "LLM Configured",
                        f"Successfully connected to {result.provider}!\n"
                        f"Model: {result.model}\n"
                        f"Available models: {', '.join(models[:3])}..."
                    )
                else:
                    self.llm_status_label.config(
                        text="[LLM: Connection Failed]",
                        foreground='red'
                    )
                    messagebox.showwarning(
                        "Connection Failed",
                        "Could not connect to LLM provider.\n\n"
                        "Using template-based generation instead."
                    )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to configure LLM: {str(e)}")

    def _append_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def _update_status(self, message: str):
        self.status_label.config(text=message)
        self._append_log(message)

    def _on_generate_clicked(self):
        question = self.question_text.get("1.0", tk.END).strip()
        if not question:
            messagebox.showwarning("警告", "请输入研究问题")
            return

        self.research_question = question
        self._update_status(f"开始为问题生成假说: {question[:50]}...")

        self.btn_start.config(state=tk.DISABLED)
        self.progress_bar.pack(anchor=tk.W, pady=(10, 0))
        self.progress_bar.start()

        thread = threading.Thread(target=self._generate_hypotheses_thread, args=(question,))
        thread.daemon = True
        thread.start()

    def _generate_hypotheses_thread(self, question: str):
        try:
            hypotheses = self.hypothesis_generator.generate_hypotheses(
                research_question=question,
                num_hypotheses=5
            )
            self.hypotheses = hypotheses

            for h in hypotheses:
                self._save_hypothesis(h)

            self.root.after(0, self._on_hypotheses_generated, hypotheses)
        except Exception as e:
            self.root.after(0, self._on_error, str(e))

    def _on_hypotheses_generated(self, hypotheses):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.btn_start.config(state=tk.NORMAL)

        self._update_status(f"生成了 {len(hypotheses)} 个假说")
        self._refresh_hypothesis_list()
        self.notebook.select(1)

        self.hypothesis_count_label.config(text=f"{len(hypotheses)} 个假说")

        messagebox.showinfo(
            "生成完成",
            f"已生成 {len(hypotheses)} 个候选假说。\n"
            "请前往「假说列表」查看并前往「人类验证」进行筛选。"
        )

    def _on_error(self, error_msg: str):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.btn_start.config(state=tk.NORMAL)
        self._update_status(f"错误: {error_msg}")
        messagebox.showerror("错误", f"发生错误: {error_msg}")

    def _save_hypothesis(self, hypothesis: ScientificHypothesis):
        filename = os.path.join(
            self.workspace_path,
            "hypotheses",
            f"hypothesis_{hypothesis.id}.json"
        )
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(hypothesis.to_dict(), f, indent=2, ensure_ascii=False)

    def _refresh_hypothesis_list(self):
        self.hypothesis_listbox.delete(0, tk.END)
        hypotheses_dir = os.path.join(self.workspace_path, "hypotheses")

        if not os.path.exists(hypotheses_dir):
            return

        self.hypotheses = []
        for filename in sorted(os.listdir(hypotheses_dir)):
            if filename.endswith('.json'):
                with open(os.path.join(hypotheses_dir, filename), encoding='utf-8') as f:
                    h = ScientificHypothesis.from_dict(json.load(f))
                    self.hypotheses.append(h)
                    status_icon = self._get_status_icon(h.status)
                    self.hypothesis_listbox.insert(
                        tk.END,
                        f"{status_icon} [{h.id}] {h.title[:60]}..."
                    )

        self.hypothesis_count_label.config(text=f"{len(self.hypotheses)} 个假说")

    def _get_status_icon(self, status: str) -> str:
        icons = {
            HypothesisStatus.DRAFT.value: "[草稿]",
            HypothesisStatus.PENDING_VALIDATION.value: "[待验证]",
            HypothesisStatus.VALIDATED_WORTHY.value: "[✓批准]",
            HypothesisStatus.VALIDATED_UNWORTHY.value: "[✗拒绝]",
            HypothesisStatus.EXPERIMENTING.value: "[实验中]",
            HypothesisStatus.EXPERIMENT_COMPLETED.value: "[已完成]",
            HypothesisStatus.EXPERIMENT_FAILED.value: "[失败]"
        }
        return icons.get(status, "[?]")

    def _on_hypothesis_select(self, event):
        selection = self.hypothesis_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx >= len(self.hypotheses):
            return

        h = self.hypotheses[idx]
        self._show_hypothesis_detail(h)

    def _show_hypothesis_detail(self, h: ScientificHypothesis):
        detail = f"""
=== 假说详情 ===
ID: {h.id}
状态: {h.status}
标题: {h.title}

【描述】
{h.description}

【科学依据】
{h.rationale}

【预测机制】
{h.predicted_mechanism}

【预期效果方向】
{h.expected_effect_direction}

【建议的实验】
"""
        for i, exp in enumerate(h.suggested_experiments, 1):
            detail += f"  {i}. {exp}\n"

        detail += f"""
【可行性评估】
{h.estimated_feasibility}

【AI置信度】
{h.ai_confidence:.2f}

【创建时间】
{h.created_at}
"""

        if h.validation_notes:
            detail += f"\n【验证备注】\n{h.validation_notes}\n"

        self.hypothesis_detail_text.config(state=tk.NORMAL)
        self.hypothesis_detail_text.delete("1.0", tk.END)
        self.hypothesis_detail_text.insert("1.0", detail)
        self.hypothesis_detail_text.config(state=tk.DISABLED)

    def _show_all_hypotheses_detail(self):
        if not self.hypotheses:
            return

        detail_window = tk.Toplevel(self.root)
        detail_window.title("所有假说详情")
        detail_window.geometry("800x600")

        text = scrolledtext.ScrolledText(
            detail_window,
            font=('Helvetica', 10),
            wrap=tk.WORD
        )
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for i, h in enumerate(self.hypotheses):
            text.insert(tk.END, f"\n{'='*60}\n")
            text.insert(tk.END, f"假说 {i+1}: {h.title}\n")
            text.insert(tk.END, f"{'='*60}\n")
            text.insert(tk.END, f"ID: {h.id} | 状态: {h.status}\n\n")
            text.insert(tk.END, f"{h.description}\n\n")
            text.insert(tk.END, f"依据: {h.rationale}\n")
            text.insert(tk.END, f"预测机制: {h.predicted_mechanism}\n")

        text.config(state=tk.DISABLED)

    def _refresh_validation_list(self):
        self._load_validated_hypotheses()
        pending = [h for h in self.hypotheses
                  if h.status in [HypothesisStatus.DRAFT.value,
                                HypothesisStatus.PENDING_VALIDATION.value]]

        if pending:
            h = pending[0]
            self._show_hypothesis_detail(h)
            self.validation_progress.config(text=f"0 / {len(pending)} 已验证")
        else:
            self.validation_detail.config(state=tk.NORMAL)
            self.validation_detail.delete("1.0", tk.END)
            self.validation_detail.insert("1.0", "没有待验证的假说。\n\n请先在「研究问题」标签页生成假说。")
            self.validation_detail.config(state=tk.DISABLED)

    def _load_validated_hypotheses(self):
        hypotheses_dir = os.path.join(self.workspace_path, "hypotheses")
        if not os.path.exists(hypotheses_dir):
            return

        self.hypotheses = []
        for filename in sorted(os.listdir(hypotheses_dir)):
            if filename.endswith('.json'):
                with open(os.path.join(hypotheses_dir, filename), encoding='utf-8') as f:
                    self.hypotheses.append(ScientificHypothesis.from_dict(json.load(f)))

    def _validate_current(self, decision: ValidationDecision):
        pending = [h for h in self.hypotheses
                  if h.status in [HypothesisStatus.DRAFT.value,
                                HypothesisStatus.PENDING_VALIDATION.value]]

        if not pending:
            messagebox.showinfo("完成", "所有假说都已验证完毕！")
            return

        h = pending[0]
        decision_text = {
            ValidationDecision.WORTHY: "批准",
            ValidationDecision.UNWORTHY: "拒绝",
            ValidationDecision.DEFER: "跳过"
        }.get(decision, "处理")

        self.human_validator.validate_hypothesis(
            hypothesis=h,
            validator_name="gui_user",
            decision=decision,
            confidence_level=5,
            reasoning=f"GUI验证: {decision_text}"
        )

        self._save_hypothesis(h)
        self._update_status(f"假说 [{h.id}] 已标记为: {decision_text}")

        self._refresh_validation_list()
        self._refresh_hypothesis_list()

        remaining = len([h for h in self.hypotheses
                        if h.status in [HypothesisStatus.DRAFT.value,
                                       HypothesisStatus.PENDING_VALIDATION.value]])

        if remaining == 0:
            messagebox.showinfo("验证完成", "所有假说已验证完毕！\n请前往「执行实验」开始实验。")
            self.notebook.select(3)

    def _auto_validate_all(self):
        for h in self.hypotheses:
            if h.status in [HypothesisStatus.DRAFT.value, HypothesisStatus.PENDING_VALIDATION.value]:
                self.human_validator.validate_hypothesis(
                    hypothesis=h,
                    validator_name="gui_user",
                    decision=ValidationDecision.WORTHY,
                    confidence_level=5,
                    reasoning="GUI自动批准"
                )
                self._save_hypothesis(h)

        self._update_status("已自动批准所有假说")
        self._refresh_validation_list()
        self._refresh_hypothesis_list()
        messagebox.showinfo("完成", "已自动批准所有假说！")

    def _run_experiments_thread(self):
        worthy = [h for h in self.hypotheses
                 if h.status == HypothesisStatus.VALIDATED_WORTHY.value]

        if not worthy:
            self.root.after(0, lambda: messagebox.showwarning("警告", "没有已批准的假说可实验"))
            return

        self.btn_run_experiments.config(state=tk.DISABLED)
        self.experiment_status.config(text="实验中...")
        self._clear_experiment_output()
        self._append_experiment_log("开始执行实验...\n")

        thread = threading.Thread(target=self._run_experiments_worker, args=(worthy,))
        thread.daemon = True
        thread.start()

    def _run_experiments_worker(self, worthy: List[ScientificHypothesis]):
        from core.experiment_executor_v2 import LLMExperimentExecutor, ExperimentType as ExpType

        type_map = {
            "literature_search": ExpType.LITERATURE_SEARCH,
            "case_study": ExpType.CASE_STUDY,
            "comparative_analysis": ExpType.COMPARATIVE_ANALYSIS,
            "critical_review": ExpType.CRITICAL_REVIEW,
            "text_generation": ExpType.TEXT_GENERATION,
            "survey_design": ExpType.SURVEY_DESIGN,
            "interview_analysis": ExpType.INTERVIEW_ANALYSIS,
            "generic": ExpType.DATA_ANALYSIS,
        }

        exp_type = type_map.get(self.experiment_type_var.get(), ExpType.LITERATURE_SEARCH)

        llm_executor = LLMExperimentExecutor(
            llm_provider=self.hypothesis_generator.llm_provider,
            workspace_path=self.workspace_path
        )

        if not llm_executor.is_llm_available():
            self.root.after(0, lambda: self._append_experiment_log(
                "\n⚠️ 警告: LLM 未配置，实验将以模拟模式运行\n"
                "请先配置 LLM 以获得真实结果\n\n"
            ))

        for i, h in enumerate(worthy):
            self.root.after(0, lambda h=h, i=i: self._append_experiment_log(
                f"\n{'='*50}\n"
                f"实验 {i+1}/{len(worthy)}\n"
                f"假说: {h.title}\n"
                f"实验类型: {exp_type.value}\n"
                f"{'='*50}\n\n"
            ))

            def progress_callback(msg, pct):
                self.root.after(0, lambda m=msg, p=pct: self._append_experiment_log(f"  [{p:3d}%] {m}\n"))

            design = llm_executor.design_experiment(h, exp_type)

            self.root.after(0, lambda d=design: self._append_experiment_log(
                f"方法论: {d.get('methodology', 'N/A')}\n"
                f"步骤数: {len(d.get('steps', []))}\n\n"
            ))

            result = llm_executor.execute_experiment(
                hypothesis=h,
                design=design,
                experiment_type=exp_type,
                iteration=1,
                progress_callback=progress_callback
            )

            findings_str = ""
            if result.findings:
                findings_str = "\n关键发现:\n" + "\n".join(f"  - {x}" for x in result.findings[:3]) + "\n"

            self.root.after(0, lambda r=result, fs=findings_str: self._append_experiment_log(
                f"\n结果:\n"
                f"  - 状态: {r.status}\n"
                f"  - 结论: {r.assessment.get('verdict', 'N/A')}\n"
                f"  - 证据强度: {r.assessment.get('evidence_strength', 'N/A')}\n"
                f"  - 执行时间: {r.duration_seconds:.1f}秒\n"
                f"{fs}"
            ))

        self.root.after(0, self._on_experiments_complete)

    def _on_experiments_complete(self):
        self.btn_run_experiments.config(state=tk.NORMAL)
        self.experiment_status.config(text="实验完成")
        self._update_status("所有实验执行完成")
        self._refresh_results()
        self.notebook.select(4)
        messagebox.showinfo("完成", "所有实验执行完成！\n请查看「评估结果」。")

    def _append_experiment_log(self, message: str):
        self.experiment_text.config(state=tk.NORMAL)
        self.experiment_text.insert(tk.END, message)
        self.experiment_text.see(tk.END)
        self.experiment_text.config(state=tk.DISABLED)

    def _clear_experiment_output(self):
        self.experiment_text.config(state=tk.NORMAL)
        self.experiment_text.delete("1.0", tk.END)
        self.experiment_text.config(state=tk.DISABLED)

    def _refresh_results(self):
        self._load_validated_hypotheses()
        experiments_dir = os.path.join(self.workspace_path, "experiments")

        results_text = "="*60 + "\n"
        results_text += "假说验证评估结果\n"
        results_text += "="*60 + "\n\n"

        worthy = [h for h in self.hypotheses
                 if h.status == HypothesisStatus.VALIDATED_WORTHY.value]

        if not worthy:
            results_text += "还没有已批准的假说。\n"
        else:
            supported = 0
            partial = 0
            not_supported = 0

            for h in worthy:
                exp_files = [f for f in os.listdir(experiments_dir)
                            if f.startswith(f"experiment_{h.id}") or h.id in f]

                if not exp_files:
                    results_text += f"\n【{h.title}】\n"
                    results_text += "  状态: 等待实验\n\n"
                    continue

                experiments = []
                for f in exp_files:
                    with open(os.path.join(experiments_dir, f), encoding='utf-8') as fp:
                        experiments.append(json.load(fp))

                if not experiments:
                    continue

                exp_objects = []
                for e in experiments:
                    from core.experiment_executor import Experiment
                    exp_objects.append(Experiment.from_dict(e))

                eval_result = self.evaluator.evaluate_hypothesis(h, exp_objects)

                verdict_icon = {
                    EvaluationVerdict.SUPPORTED.value: "✓ 支持",
                    EvaluationVerdict.PARTIALLY_SUPPORTED.value: "◐ 部分支持",
                    EvaluationVerdict.NOT_SUPPORTED.value: "✗ 不支持",
                    EvaluationVerdict.CONTRADICTED.value: "✗ 矛盾",
                    EvaluationVerdict.INCONCLUSIVE.value: "? 不确定"
                }.get(eval_result.verdict, "? 未知")

                evidence_icon = {
                    EvidenceStrength.STRONG.value: "●●●",
                    EvidenceStrength.MODERATE.value: "●●○",
                    EvidenceStrength.WEAK.value: "●○○",
                    EvidenceStrength.NONE.value: "○○○"
                }.get(eval_result.evidence_strength, "○○○")

                results_text += f"\n【{h.title[:50]}】\n"
                results_text += f"  结论: {verdict_icon}\n"
                results_text += f"  证据强度: {evidence_icon}\n"
                results_text += f"  效果量(d): {eval_result.effect_size:.4f}\n"
                results_text += f"  P值: {eval_result.p_value:.4f}\n"
                results_text += f"  建议: {eval_result.recommendation}\n"

                if eval_result.verdict == EvaluationVerdict.SUPPORTED.value:
                    supported += 1
                elif eval_result.verdict == EvaluationVerdict.PARTIALLY_SUPPORTED.value:
                    partial += 1
                elif eval_result.verdict == EvaluationVerdict.NOT_SUPPORTED.value:
                    not_supported += 1

            results_text += "\n" + "="*60 + "\n"
            results_text += f"汇总: 支持({supported}) | 部分支持({partial}) | 不支持({not_supported})\n"

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", results_text)
        self.results_text.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("")


class LogHandler:
    def __init__(self, gui: KTautoresearchGUI):
        self.gui = gui

    def write(self, message):
        if message.strip():
            self.gui._append_log(message.strip())

    def flush(self):
        pass


def main():
    root = tk.Tk()
    app = KTautoresearchGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

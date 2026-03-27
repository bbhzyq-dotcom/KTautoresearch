#!/usr/bin/env python3
"""
KTautoresearch - Main Entry Point

Scientific Hypothesis Generation and Autonomous Experimentation System

Usage:
    python main.py --gui           # Launch GUI version (Recommended)
    python main.py --cli           # Run in command-line mode
    python main.py --demo          # Run demo workflow
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="KTautoresearch - Scientific Hypothesis Generation and Autonomous Experimentation"
    )
    parser.add_argument(
        "--gui", "-g",
        action="store_true",
        help="Launch graphical user interface (GUI)"
    )
    parser.add_argument(
        "--cli", "-c",
        action="store_true",
        help="Run in command-line mode"
    )
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Run demo workflow in CLI mode"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        default=None,
        help="Research question (for CLI mode)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run full workflow (for CLI mode)"
    )
    parser.add_argument(
        "--generate", "-gen",
        action="store_true",
        help="Generate hypotheses only"
    )
    parser.add_argument(
        "--num-hypotheses", "-n",
        type=int,
        default=5,
        help="Number of hypotheses to generate"
    )
    parser.add_argument(
        "--workspace", "-w",
        type=str,
        default="./workspace",
        help="Workspace directory"
    )

    args = parser.parse_args()

    if args.gui or (not args.cli and not args.demo and not args.question):
        print("Launching GUI...")
        from gui import main as gui_main
        gui_main()
        return

    if args.cli or args.all or args.generate or args.question:
        from ktcli import KTAutoResearchCLI
        cli = KTAutoResearchCLI(workspace_path=args.workspace)

        if args.demo:
            cli.run_demo()
        elif args.question:
            cli.research_question = args.question
            cli.setup_workspace()
            if args.all:
                cli.run_full_workflow(num_hypotheses=args.num_hypotheses)
            elif args.generate:
                cli.generate_hypotheses(num_hypotheses=args.num_hypotheses)
        else:
            print("Use --gui for graphical interface, or provide --question")
            print("\nExamples:")
            print("  python main.py --gui")
            print("  python main.py --question 'How does sleep affect memory?' --all")
            return


if __name__ == "__main__":
    main()

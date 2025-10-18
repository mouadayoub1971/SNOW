def print_intro():
    """Display the welcome screen with ASCII art."""
    # ANSI color codes
    RED = "\033[91m"
    GOLD = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Clear screen effect with some spacing
    print("\n" * 2)

    # Welcome box with red border
    box_width = 50
    welcome_text = "Welcome to Valyrion"
    padding = (box_width - len(welcome_text) - 2) // 2

    print(f"{RED}{'═' * box_width}{RESET}")
    print(f"{RED}║{' ' * padding}{BOLD}{welcome_text}{RESET}{RED}{' ' * (box_width - len(welcome_text) - padding - 2)}║{RESET}")
    print(f"{RED}{'═' * box_width}{RESET}")
    print()

    # ASCII art for VALYRION in block letters with fire emojis
    valyrion_art = f"""{BOLD}{RED}     🔥                                                                   🔥
          ██╗   ██╗ █████╗ ██╗  ██╗   ██╗██████╗ ██╗ ██████╗ ███╗   ██╗
          ██║   ██║██╔══██╗██║  ╚██╗ ██╔╝██╔══██╗██║██╔═══██╗████╗  ██║
          ██║   ██║███████║██║   ╚████╔╝ ██████╔╝██║██║   ██║██╔██╗ ██║
          ╚██╗ ██╔╝██╔══██║██║    ╚██╔╝  ██╔══██╗██║██║   ██║██║╚██╗██║
           ╚████╔╝ ██║  ██║███████╗██║   ██║  ██║██║╚██████╔╝██║ ╚████║
            ╚═══╝  ╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
     🔥                                                                   🔥{RESET}"""

    print(valyrion_art)
    print()
    print(f"{GOLD}                      🐉  The Dragon of Financial Markets  🐉{RESET}")
    print()
    print("Forged in fire, powered by data.")
    print("Ask me any questions. Type 'exit' or 'quit' to end.")
    print()


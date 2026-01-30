import sys, builtins, logging, runpy, rich, rich.logging

# Estetica Rich
builtins.print = rich.print
logging.basicConfig(
    level=logging.INFO, 
    format="%(message)s", 
    handlers=[rich.logging.RichHandler(rich_tracebacks=True, markup=True)]
)

if len(sys.argv) > 1:
    # Prepara gli argomenti per lo script bersaglio
    target_script = sys.argv[1]
    sys.argv = sys.argv[1:] # shift degli argomenti
    runpy.run_path(target_script, run_name="__main__")
else:
    print("[bold red]Utilizzo:[/bold red] python r.py nome_script.py --args")

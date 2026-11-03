"""Run demo conversations against the real agent and save them as markdown.

Usage (from the project root):
    python -m examples.run_scenarios          # all scenarios
    python -m examples.run_scenarios 05 02    # only scenarios whose file name starts with these prefixes

A scenario is saved only if every turn succeeded, so the saved files never
contain placeholder or error replies.
"""
import sys
import time
from pathlib import Path

from app.agent.session import Session
from main import initialize_agent

OUT_DIR = Path(__file__).parent
PAUSE_BETWEEN_TURNS = 4  # seconds; helps avoid free-tier rate limits
MAX_ATTEMPTS = 3

# Each scenario = (file name, title, list of customer turns).
# Scenario 05 uses an email from customers.csv (the customer who owns order 2).
SCENARIOS = [
    ("01_preco_produto", "Consulta de preço (dados em tempo real)",
     ["Quanto custa o Takamine GD20?"]),
    ("02_catalogo_violoes", "Opções de violões até R$ 1.000 (catálogo + contexto)",
     ["Quais opções de violões disponíveis custando até R$1000?",
      "Qual desses é melhor pra iniciante?"]),
    ("03_info_loja", "Informações institucionais (políticas)",
     ["Oi! Qual o endereço da loja e até que horas vocês abrem hoje?"]),
    ("04_devolucao", "Arrependimento de compra (aplicação das políticas)",
     ["Me arrependi da minha compra, posso devolver meu pedido?",
      "Foi uma compra online, comprei há 5 dias."]),
    ("05_pedido_e_fora_escopo", "Status de pedido com identificação + fora do escopo",
     ["Onde está meu pedido 2?",
      "Meu e-mail é pedro.oliveira@jmail.com",
      "Aproveitando, me ajuda a escrever um código em Python?"]),
]


def ask(agent, turn: str) -> str | None:
    """
    Send one message, retrying with a growing wait. Returns None if all attempts fail.
    A failed attempt leaves the session history untouched (the agent only saves
    messages after a successful reply), so retrying is safe.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return agent.handle_message(turn)
        except Exception as error:
            print(f"  attempt {attempt}/{MAX_ATTEMPTS} failed: {error!r}")
            if attempt < MAX_ATTEMPTS:
                time.sleep(10 * attempt)
    return None


def main():
    selected = sys.argv[1:]
    agent = initialize_agent()  # loads models once; sessions are swapped per scenario

    for filename, title, turns in SCENARIOS:
        if selected and not any(filename.startswith(prefix) for prefix in selected):
            continue

        print(f"Running {filename}...")
        agent.session = Session()
        lines = [f"# {title}\n"]
        succeeded = True

        for turn in turns:
            reply = ask(agent, turn)
            if reply is None:
                succeeded = False
                break
            lines += [f"**Cliente:** {turn}\n", f"**Assistente:** {reply}\n"]
            time.sleep(PAUSE_BETWEEN_TURNS)

        if not succeeded:
            print(f"SKIPPED {filename}: a turn failed after {MAX_ATTEMPTS} attempts (nothing saved)")
            continue

        (OUT_DIR / f"{filename}.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"saved {filename}.md")


if __name__ == "__main__":
    main()
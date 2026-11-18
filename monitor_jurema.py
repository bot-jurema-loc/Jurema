
import os
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Pasta oficial do projeto
PASTA = Path(
    r"C:\Users\Raphael Rodrigues\Documents\GitHub\Jurema"
)

INTERVALO = 5
TEMPO_ESTAVEL = 10
ULTIMA_TENTATIVA_PUSH = 0


def executar(comando):
    return subprocess.run(
        comando,
        cwd=str(PASTA),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )


def registrar(mensagem):
    horario = datetime.now().strftime("%H:%M:%S")
    print(f"[{horario}] {mensagem}", flush=True)


def obter_snapshot():
    arquivos = []

    for raiz, pastas, nomes in os.walk(PASTA):
        pastas[:] = [
            p for p in pastas
            if p not in {
                ".git", "__pycache__", "venv",
                ".venv", "env", "node_modules"
            }
        ]

        for nome in nomes:
            caminho = Path(raiz) / nome

            try:
                info = caminho.stat()
                relativo = caminho.relative_to(PASTA)
                arquivos.append(
                    (str(relativo), info.st_size, info.st_mtime_ns)
                )
            except (OSError, FileNotFoundError):
                continue

    return tuple(sorted(arquivos))


def sincronizar():
    global ULTIMA_TENTATIVA_PUSH

    # Adiciona arquivos novos, modificados e exclusões
    resultado = executar(["git", "add", "-A"])

    if resultado.returncode != 0:
        registrar("Erro ao adicionar arquivos: " + resultado.stderr)
        return

    diferenca = executar(["git", "diff", "--cached", "--quiet"])

    if diferenca.returncode == 1:
        horario = datetime.now().strftime("%d/%m/%Y %H:%M")

        commit = executar([
            "git", "commit", "-m",
            f"Atualizacao automatica - {horario}"
        ])

        if commit.returncode != 0:
            registrar("Erro no commit: " + commit.stderr)
            return

        registrar("Alteracoes registradas!")

    elif diferenca.returncode != 0:
        registrar("Erro ao verificar alteracoes.")
        return

    # Verifica se existem commits pendentes de envio
    pendentes = executar([
        "git", "rev-list", "--count", "@{u}..HEAD"
    ])

    if pendentes.returncode != 0:
        registrar("Nao foi possivel verificar o envio ao GitHub.")
        return

    if int(pendentes.stdout.strip() or "0") > 0:
        agora = time.monotonic()

        if agora - ULTIMA_TENTATIVA_PUSH < 30:
            return

        ULTIMA_TENTATIVA_PUSH = agora

        envio = executar(["git", "push"])

        if envio.returncode == 0:
            registrar("GitHub atualizado com sucesso!")
        else:
            registrar("Falha no envio. Tentarei novamente.")
            registrar(envio.stderr.strip())


def main():
    registrar("Monitor Jurema iniciado!")

    if not (PASTA / ".git").exists():
        registrar("ERRO: pasta Git nao encontrada.")
        return

    snapshot_anterior = obter_snapshot()
    ultima_mudanca = time.monotonic()

    while True:
        time.sleep(INTERVALO)

        snapshot_atual = obter_snapshot()

        if snapshot_atual != snapshot_anterior:
            snapshot_anterior = snapshot_atual
            ultima_mudanca = time.monotonic()
            registrar("Alteracao detectada. Aguardando...")
            continue

        if time.monotonic() - ultima_mudanca >= TEMPO_ESTAVEL:
            sincronizar()
            ultima_mudanca = time.monotonic()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        registrar("Monitor encerrado.")

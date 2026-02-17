#!/usr/bin/env python3
"""Genera un par de claves BSV (PrivateKey WIF + dirección pública) para KAIROS.

Uso:
    python generate_wallet.py

La clave privada WIF generada se debe pegar en backend/.env como BSV_PRIVATE_KEY.
La dirección pública es la que puedes compartir y buscar en https://whatsonchain.com
para comprobar las transacciones de notarización de auditoría.

⚠️  GUARDA LA CLAVE PRIVADA EN UN LUGAR SEGURO. Si la pierdes, no podrás
    firmar nuevas transacciones.
"""

import sys

try:
    from bsv import PrivateKey
except ImportError:
    print("❌  Paquete 'bsv-sdk' no instalado.")
    print("   Instálalo con:  pip install bsv-sdk")
    sys.exit(1)


def main():
    key = PrivateKey()                    # genera aleatoriamente
    wif = key.wif()                       # clave privada en formato WIF
    address = key.address()               # dirección pública (P2PKH)

    print("=" * 64)
    print("  🔑  NUEVA WALLET BSV PARA KAIROS CDS")
    print("=" * 64)
    print()
    print(f"  Dirección pública (nº de cartera):")
    print(f"    {address}")
    print()
    print(f"  Clave privada (WIF) — NO COMPARTIR:")
    print(f"    {wif}")
    print()
    print("  👉  Pega la clave privada en backend/.env:")
    print(f"       BSV_PRIVATE_KEY={wif}")
    print()
    print(f"  🔍  Verifica transacciones en:")
    print(f"       https://whatsonchain.com/address/{address}")
    print()
    print("  💰  Para notarizar, la dirección necesita un saldo mínimo de BSV.")
    print("       Cada OP_RETURN cuesta ~1 satoshi (~0.00000001 BSV).")
    print("=" * 64)


if __name__ == "__main__":
    main()

"""Merkle Tree para batching de audit logs en una sola transacción BSV.

En lugar de una TX por cada audit log (~$0.01-0.03 c/u), agrupamos
N hashes en un Merkle Tree y subimos solo la raíz a BSV.

Coste: 1 TX = miles de logs certificados. Cada log individual sigue
siendo verificable con su Merkle Proof (camino del leaf a la raíz).

Estructura del árbol:
    - Hojas: SHA-256 hashes de audit logs individuales
    - Nodos internos: SHA-256(left || right)
    - Si un nivel tiene número impar, se duplica el último nodo
"""

from __future__ import annotations

import hashlib
from typing import Any


def _hash_pair(left: str, right: str) -> str:
    """Hash SHA-256 de dos hashes concatenados (hex strings)."""
    combined = bytes.fromhex(left) + bytes.fromhex(right)
    return hashlib.sha256(combined).hexdigest()


def build_merkle_tree(leaf_hashes: list[str]) -> dict[str, Any]:
    """Construye un Merkle Tree a partir de una lista de hashes.

    Returns:
        {
            "root": str,               # Merkle root hash
            "leaves": list[str],        # Hashes originales (hojas)
            "leaf_count": int,
            "levels": list[list[str]],  # Todos los niveles del árbol
        }

    Raises:
        ValueError: Si la lista está vacía.
    """
    if not leaf_hashes:
        raise ValueError("Cannot build Merkle tree from empty list")

    if len(leaf_hashes) == 1:
        return {
            "root": leaf_hashes[0],
            "leaves": leaf_hashes,
            "leaf_count": 1,
            "levels": [leaf_hashes],
        }

    levels: list[list[str]] = [list(leaf_hashes)]

    current = list(leaf_hashes)
    while len(current) > 1:
        # Si impar, duplicar último nodo
        if len(current) % 2 != 0:
            current.append(current[-1])

        next_level = []
        for i in range(0, len(current), 2):
            next_level.append(_hash_pair(current[i], current[i + 1]))
        levels.append(next_level)
        current = next_level

    return {
        "root": current[0],
        "leaves": list(leaf_hashes),
        "leaf_count": len(leaf_hashes),
        "levels": levels,
    }


def get_merkle_proof(leaf_hash: str, tree: dict[str, Any]) -> list[dict[str, str]] | None:
    """Genera el Merkle Proof (camino de verificación) para un leaf.

    Devuelve una lista de pasos [{hash, position}] donde position
    es 'left' o 'right' indicando de qué lado va el sibling.

    Returns:
        Lista de pasos del proof, o None si el leaf no está en el árbol.
    """
    levels = tree["levels"]

    # Buscar índice del leaf en el nivel 0
    try:
        idx = levels[0].index(leaf_hash)
    except ValueError:
        return None

    proof: list[dict[str, str]] = []
    current_idx = idx

    for level in levels[:-1]:  # No incluir la raíz
        # Padear con duplicado si impar
        padded = list(level)
        if len(padded) % 2 != 0:
            padded.append(padded[-1])

        if current_idx % 2 == 0:
            # El sibling está a la derecha
            sibling_idx = current_idx + 1
            proof.append({
                "hash": padded[sibling_idx],
                "position": "right",
            })
        else:
            # El sibling está a la izquierda
            sibling_idx = current_idx - 1
            proof.append({
                "hash": padded[sibling_idx],
                "position": "left",
            })

        current_idx = current_idx // 2

    return proof


def verify_merkle_proof(
    leaf_hash: str,
    proof: list[dict[str, str]],
    expected_root: str,
) -> bool:
    """Verifica un Merkle Proof: recorre el camino del leaf a la raíz.

    Si el hash recalculado coincide con expected_root, el leaf
    está incluido en el batch y no fue alterado.
    """
    current = leaf_hash

    for step in proof:
        sibling = step["hash"]
        if step["position"] == "right":
            current = _hash_pair(current, sibling)
        else:
            current = _hash_pair(sibling, current)

    return current == expected_root

#!/usr/bin/env python3
"""PreToolUse (Write|Edit|MultiEdit|NotebookEdit): bloquea escrituras en rutas protegidas.

Protegidas: el repo fuente, .claude/hooks/, .claude/settings.json y quizfmt/.
exit 2 = se cancela la acción y el agente recibe el motivo.
"""
from _common import PROTECTED, fail, is_under, read_input, rel, target_path

p = target_path(read_input())
if p:
    for prot in PROTECTED:
        if is_under(p, prot):
            fail(
                f"Bloqueado: '{rel(p)}' es de solo lectura para los agentes.",
                ["Si hace falta cambiarlo, explícale a la persona qué y por qué; lo cambia ella."],
            )

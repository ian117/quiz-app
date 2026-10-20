"""Tests del parser. Correr: python3 -m pytest quizfmt  (o python3 quizfmt/test_quizfmt.py)"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quizfmt import check_question, parse_text, validate_tree  # noqa: E402

OPTS = """
- [x] Una copia en memoria del DOM que React compara para aplicar cambios
- [ ] Un DOM paralelo que el navegador renderiza en otro hilo aparte
- [ ] Una caché del HTML que evita volver a llamar al servidor web
- [ ] El DOM real, pero sin eventos para que sea más rápido de usar
"""


def issues_for(md: str, topic: str = "react") -> list[str]:
    qs, issues = parse_text(md)
    for q in qs:
        issues += check_question(q, topic, "<t>")
    return [i.msg for i in issues]


def test_valido_minimo():
    md = f"## react-vdom\n¿Qué es el Virtual DOM?\ntags: frecuente, fundamentos\n{OPTS}\n> Explicación: diffing.\n"
    qs, issues = parse_text(md)
    assert issues == [] and issues_for(md) == []
    assert qs[0].tags == ["frecuente", "fundamentos"] and qs[0].position == 1


def test_codigo_en_pregunta_y_explicacion_multilinea():
    md = """## react-estado
¿Qué muestra el botón tras un clic?

```jsx
## esto no es una key
- [x] esto no es una opción
setN(n + 1); setN(n + 1);
```

- [x] 1
- [ ] 2
- [ ] 0
- [ ] undefined

> Explicación: ambas llamadas usan el mismo `n`.
>
> ```js
> setN(prev => prev + 1)
> ```
"""
    qs, _ = parse_text(md)
    assert len(qs) == 1, "el '## ' dentro del código no debe abrir otra pregunta"
    assert len(qs[0].options) == 4
    assert "setN(prev" in qs[0].explanation_md
    assert issues_for(md) == [], "opciones cortas no deben fallar por largo"


def test_errores_de_formato():
    md = "## React Mal\n¿P?\n- [x] a\n- [x] b\n- [ ] c\n"
    msgs = " | ".join(issues_for(md))
    for frag in ("slug", "exactamente un [x]", "al menos tres", "falta la explicación"):
        assert frag in msgs


def test_correcta_delatada_por_largo():
    md = """## react-x
¿Pregunta?
- [x] Una respuesta correcta muchísimo más larga y detallada que cualquiera de las otras opciones
- [ ] Distractor de largo normal aquí
- [ ] Otro distractor de largo normal
- [ ] Tercer distractor de largo normal
> Explicación: x.
"""
    assert any("más larga" in m for m in issues_for(md))


def test_tags_prohibidos_y_prefijo_de_key():
    md = f"## node-x\n¿P?\ntags: importante, avanzada\n{OPTS}\n> Explicación: x.\n"
    msgs = " | ".join(issues_for(md))
    assert "debe empezar con el tema" in msgs
    assert "'importante' no permitido" in msgs and "'avanzada' no permitido" in msgs


def test_texto_entre_opciones_y_codigo_sin_cerrar():
    md = "## react-x\n¿P?\n- [x] a\nsuelto\n- [ ] b\n```\n"
    msgs = " | ".join(issues_for(md))
    assert "texto inesperado" in msgs and "sin cerrar" in msgs


def test_arbol_ubicacion_y_keys_duplicadas():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "frontend").mkdir()
        (root / "backend").mkdir()
        (root / "inventada").mkdir()
        q = f"## react-vdom\n¿P?\n{OPTS}\n> Explicación: x.\n"
        (root / "frontend" / "react.md").write_text(q)
        (root / "backend" / "react.md").write_text(q)
        (root / "inventada" / "x.md").write_text(q.replace("react-", "x-"))
        msgs = " | ".join(str(i) for i in validate_tree(root))
        assert "key ya usada" in msgs
        assert "categoría 'inventada' desconocida" in msgs


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)

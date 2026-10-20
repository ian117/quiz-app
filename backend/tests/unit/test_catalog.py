from __future__ import annotations

from app.domain.catalog import Catalog

from .builders import T0, T1, question, snapshot


def reconciled(*specs, area="frontend") -> Catalog:
    catalog = Catalog([], [])
    catalog.reconcile(snapshot(*specs, area=area), T0)
    return catalog


def test_crea_tema_preguntas_opciones_y_tags():
    catalog = Catalog([], [])
    report = catalog.reconcile(snapshot(question(tags=("frecuente", "hooks"))), T0)

    assert catalog.topics["react"].area == "frontend"
    assert catalog.topics["react"].name == "React"
    q = catalog.questions["react-uno"]
    assert q.tags == {"frecuente", "hooks"}
    assert [(o.text_md, o.is_correct) for o in q.options] == [
        ("A", True), ("B", False), ("C", False), ("D", False),
    ]  # fmt: skip
    assert (report.topics_created, report.questions_created, report.options_created) == (1, 1, 4)


def test_segunda_vez_no_cambia_nada():
    catalog = reconciled(question(), question("react-dos", position=2))
    report = catalog.reconcile(snapshot(question(), question("react-dos", position=2)), T1)

    assert not report.changed


def test_pregunta_que_desaparece_se_retira_sin_borrarse():
    catalog = reconciled(question(), question("react-dos", position=2))
    report = catalog.reconcile(snapshot(question()), T1)

    assert report.questions_retired == 1
    assert catalog.questions["react-dos"].retired_at == T1
    assert catalog.questions["react-uno"].retired_at is None


def test_retirar_conserva_la_fecha_original():
    catalog = reconciled(question(), question("react-dos", position=2))
    catalog.reconcile(snapshot(question()), T0)
    report = catalog.reconcile(snapshot(question()), T1)

    assert not report.changed
    assert catalog.questions["react-dos"].retired_at == T0


def test_pregunta_que_vuelve_se_reactiva():
    catalog = reconciled(question(), question("react-dos", position=2))
    catalog.reconcile(snapshot(question()), T0)
    report = catalog.reconcile(snapshot(question(), question("react-dos", position=2)), T1)

    assert report.questions_reactivated == 1
    assert report.questions_updated == 0
    assert catalog.questions["react-dos"].retired_at is None


def test_insertar_en_medio_recalcula_position_sin_crear_duplicados():
    catalog = reconciled(question("react-a", position=1), question("react-b", position=2))
    report = catalog.reconcile(
        snapshot(
            question("react-a", position=1),
            question("react-nueva", position=2),
            question("react-b", position=3),
        ),
        T1,
    )

    assert report.questions_created == 1
    assert report.questions_updated == 1
    assert catalog.questions["react-b"].position == 3


def test_editar_prompt_explicacion_y_tags_actualiza_en_sitio():
    catalog = reconciled(question(tags=("hooks",)))
    report = catalog.reconcile(
        snapshot(question(prompt="¿Otra?", explanation="Nueva.", tags=("senior",))), T1
    )

    q = catalog.questions["react-uno"]
    assert (q.prompt_md, q.explanation_md, q.tags) == ("¿Otra?", "Nueva.", {"senior"})
    assert report.questions_updated == 1


def test_cambiar_de_area_actualiza_el_tema():
    catalog = reconciled(question(), area="frontend")
    report = catalog.reconcile(snapshot(question(), area="fundamentos"), T1)

    assert catalog.topics["react"].area == "fundamentos"
    assert report.topics_updated == 1


class TestOpciones:
    def test_mismo_texto_actualiza_is_correct_en_la_misma_fila(self):
        catalog = reconciled(question())
        catalog.questions["react-uno"].options[0].id = 10
        catalog.questions["react-uno"].options[1].id = 11

        catalog.reconcile(
            snapshot(question(options=(("A", False), ("B", True), ("C", False), ("D", False)))),
            T1,
        )

        opts = {o.text_md: o for o in catalog.questions["react-uno"].options}
        assert (opts["A"].id, opts["A"].is_correct) == (10, False)
        assert (opts["B"].id, opts["B"].is_correct) == (11, True)
        assert all(o.retired_at is None for o in opts.values())

    def test_texto_nuevo_crea_fila_y_retira_la_vieja(self):
        catalog = reconciled(question())
        report = catalog.reconcile(
            snapshot(question(options=(("A", True), ("B", False), ("C", False), ("E", False)))),
            T1,
        )

        opts = {o.text_md: o for o in catalog.questions["react-uno"].options}
        assert len(opts) == 5
        assert opts["D"].retired_at == T1
        assert opts["E"].retired_at is None
        assert (report.options_created, report.options_retired) == (1, 1)

    def test_texto_retirado_que_vuelve_se_reactiva(self):
        catalog = reconciled(question())
        catalog.reconcile(
            snapshot(question(options=(("A", True), ("B", False), ("C", False), ("E", False)))),
            T0,
        )
        report = catalog.reconcile(snapshot(question()), T1)

        opts = {o.text_md: o for o in catalog.questions["react-uno"].options}
        assert len(opts) == 5  # nunca se borra ni se duplica
        assert opts["D"].retired_at is None
        assert opts["E"].retired_at == T1
        assert report.options_reactivated == 1

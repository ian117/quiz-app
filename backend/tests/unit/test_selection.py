from __future__ import annotations

from random import Random

from app.domain.selection import Candidate, Order, Stretch, select_questions


def cand(qid, topic="react", area="frontend", position=None, *tags) -> Candidate:
    return Candidate(qid, topic, area, position or qid, frozenset(tags))


POOL = [
    cand(1, "react", "frontend", 1, "frecuente", "hooks"),
    cand(2, "react", "frontend", 2, "hooks"),
    cand(3, "react", "frontend", 3, "frecuente"),
    cand(4, "node", "backend", 1, "frecuente"),
    cand(5, "node", "backend", 2, "senior"),
    cand(6, "python", "backend", 1),
]


def pick(*plan: Stretch, seed: int = 0) -> list[int]:
    return select_questions(POOL, plan, Random(seed))


class TestFiltros:
    def test_por_tema(self):
        assert sorted(pick(Stretch(topic="react"))) == [1, 2, 3]

    def test_varios_temas_es_or(self):
        assert sorted(pick(Stretch(topics=("react", "python")))) == [1, 2, 3, 6]

    def test_por_area(self):
        assert sorted(pick(Stretch(area="backend"))) == [4, 5, 6]

    def test_varios_tags_es_or(self):
        assert sorted(pick(Stretch(tags=("hooks", "senior")))) == [1, 2, 5]

    def test_claves_distintas_se_combinan_con_and(self):
        assert sorted(pick(Stretch(area="backend", tags=("frecuente", "senior")))) == [4, 5]

    def test_sin_filtro_son_todas(self):
        assert sorted(pick(Stretch())) == [1, 2, 3, 4, 5, 6]

    def test_filtro_sin_coincidencias(self):
        assert pick(Stretch(topic="rust")) == []


class TestCantidad:
    def test_n_limita(self):
        assert len(pick(Stretch(area="backend", n=2))) == 2

    def test_n_mayor_que_lo_disponible_aporta_lo_que_hay(self):
        assert len(pick(Stretch(topic="react", n=50))) == 3

    def test_n_ausente_son_todas(self):
        assert len(pick(Stretch(topic="react"))) == 3


class TestTramos:
    def test_una_pregunta_no_se_repite_entre_tramos(self):
        ids = pick(Stretch(tags=("frecuente",), n=3), Stretch(topic="react"))

        assert len(ids) == len(set(ids))
        assert sorted(ids) == [1, 2, 3, 4]  # los 3 frecuentes y el react que faltaba

    def test_los_tramos_se_juegan_en_orden(self):
        ids = pick(Stretch(topic="python"), Stretch(topic="node", order=Order.IN_ORDER))

        assert ids == [6, 4, 5]

    def test_entrevista_por_fases(self):
        ids = pick(
            Stretch(tags=("frecuente",), n=1, order=Order.IN_ORDER),
            Stretch(area="backend", n=2),
            Stretch(topic="react", n=1),
        )

        assert ids[0] == 4  # en orden: 'node' va antes que 'react'
        assert len(ids) == 4 and len(set(ids)) == 4


class TestOrden:
    def test_en_orden_usa_position_dentro_del_tema(self):
        assert pick(Stretch(order=Order.IN_ORDER)) == [4, 5, 6, 1, 2, 3]

    def test_random_es_reproducible_con_la_misma_semilla(self):
        assert pick(Stretch(), seed=3) == pick(Stretch(), seed=3)

    def test_random_cambia_con_otra_semilla(self):
        assert len({tuple(pick(Stretch(), seed=s)) for s in range(10)}) > 1

    def test_frecuentes_primero(self):
        for seed in range(20):
            ids = pick(Stretch(order=Order.FREQUENT_FIRST), seed=seed)

            assert set(ids[:3]) == {1, 3, 4}  # los frecuentes, luego el resto
            assert set(ids[3:]) == {2, 5, 6}

    def test_frecuentes_primero_con_n_toma_de_los_frecuentes(self):
        ids = pick(Stretch(order=Order.FREQUENT_FIRST, n=2), seed=1)

        assert set(ids) <= {1, 3, 4}

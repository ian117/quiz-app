from __future__ import annotations

from collections import Counter

from app.domain.shuffle import shuffle_option_ids

IDS = [1, 2, 3, 4]


def test_misma_semilla_mismo_orden():
    assert shuffle_option_ids(IDS, 7, 3) == shuffle_option_ids(IDS, 7, 3)


def test_es_una_permutacion_de_las_opciones():
    assert sorted(shuffle_option_ids(IDS, 7, 3)) == IDS


def test_no_depende_del_orden_de_entrada():
    assert shuffle_option_ids([4, 2, 1, 3], 7, 3) == shuffle_option_ids(IDS, 7, 3)


def test_semillas_distintas_dan_ordenes_distintos():
    orders = {tuple(shuffle_option_ids(IDS, s, 3)) for s in range(1, 200)}

    assert len(orders) > 10  # hay 24 posibles


def test_la_sesion_y_la_pregunta_no_se_confunden():
    # Sin separador, (1, 23) y (12, 3) serían la misma cadena.
    orders = {tuple(shuffle_option_ids(IDS, s, q)) for s, q in [(1, 23), (12, 3), (123, 0)]}

    assert len(orders) > 1


def test_la_correcta_no_queda_fija_en_una_posicion():
    # La correcta va primero en el markdown: es la de menor id. Se mide dónde acaba.
    n = 2000
    positions = Counter(
        shuffle_option_ids(IDS, session_id, 5).index(1) for session_id in range(1, n + 1)
    )

    assert set(positions) == {0, 1, 2, 3}
    for count in positions.values():
        assert 0.20 * n <= count <= 0.30 * n  # lo esperado es 25%, con holgura


def test_la_correcta_tampoco_se_fija_variando_solo_la_pregunta():
    n = 2000
    positions = Counter(shuffle_option_ids(IDS, 1, q).index(1) for q in range(n))

    assert set(positions) == {0, 1, 2, 3}
    assert max(positions.values()) <= 0.30 * n


def test_retirar_una_opcion_no_mueve_a_las_demas():
    full = shuffle_option_ids(IDS, 7, 3)
    without_two = shuffle_option_ids([1, 3, 4], 7, 3)

    assert without_two == [i for i in full if i != 2]


def test_orden_fijado_para_no_reordenar_el_historial():
    # Si este test falla, cambió el algoritmo y las sesiones pasadas se verían distintas.
    assert shuffle_option_ids(IDS, 1, 1) == [3, 2, 1, 4]
    assert shuffle_option_ids(IDS, 1, 2) == [1, 2, 4, 3]
    assert shuffle_option_ids(IDS, 42, 7) == [1, 3, 4, 2]

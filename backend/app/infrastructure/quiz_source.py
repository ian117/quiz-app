"""QuizSource sobre quiz/*.md. La convención vive en quizfmt: aquí no se reimplementa."""
from __future__ import annotations

from pathlib import Path

import quizfmt
from app.application.ports import InvalidQuiz
from app.domain.catalog import OptionSpec, QuestionSpec, QuizSnapshot, TopicSpec


class QuizFileSource:
    def __init__(self, quiz_dir: Path) -> None:
        self._quiz_dir = quiz_dir

    def load(self) -> QuizSnapshot:
        if not self._quiz_dir.is_dir():
            raise InvalidQuiz(f"no existe el directorio del quiz: {self._quiz_dir}")
        try:
            files = quizfmt.load_tree(self._quiz_dir)
        except ValueError as exc:
            raise InvalidQuiz(str(exc)) from exc

        topics: dict[str, TopicSpec] = {}
        questions: list[QuestionSpec] = []
        for f in files:
            if f.topic in topics:
                # topic.slug es UNIQUE: un mismo tema no puede colgar de dos áreas.
                raise InvalidQuiz(
                    f"el tema '{f.topic}' aparece en dos categorías: "
                    f"'{topics[f.topic].area}' y '{f.category}'"
                )
            topics[f.topic] = TopicSpec(slug=f.topic, area=f.category)
            questions += [
                QuestionSpec(
                    key=q.key,
                    topic_slug=f.topic,
                    position=q.position,
                    prompt_md=q.prompt_md,
                    explanation_md=q.explanation_md,
                    options=tuple(OptionSpec(o.text, o.correct) for o in q.options),
                    tags=tuple(q.tags),
                )
                for q in f.questions
            ]
        return QuizSnapshot(tuple(topics.values()), tuple(questions))

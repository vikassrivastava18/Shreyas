from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from api.v3.answer import review_response, start_dialogue
from core.db.schemas import AnswerSchema, ChapterInputRequest


class StartDialogueTests(TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.chapter = SimpleNamespace(
            subtopics=[
                SimpleNamespace(
                    content="Notes about fractions",
                    subtopic_name="Fractions",
                )
            ]
        )
        self.db.query.return_value.filter.return_value.first.return_value = (
            self.chapter
        )

    @patch("api.v3.answer.uuid.uuid4")
    @patch("api.v3.answer.AnswerGraph.build_graph")
    def test_returns_question_and_session_id(self, build_graph, uuid4):
        session_id = "8de0f665-600f-4cf2-b2c8-c8b10058000f"
        uuid4.return_value = session_id
        graph = MagicMock()
        graph.stream.return_value = iter(
            [{"__interrupt__": [SimpleNamespace(value="What is a fraction?")]}]
        )
        build_graph.return_value = graph

        response = start_dialogue(ChapterInputRequest(chapter_id=7), self.db)

        self.assertEqual(
            response,
            {
                "question": "What is a fraction?",
                "session_id": session_id,
            },
        )
        graph.stream.assert_called_once_with(
            {
                "topics": [
                    {
                        "notes": "Notes about fractions",
                        "topic": "Fractions",
                    }
                ],
                "topic": {},
                "index": -1,
                "max_ind": 1,
            },
            {"configurable": {"thread_id": session_id}},
        )

    @patch("api.v3.answer.AnswerGraph.build_graph")
    def test_missing_chapter_returns_not_found(self, build_graph):
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as raised:
            start_dialogue(ChapterInputRequest(chapter_id=99), self.db)

        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.detail, "Chapter not found")
        build_graph.assert_not_called()

    @patch("api.v3.answer.AnswerGraph.build_graph")
    def test_graph_error_returns_internal_server_error(self, build_graph):
        graph = MagicMock()
        graph.stream.side_effect = RuntimeError("graph unavailable")
        build_graph.return_value = graph

        with self.assertRaises(HTTPException) as raised:
            start_dialogue(ChapterInputRequest(chapter_id=7), self.db)

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(raised.exception.detail, "Internal server error")


class ReviewResponseTests(TestCase):
    @patch("api.v3.answer.AnswerGraph.build_graph")
    def test_returns_assessment_when_graph_interrupts(self, build_graph):
        graph = MagicMock()
        graph.stream.return_value = iter(
            [{"__interrupt__": [SimpleNamespace(value="Try another example.")]}]
        )
        graph.get_state.return_value.values = {
            "topic": {"assessment": "Needs more practice"}
        }
        build_graph.return_value = graph
        request = AnswerSchema(session_id="session-123", answer="My answer")

        response = review_response(request)

        self.assertEqual(
            response,
            {
                "response": "Try another example.",
                "session_id": "session-123",
                "complete": False,
                "assessment": "Needs more practice",
            },
        )
        command, config = graph.stream.call_args.args
        self.assertEqual(command.resume, "My answer")
        self.assertEqual(
            config, {"configurable": {"thread_id": "session-123"}}
        )

    @patch("api.v3.answer.AnswerGraph.build_graph")
    def test_returns_completion_when_graph_has_no_interrupt(self, build_graph):
        graph = MagicMock()
        graph.stream.return_value = iter([])
        build_graph.return_value = graph

        response = review_response(
            AnswerSchema(session_id="session-123", answer="My answer")
        )

        self.assertEqual(
            response,
            {
                "response": "Session completed!",
                "session_id": "session-123",
                "complete": True,
            },
        )

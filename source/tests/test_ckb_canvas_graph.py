from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "prototypes" / "ckb-canvas-skill"
FIXTURE = REPO / "tests" / "fixtures" / "obsidian-canvas-agent-visualization"
sys.path[:0] = [str(REPO), str(SKILL), str(FIXTURE)]

from ckb_canvas.commands import validate_only
from ckb_canvas.contracts import CanvasFailure
from ckb_canvas.freeze import load_and_freeze_request
from ckb_canvas.graph import canonical_canvas_bytes, layout_graph, select_graph, validate_canvas
from runtime_builder import build_case, sha256, write_json


class CanvasGraphTests(unittest.TestCase):
    def test_maximal_selection_has_12_nodes_stable_order_and_fixed_coordinates(self) -> None:
        case = build_case("maximal-graph", page_count=6, record_count=2, source_count=3)
        try:
            frozen = load_and_freeze_request(case.request)
            selected = select_graph(frozen)
            first = layout_graph(selected, frozen)
            second = layout_graph(select_graph(frozen), frozen)
            facts = validate_canvas(first, frozen, selected)
            self.assertEqual(12, facts.node_count)
            self.assertEqual(11, facts.edge_count)
            self.assertEqual({"text": 1, "page": 6, "record": 2, "source": 3}, facts.role_counts)
            self.assertEqual(canonical_canvas_bytes(first), canonical_canvas_bytes(second))
            self.assertEqual(["text"] + ["file"] * 8 + ["link"] * 3, [node["type"] for node in first["nodes"]])
            pages = first["nodes"][1:7]
            self.assertEqual([index * 260 for index in range(6)], [node["y"] for node in pages])
            self.assertTrue(all(node["x"] == 480 and node["width"] == 360 and node["height"] == 220 for node in pages))
            sources = first["nodes"][-3:]
            self.assertEqual([0, 260, 520], [node["y"] for node in sources])
            self.assertTrue(all(node["x"] == 960 and node["height"] == 160 for node in sources))
            labels = [edge["label"] for edge in first["edges"]]
            self.assertEqual(["检索命中"] * 6 + ["相关记录"] * 2 + ["来源核对"] * 3, labels)
            self.assertTrue(all(len(item["id"]) == 16 for item in first["nodes"] + first["edges"]))
        finally:
            case.cleanup()

    def test_duplicate_page_and_source_keep_first_record_ordinal(self) -> None:
        case = build_case("dedup-order", page_count=2, record_count=1, source_count=2)
        try:
            record = json.loads(case.record.read_text(encoding="utf-8"))
            record["selected_entities"][1]["human_page_file"] = record["selected_entities"][0]["human_page_file"]
            record["selected_entities"][1]["source_path"] = record["selected_entities"][0]["source_path"]
            record["selected_entities"][1]["start_line"] = record["selected_entities"][0]["start_line"]
            record["selected_entities"][1]["end_line"] = record["selected_entities"][0]["end_line"]
            write_json(case.record, record)
            request = case.request_value()
            request["ckb"]["record_sha256"] = sha256(case.record)
            case.write_request(request)
            selected = select_graph(load_and_freeze_request(case.request))
            self.assertEqual([0], [item.ordinal for item in selected.pages])
            self.assertEqual([0], [item.owner_ordinal for item in selected.sources])
        finally:
            case.cleanup()

    def test_required_page_budget_is_not_silently_dropped(self) -> None:
        case = build_case("page-budget", page_count=7, record_count=0, source_count=0)
        try:
            request = case.request_value()
            request["request"]["required_entries"] = [
                {"kind": "selected_entity", "ordinal": index, "require": "page"} for index in range(7)
            ]
            case.write_request(request)
            with self.assertRaises(CanvasFailure) as raised:
                validate_only(case.request)
            self.assertEqual("budget_exceeded", raised.exception.reason)
            self.assertEqual(5, raised.exception.exit_code)
            self.assertFalse(case.target.exists())
        finally:
            case.cleanup()

    def test_dangling_edge_duplicate_id_and_machine_field_are_distinct_failures(self) -> None:
        case = build_case("graph-negative")
        try:
            frozen = load_and_freeze_request(case.request)
            selected = select_graph(frozen)
            canvas = layout_graph(selected, frozen)

            dangling = copy.deepcopy(canvas)
            dangling["edges"][0]["toNode"] = "ffffffffffffffff"
            with self.assertRaises(CanvasFailure) as raised:
                validate_canvas(dangling, frozen, selected)
            self.assertEqual("dangling_edge", raised.exception.reason)

            duplicate = copy.deepcopy(canvas)
            duplicate["nodes"][1]["id"] = duplicate["nodes"][0]["id"]
            with self.assertRaises(CanvasFailure) as raised:
                validate_canvas(duplicate, frozen, selected)
            self.assertEqual("duplicate_id", raised.exception.reason)

            leaked = copy.deepcopy(canvas)
            leaked["nodes"][0]["text"] += "\nentity_id"
            with self.assertRaises(CanvasFailure) as raised:
                validate_canvas(leaked, frozen, selected)
            self.assertEqual("invalid_canvas", raised.exception.reason)
        finally:
            case.cleanup()

    def test_collision_hook_never_adds_random_salt(self) -> None:
        case = build_case("stable-id-collision")
        try:
            frozen = load_and_freeze_request(case.request)
            selected = select_graph(frozen)
            with mock.patch("ckb_canvas.graph._stable_id", return_value="0" * 16):
                canvas = layout_graph(selected, frozen)
                with self.assertRaises(CanvasFailure) as raised:
                    validate_canvas(canvas, frozen, selected)
            self.assertEqual("duplicate_id", raised.exception.reason)
        finally:
            case.cleanup()

    def test_invalid_source_range_is_rejected(self) -> None:
        case = build_case("invalid-source-range")
        try:
            record = json.loads(case.record.read_text(encoding="utf-8"))
            record["selected_entities"][0]["end_line"] = 999
            write_json(case.record, record)
            request = case.request_value()
            request["ckb"]["record_sha256"] = sha256(case.record)
            case.write_request(request)
            with self.assertRaises(CanvasFailure) as raised:
                validate_only(case.request)
            self.assertEqual("invalid_source_range", raised.exception.reason)
        finally:
            case.cleanup()


if __name__ == "__main__":
    unittest.main()

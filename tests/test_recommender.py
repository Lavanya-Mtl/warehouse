"""
Tests for the box recommendation algorithm.
These tests do NOT require the database — pure unit tests.
"""
import pytest
from recommender.service import (
    ItemDimension,
    BoundingBox,
    compute_bounding_box,
    recommend_box,
    RecommendationResult,
)
from unittest.mock import MagicMock


def make_box(name, length, width, height, max_weight, cost, active=True):
    """Helper to create a mock Box-like object."""
    box = MagicMock()
    box.name = name
    box.internal_length_cm = length
    box.internal_width_cm = width
    box.internal_height_cm = height
    box.max_weight_kg = max_weight
    box.cost_rupees = cost
    box.is_active = active
    return box


# ── compute_bounding_box ─────────────────────────────────────────────────────

class TestComputeBoundingBox:
    def test_single_item_single_unit(self):
        items = [ItemDimension(length_cm=10, width_cm=8, height_cm=5, weight_kg=1.0, quantity=1)]
        bb = compute_bounding_box(items)
        # Largest dim = 10, middle = 8, smallest = 5 (becomes height)
        assert bb.length_cm == 10
        assert bb.width_cm == 8
        assert bb.height_cm == 5
        assert bb.total_weight_kg == pytest.approx(1.0)

    def test_single_item_multiple_units_stacks_height(self):
        items = [ItemDimension(length_cm=10, width_cm=8, height_cm=5, weight_kg=1.0, quantity=3)]
        bb = compute_bounding_box(items)
        assert bb.length_cm == 10
        assert bb.width_cm == 8
        # 3 units stacked — height is 3 * smallest_dim = 3 * 5 = 15
        assert bb.height_cm == pytest.approx(15)
        assert bb.total_weight_kg == pytest.approx(3.0)

    def test_two_different_items(self):
        items = [
            ItemDimension(length_cm=20, width_cm=10, height_cm=5, weight_kg=2.0, quantity=1),
            ItemDimension(length_cm=15, width_cm=12, height_cm=8, weight_kg=1.5, quantity=1),
        ]
        bb = compute_bounding_box(items)
        # footprint = max(20, 15) × max(10, 12)
        assert bb.length_cm == 20
        assert bb.width_cm == 12
        # heights stack: 5 + 8 = 13
        assert bb.height_cm == pytest.approx(13)
        assert bb.total_weight_kg == pytest.approx(3.5)

    def test_empty_items_returns_zero_bounding_box(self):
        bb = compute_bounding_box([])
        assert bb.length_cm == 0
        assert bb.width_cm == 0
        assert bb.height_cm == 0
        assert bb.total_weight_kg == 0

    def test_weight_accumulates_with_quantity(self):
        items = [
            ItemDimension(length_cm=5, width_cm=5, height_cm=5, weight_kg=0.5, quantity=4),
        ]
        bb = compute_bounding_box(items)
        assert bb.total_weight_kg == pytest.approx(2.0)

    def test_non_cubic_item_uses_smallest_as_height(self):
        # 30 × 5 × 5 — largest=30, others=5. Height should be 5 (smallest).
        items = [ItemDimension(length_cm=30, width_cm=5, height_cm=5, weight_kg=0.5, quantity=1)]
        bb = compute_bounding_box(items)
        assert bb.length_cm == 30
        assert bb.height_cm == 5


# ── BoundingBox.fits_in ───────────────────────────────────────────────────────

class TestBoundingBoxFitsIn:
    def _bb(self, l, w, h, wt=1.0):
        return BoundingBox(length_cm=l, width_cm=w, height_cm=h, total_weight_kg=wt)

    def test_fits_exactly(self):
        bb = self._bb(30, 20, 10)
        box = make_box("B", 30, 20, 10, 5, 100)
        assert bb.fits_in(box) is True

    def test_fits_smaller(self):
        bb = self._bb(10, 8, 5)
        box = make_box("B", 30, 20, 10, 5, 100)
        assert bb.fits_in(box) is True

    def test_does_not_fit_one_dim_too_large(self):
        bb = self._bb(31, 20, 10)
        box = make_box("B", 30, 20, 10, 5, 100)
        assert bb.fits_in(box) is False

    def test_fits_rotated(self):
        # bb is 30×10×20, box is 30×20×10 — should fit when rotated
        bb = self._bb(30, 10, 20)
        box = make_box("B", 30, 20, 10, 5, 100)
        assert bb.fits_in(box) is True

    def test_weight_check(self):
        bb = self._bb(10, 10, 10, wt=6.0)
        box = make_box("B", 50, 50, 50, 5, 100)
        assert bb.weight_fits_in(box) is False

    def test_weight_exactly_at_limit(self):
        bb = self._bb(10, 10, 10, wt=5.0)
        box = make_box("B", 50, 50, 50, 5, 100)
        assert bb.weight_fits_in(box) is True


# ── recommend_box ─────────────────────────────────────────────────────────────

class TestRecommendBox:
    def _single_item(self, l=10, w=8, h=5, wt=0.5):
        return [ItemDimension(length_cm=l, width_cm=w, height_cm=h, weight_kg=wt, quantity=1)]

    def test_recommends_cheapest_fitting_box(self):
        items = self._single_item()
        boxes = [
            make_box("Large", 50, 40, 30, 20, 200),
            make_box("Small", 20, 15, 10, 5, 80),   # cheapest that fits
            make_box("Tiny", 5, 4, 3, 1, 30),        # too small
        ]
        result = recommend_box(items, boxes)
        assert result.success is True
        assert result.recommended_box.name == "Small"

    def test_no_fit_returns_failure(self):
        items = self._single_item(l=100, w=100, h=100)
        boxes = [make_box("Tiny", 10, 10, 10, 1, 50)]
        result = recommend_box(items, boxes)
        assert result.success is False
        assert result.recommended_box is None

    def test_weight_too_heavy_returns_failure(self):
        items = [ItemDimension(10, 8, 5, weight_kg=50.0, quantity=1)]
        boxes = [make_box("Big", 100, 100, 100, max_weight=5, cost=100)]
        result = recommend_box(items, boxes)
        assert result.success is False

    def test_empty_items_returns_failure(self):
        boxes = [make_box("Box", 50, 50, 50, 20, 100)]
        result = recommend_box([], boxes)
        assert result.success is False

    def test_no_boxes_returns_failure(self):
        items = self._single_item()
        result = recommend_box(items, [])
        assert result.success is False

    def test_inactive_box_is_skipped(self):
        items = self._single_item()
        boxes = [
            make_box("Inactive", 50, 40, 30, 20, 50, active=False),
            make_box("Active", 50, 40, 30, 20, 200, active=True),
        ]
        result = recommend_box(items, boxes)
        assert result.success is True
        assert result.recommended_box.name == "Active"

    def test_returns_all_candidates(self):
        items = self._single_item()
        boxes = [
            make_box("Medium", 30, 20, 15, 5, 120),
            make_box("Large", 50, 40, 30, 20, 200),
            make_box("Small", 15, 12, 8, 5, 80),
        ]
        result = recommend_box(items, boxes)
        assert result.success is True
        # All three should be candidates
        assert len(result.all_candidates) == 3
        # First candidate should be cheapest
        assert result.all_candidates[0].cost_rupees == 80

    def test_multiple_items_combined(self):
        items = [
            ItemDimension(length_cm=20, width_cm=15, height_cm=10, weight_kg=1.0, quantity=2),
            ItemDimension(length_cm=10, width_cm=8, height_cm=5, weight_kg=0.5, quantity=1),
        ]
        # Bounding box: length=20, width=15, height = 10+10+5=25
        # weight = 1.0*2 + 0.5*1 = 2.5
        boxes = [
            make_box("Small", 20, 15, 20, 5, 80),   # height 20 < 25, won't fit
            make_box("Medium", 30, 20, 30, 5, 120),  # fits
        ]
        result = recommend_box(items, boxes)
        assert result.success is True
        assert result.recommended_box.name == "Medium"

    def test_result_reason_included(self):
        items = self._single_item()
        boxes = [make_box("Box", 50, 40, 30, 20, 100)]
        result = recommend_box(items, boxes)
        assert result.reason != ""
        assert "Box" in result.reason or "box" in result.reason.lower()
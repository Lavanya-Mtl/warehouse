"""
Box Recommendation Service
===========================
Algorithm: Bounding Box approach

Given a list of OrderItems, compute the bounding box needed to fit all items
and find the cheapest active Box that satisfies both:
  1. Bounding box dimensions fit inside the box's internal dimensions
  2. Total weight of all items ≤ box's max_weight_kg

Bounding box calculation:
  - We consider all axis-aligned orientations of item groups
  - Simple approach: sort items by largest dimension, stack them
  - The bounding box has:
      height = sum of all items' heights (stacked vertically)
      length = max of all items' lengths
      width  = max of all items' widths
  This is a conservative (safe) estimate — it may overestimate needed space
  but will never recommend a box that's actually too small.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class ItemDimension:
    """Represents a single unit of a product with its dimensions and weight."""
    length_cm: float
    width_cm: float
    height_cm: float
    weight_kg: float
    quantity: int = 1

    def sorted_dims(self) -> tuple[float, float, float]:
        """Return dimensions sorted descending: (largest, middle, smallest)."""
        dims = sorted(
            [self.length_cm, self.width_cm, self.height_cm], reverse=True
        )
        return (dims[0], dims[1], dims[2])


@dataclass
class BoundingBox:
    length_cm: float
    width_cm: float
    height_cm: float
    total_weight_kg: float

    def fits_in(self, box) -> bool:
        """
        Check whether this bounding box fits inside a Box model instance.
        Tries all 6 axis-aligned orientations of the bounding box.
        """
        l, w, h = self.length_cm, self.width_cm, self.height_cm
        bl = float(box.internal_length_cm)
        bw = float(box.internal_width_cm)
        bh = float(box.internal_height_cm)

        orientations = [
            (l, w, h), (l, h, w),
            (w, l, h), (w, h, l),
            (h, l, w), (h, w, l),
        ]
        for ol, ow, oh in orientations:
            if ol <= bl and ow <= bw and oh <= bh:
                return True
        return False

    def weight_fits_in(self, box) -> bool:
        return self.total_weight_kg <= float(box.max_weight_kg)


@dataclass
class RecommendationResult:
    success: bool
    recommended_box: Optional[object]  # Box model instance or None
    bounding_box: BoundingBox
    reason: str
    all_candidates: list  # All boxes that could fit, ordered by cost


def compute_bounding_box(items: list[ItemDimension]) -> BoundingBox:
    """
    Compute the bounding box required for a list of items (with quantities).

    Strategy:
    - Expand each item by its quantity (each unit stacked).
    - Sort all units by their largest dimension descending.
    - Stack them vertically (sum of heights after sorting each unit
      so its smallest dim is its height, keeping footprint minimal).
    - The bounding footprint is max(length) × max(width) across all units.

    This is a "worst-case stack" approximation — real packing may be more
    efficient, but this guarantees items will always fit in the recommended box.
    """
    if not items:
        return BoundingBox(0, 0, 0, 0)

    all_units: list[tuple[float, float, float]] = []
    total_weight = 0.0

    for item in items:
        dims = sorted(
            [item.length_cm, item.width_cm, item.height_cm], reverse=True
        )
        # largest=dims[0], middle=dims[1], smallest=dims[2]
        for _ in range(item.quantity):
            # Orient so tallest goes down the stack (use smallest as height)
            all_units.append((dims[0], dims[1], dims[2]))
        total_weight += item.weight_kg * item.quantity

    # Sort units so the largest footprint units are placed first
    all_units.sort(key=lambda u: u[0] * u[1], reverse=True)

    max_length = max(u[0] for u in all_units)
    max_width = max(u[1] for u in all_units)
    total_height = sum(u[2] for u in all_units)

    return BoundingBox(
        length_cm=max_length,
        width_cm=max_width,
        height_cm=total_height,
        total_weight_kg=total_weight,
    )


def recommend_box(items: list[ItemDimension], available_boxes) -> RecommendationResult:
    """
    Given a list of ItemDimension and a queryset/list of Box objects,
    return the cheapest box that fits all items.

    Args:
        items: list of ItemDimension
        available_boxes: QuerySet or list of Box instances (active boxes)

    Returns:
        RecommendationResult
    """
    bounding_box = compute_bounding_box(items)

    if not items:
        return RecommendationResult(
            success=False,
            recommended_box=None,
            bounding_box=bounding_box,
            reason="No items in order.",
            all_candidates=[],
        )

    # Filter boxes by weight first, then dimension
    candidates = []
    for box in available_boxes:
        if not box.is_active:
            continue
        if not bounding_box.weight_fits_in(box):
            continue
        if not bounding_box.fits_in(box):
            continue
        candidates.append(box)

    # Sort by cost ascending — pick cheapest
    candidates.sort(key=lambda b: b.cost_rupees)

    if candidates:
        return RecommendationResult(
            success=True,
            recommended_box=candidates[0],
            bounding_box=bounding_box,
            reason=(
                f"Bounding box: {bounding_box.length_cm:.1f} × "
                f"{bounding_box.width_cm:.1f} × "
                f"{bounding_box.height_cm:.1f} cm, "
                f"{bounding_box.total_weight_kg:.3f} kg. "
                f"{len(candidates)} box(es) fit; cheapest selected."
            ),
            all_candidates=candidates,
        )
    else:
        # Diagnose why nothing fits
        weight_failures = [
            b for b in available_boxes
            if b.is_active and not bounding_box.weight_fits_in(b)
        ]
        dim_failures = [
            b for b in available_boxes
            if b.is_active
            and bounding_box.weight_fits_in(b)
            and not bounding_box.fits_in(b)
        ]

        if not list(available_boxes):
            reason = "No boxes are configured in the system."
        elif weight_failures and not dim_failures:
            reason = (
                f"Order is too heavy ({bounding_box.total_weight_kg:.3f} kg). "
                f"No box can hold this weight."
            )
        elif dim_failures and not weight_failures:
            reason = (
                f"Order bounding box ({bounding_box.length_cm:.1f} × "
                f"{bounding_box.width_cm:.1f} × "
                f"{bounding_box.height_cm:.1f} cm) is too large for any available box."
            )
        else:
            reason = (
                f"No single box fits the order (bounding box: "
                f"{bounding_box.length_cm:.1f} × {bounding_box.width_cm:.1f} × "
                f"{bounding_box.height_cm:.1f} cm, "
                f"{bounding_box.total_weight_kg:.3f} kg). "
                f"Manual review required."
            )

        return RecommendationResult(
            success=False,
            recommended_box=None,
            bounding_box=bounding_box,
            reason=reason,
            all_candidates=[],
        )


def items_from_order(order) -> list[ItemDimension]:
    """Convert an Order's items into ItemDimension list for the algorithm."""
    result = []
    for item in order.items.select_related("product").all():
        p = item.product
        result.append(ItemDimension(
            length_cm=float(p.length_cm),
            width_cm=float(p.width_cm),
            height_cm=float(p.height_cm),
            weight_kg=float(p.weight_kg),
            quantity=item.quantity,
        ))
    return result
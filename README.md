# BoxWise — Shipping Box Recommendation System


An internal Django tool for the warehouse team: given an order's items, it recommends the cheapest shipping box that the order will physically fit into, based on product dimensions/weight and the available box inventory.

## Problem

Each product has length, width, height, and weight. Each box has internal dimensions, a maximum weight capacity, and a cost. When an order is placed, the warehouse team needs to know which single box to pack it in — the cheapest one that the order actually fits in, both by volume and by weight.

## How recommendation works

The core logic lives in `recommender/service.py`, isolated from Django so it's independently testable.

1. **Bounding box approach.** For all items in an order (expanded by quantity), each unit's dimensions are sorted so its smallest side becomes its "height" when stacked. The bounding box used for fitting is:
   - `length` = max length across all units
   - `width` = max width across all units
   - `height` = sum of all units' heights (stacked)

   This is a conservative, axis-aligned approximation — not true 3D bin-packing — but it never under-estimates the space needed, so a box that's recommended will always physically fit the order.

2. **Filtering.** Boxes are filtered to those that are `is_active`, whose `max_weight_kg` covers the order's total weight, and whose internal dimensions fit the bounding box (tried in all 6 axis-aligned rotations).

3. **Selection.** Among boxes that fit, the cheapest (`cost_pence`) is recommended.

4. **No fit.** If no box satisfies both constraints, the order is flagged `needs_review` with a reason explaining whether it failed on weight, dimensions, or both.

## Features

- Order intake with line items (product + quantity), auto box recommendation on save
- Manual re-run of the recommendation (e.g. after editing an order)
- Order status workflow: `Pending → To Be Packed → Packed → Dispatched → Delivered`, plus `Cancelled` and `Needs Manual Review`, enforced via explicit transition rules — invalid transitions are rejected
- Dashboard grouping live orders by status
- Product and Box CRUD, restricted to Manager-role users
- Two user roles: Warehouse Staff (view/manage orders) and Manager (also manages products/boxes)
- Authentication via Django's built-in auth system

## Tech stack

| Layer | Choice |
|---|---|
| Framework | Django |
| Database | SQLite (local dev and CI) |
| Frontend | Django templates + Tailwind (CDN) |
| Auth | Django built-in auth, custom `User` model with `role` field |
| Tests | pytest + pytest-django + factory_boy |
| CI | GitHub Actions |

## Project structure

```
warehouse/
├── warehouse/            # settings, urls, wsgi
│   ├── settings.py
│   ├── settings_test.py  # test-specific overrides
│   └── urls.py
├── accounts/              # custom User model, login/logout, role mixin
├── products/               # Product model, CRUD views
├── boxes/                  # Box model, CRUD views
├── orders/                 # Order, OrderItem, dashboard, status transitions
├── recommender/             # core recommendation algorithm (pure Python)
├── tests/                    # pytest suite (factories, model, view, algorithm tests)
├── *_/fixtures/                # sample demo data (products, boxes)
└── manage.py
```

## Setup (local, SQLite)

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd warehouse

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

# Optional: seed demo data
python manage.py loaddata boxes/fixtures/boxes/boxes.json   
python manage.py loaddata products/fixtures/products/products.json

python manage.py createsuperuser

python manage.py runserver
```

Visit `http://127.0.0.1:8000`. Log in with the superuser account, or create staff/manager users via `/admin/`.

### Creating a Manager user

By default, new users get the `staff` role. To promote one to `manager` (required for creating/editing Products and Boxes), use the Django admin or shell:

```bash
python manage.py shell -c "
from accounts.models import User
u = User.objects.get(username='your_username')
u.role = User.Role.MANAGER
u.save()
"
```

## Running tests

```bash
pytest
```

This runs against `warehouse.settings_test`, which uses an in-memory SQLite database — no external services required.

For coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

### Sample test run output
 
A full local test run output is checked into the repo: [`test_output.txt`](./test_output.txt)
 
## Continuous Integration
 
Tests run automatically on every push and pull request via GitHub Actions.
 
- **Workflow file:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- **Latest run:** [GitHub Actions](https://github.com/Lavanya-Mtl/warehouse/actions)

CI installs dependencies, applies migrations against an in-memory SQLite database, and runs the full pytest suite with coverage — no external database service is needed since both local dev and CI use SQLite.

## Design notes and trade-offs

- **Bounding-box, not true bin-packing.** True 3D bin-packing (irregular item arrangement, rotation optimization) is NP-hard and overkill for a warehouse tool recommending from a small, fixed box catalog. The bounding-box approach is fast, fully explainable to a human packer, and errs conservative (never recommends a box too small).
- **Single box per order.** The system always recommends one box for the whole order. Multi-box splitting (for very large/heavy orders) is flagged as `Needs Manual Review` rather than auto-split, since splitting logic (which items go in which box) is itself a bin-packing problem worth scoping separately.
- **Cost-first tie-breaking.** Among all boxes that fit, the cheapest is always chosen. This matches the stated goal ("recommends the most suitable box") under the reasonable assumption that "suitable" means cheapest-that-fits in a warehouse cost-control context.

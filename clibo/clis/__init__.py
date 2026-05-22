"""Registry of built clibo tools.

Each tool is a module exposing ``NAME``, ``HELP`` and a Typer ``app``. The
build loop appends new modules to the imports and to ``ALL`` as it ships them.
"""

from clibo.clis import (
    bills,
    budget,
    calorie,
    debt,
    expense,
    invoice,
    meditate,
    meds,
    mood,
    networth,
    period,
    savings,
    sleep,
    subs,
    vitals,
    water,
    weight,
    workout,
)

#: Every built tool module, in catalog order. Extended by the build loop.
ALL = [
    calorie,
    water,
    weight,
    workout,
    sleep,
    mood,
    meds,
    period,
    meditate,
    vitals,
    expense,
    budget,
    subs,
    bills,
    savings,
    debt,
    networth,
    invoice,
]

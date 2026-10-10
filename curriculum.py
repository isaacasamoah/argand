"""The single practice problem and explicitly authored teaching material."""

import sympy as sp

PROBLEMS = [
    {
        "id": "roots-8",
        "title": "Find the missing roots",
        "n": 3,
        "value": 8,
        "latex": "z^3 = 8",
        "level": "Your practice",
    }
]


def hints(p):
    return [
        "Find 8 on the real axis. How far is it from the centre? What angle points towards it? These are its distance and direction.",
        "Cubing a complex number cubes its distance and triples its angle. What starting distance would give 8? What starting angles would end up pointing right?",
        (
            "Pointing right can mean 0°, 360° or 720°. Divide each angle by 3 to find the starting "
            "directions. For each direction, use a = r cos(θ) and b = r sin(θ), where r is the "
            "starting distance. Write the result as a + bi."
        ),
    ]


def solution(p):
    roots = sp.solve(sp.Symbol("z") ** p["n"] - p["value"], sp.Symbol("z"))
    return (
        "The roots are "
        + ", ".join(str(x).replace("I", "i") for x in roots)
        + f". Each satisfies the equation, and a degree-{p['n']} polynomial has at most {p['n']} distinct roots. This is a worked solution, not independent completion."
    )

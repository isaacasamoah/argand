"""Restricted expression parsing and exact root verification; no model calls."""

import ast
import re

import sympy as sp


def expression(text):
    text = text.strip().replace("−", "-").replace("√", "sqrt").replace("^", "**")
    text = re.sub(r"sqrt(\d+)", r"sqrt(\1)", text)
    text = re.sub(r"(\d|\))\s*(?=i\b|sqrt\()", r"\1*", text)
    text = re.sub(r"\bi\s*(?=sqrt\(|\d|\()", "i*", text)
    text = re.sub(r"\)\s*(?=\()", ")*", text)
    if len(text) > 100:
        raise ValueError("Expression too long")
    tree = ast.parse(text, mode="eval")
    if len(list(ast.walk(tree))) > 40:
        raise ValueError("Expression too complex")

    def walk(t):
        if (
            isinstance(t, ast.Constant)
            and type(t.value) is int
            and abs(t.value) <= 10000
        ):
            return sp.Integer(t.value)
        if isinstance(t, ast.Name) and t.id == "i":
            return sp.I
        if isinstance(t, ast.UnaryOp) and isinstance(t.op, (ast.UAdd, ast.USub)):
            return walk(t.operand) * (-1 if isinstance(t.op, ast.USub) else 1)
        if (
            isinstance(t, ast.Call)
            and isinstance(t.func, ast.Name)
            and t.func.id == "sqrt"
            and len(t.args) == 1
            and not t.keywords
        ):
            v = walk(t.args[0])
            if v.is_Integer and 0 <= v <= 10000:
                return sp.sqrt(v)
        if isinstance(t, ast.BinOp):
            a, b = walk(t.left), walk(t.right)
            if isinstance(t.op, ast.Add):
                return a + b
            if isinstance(t.op, ast.Sub):
                return a - b
            if isinstance(t.op, ast.Mult):
                return a * b
            if isinstance(t.op, ast.Div) and b != 0:
                return a / b
            if (
                isinstance(t.op, ast.Pow)
                and b.is_Integer
                and abs(b) <= 6
                and not (a == 0 and b < 0)
            ):
                return a**b
        raise ValueError("Use integers, fractions, i and sqrt(number)")

    return sp.simplify(walk(tree.body))


def check(problem, text):
    try:
        bits = (
            text.strip()
            .removeprefix("z =")
            .removeprefix("z=")
            .strip()
            .strip("{}")
            .split(",")
        )
        if not 1 <= len(bits) <= 8:
            raise ValueError("Enter up to eight comma-separated roots")
        values = [expression(x) for x in bits]
    except (ValueError, SyntaxError, TypeError, RecursionError):
        return {
            "status": "not_checked",
            "detail": "I can check comma-separated exact roots using integers, fractions, i and sqrt(number). Other working is not checked yet.",
            "valid": [],
            "points": [],
        }
    valid = [sp.simplify(v ** problem["n"] - problem["value"]) == 0 for v in values]
    unique = set(values)
    status = (
        "incorrect"
        if not all(valid)
        else ("complete" if len(unique) == problem["n"] else "incomplete")
    )
    return {
        "status": status,
        "detail": {
            "incorrect": "These submitted values do not satisfy the equation: "
            + ", ".join(bits[i].strip() for i, ok in enumerate(valid) if not ok)
            + ".",
            "complete": "All distinct roots are present. The explanation still needs review.",
            "incomplete": "These roots work, but the set is not complete.",
        }[status],
        "valid": valid,
        "distinct": len(unique),
        "duplicates": len(unique) < len(values),
        "roots": list(
            dict.fromkeys(
                str(v).replace("I", "i") for v, ok in zip(values, valid) if ok
            )
        ),
        "points": [
            [float(sp.re(v)), float(sp.im(v))] for v, ok in zip(values, valid) if ok
        ],
    }

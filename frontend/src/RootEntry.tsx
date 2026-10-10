import { useEffect, useRef, useState, type ReactNode } from "react";
import { MathfieldElement } from "mathlive";
MathfieldElement.fontsDirectory = "/mathlive-fonts";
MathfieldElement.soundsDirectory = null;
export function RootEntry({
  onCheck,
  busy,
  children,
}: {
  onCheck: (value: string) => Promise<boolean>;
  busy: boolean;
  children: ReactNode;
}) {
  const host = useRef<HTMLDivElement>(null),
    field = useRef<MathfieldElement | null>(null),
    [empty, setEmpty] = useState(true);
  useEffect(() => {
    const input = new MathfieldElement();
    input.id = "root-entry";
    input.setAttribute("aria-label", "One root");
    input.mathVirtualKeyboardPolicy = "manual";
    input.addEventListener("input", () => setEmpty(!input.value.trim()));
    host.current!.append(input);
    input.menuItems = [];
    input.addEventListener("click", () =>
      input.shadowRoot
        ?.querySelector<HTMLElement>("[part=keyboard-sink]")
        ?.focus(),
    );
    input.addEventListener("focusin", () =>
      queueMicrotask(() => {
        if (
          document.activeElement === input &&
          !input.shadowRoot?.activeElement
        )
          input.shadowRoot
            ?.querySelector<HTMLElement>("[part=keyboard-sink]")
            ?.focus();
      }),
    );
    field.current = input;
    return () => {
      input.remove();
      field.current = null;
    };
  }, []);
  useEffect(() => {
    if (field.current) field.current.readOnly = busy;
  }, [busy]);
  function insert(value: string) {
    field.current?.insert(value);
    field.current?.shadowRoot
      ?.querySelector<HTMLElement>("[part=keyboard-sink]")
      ?.focus();
    setEmpty(!field.current?.value.trim());
  }
  async function submit() {
    const input = field.current;
    if (!input || busy || !input.value.trim()) return;
    const value = input.getValue("ascii-math");
    if (await onCheck(value)) {
      input.value = "";
      setEmpty(true);
      input.shadowRoot
        ?.querySelector<HTMLElement>("[part=keyboard-sink]")
        ?.focus();
    }
  }
  const keys = [
    ["i", "i", "Imaginary unit"],
    ["√", "\\sqrt{#0}", "Square root"],
    ["−", "-", "Minus"],
    ["+", "+", "Plus"],
    ["a/b", "\\frac{#0}{#?}", "Fraction"],
    ["xⁿ", "^{#0}", "Power"],
    ["( )", "\\left(#0\\right)", "Parentheses"],
  ];
  return (
    <form
      className="practice-answer"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <label htmlFor="root-entry">Try one root</label>
      <div className="answer-row">
        <div className="math-entry" ref={host} />
        <button className="primary" type="submit" disabled={busy || empty}>
          Check this root
        </button>
      </div>
      <div className="answer-support">
        <div className="math-keypad" role="group" aria-label="Maths symbols">
          {keys.map(([label, value, name]) => (
            <button
              key={name}
              type="button"
              title={name}
              aria-label={name}
              disabled={busy}
              onClick={() => insert(value)}
            >
              {label}
            </button>
          ))}
        </div>
        {children}
      </div>
    </form>
  );
}

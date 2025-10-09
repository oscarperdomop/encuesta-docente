// src/components/LikertSelect.tsx
type Props = {
  value: number | "";
  onChange: (v: number | "") => void;
  disabled?: boolean;
};

export default function LikertSelect({ value, onChange, disabled }: Props) {
  return (
    <select
      className="border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-usco-primary/30"
      value={value === "" ? "" : String(value)}
      onChange={(e) => {
        const v = e.target.value;
        onChange(v === "" ? "" : Number(v));
      }}
      disabled={disabled}
    >
      <option value="">Seleccionar</option>
      <option value="1">1 — Muy en desacuerdo</option>
      <option value="2">2 — En desacuerdo</option>
      <option value="3">3 — Ni de acuerdo ni en desacuerdo</option>
      <option value="4">4 — De acuerdo</option>
      <option value="5">5 — Muy de acuerdo</option>
    </select>
  );
}

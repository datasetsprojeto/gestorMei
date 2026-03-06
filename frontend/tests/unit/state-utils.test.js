import { describe, expect, it } from "vitest";
import { formatCurrency, formatDateKeyBusiness } from "../../js/state.js";

describe("state utils", () => {
  it("formats currency in pt-BR", () => {
    expect(formatCurrency(1234.56)).toContain("1.234,56");
  });

  it("formats business date key as YYYY-MM-DD", () => {
    const key = formatDateKeyBusiness(new Date("2026-03-06T14:10:00Z"));
    expect(key).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

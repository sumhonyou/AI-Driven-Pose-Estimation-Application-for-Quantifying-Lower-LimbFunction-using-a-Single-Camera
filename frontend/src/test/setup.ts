import "@testing-library/jest-dom/vitest";

// jsdom has no IntersectionObserver; useReveal.ts (scroll-reveal animation)
// only needs a no-op stand-in for it to run without throwing in tests.
class IntersectionObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
// @ts-expect-error -- test-only stub, not a full IntersectionObserver implementation
globalThis.IntersectionObserver = IntersectionObserverStub;

// jsdom also has no ResizeObserver; recharts' <ResponsiveContainer> (Stage R11's
// SubScoreBarChart) checks for it and no-ops gracefully if missing, but a stub
// keeps it from silently rendering 0x0 and lets its own resize logic run.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
// @ts-expect-error -- test-only stub, not a full ResizeObserver implementation
globalThis.ResizeObserver = ResizeObserverStub;

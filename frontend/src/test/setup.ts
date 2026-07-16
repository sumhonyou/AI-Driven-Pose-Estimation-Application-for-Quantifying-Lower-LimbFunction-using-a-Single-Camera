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

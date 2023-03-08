Object.defineProperty(window, "location", {
  writable: true,
  value: { replace: jest.fn() },
});

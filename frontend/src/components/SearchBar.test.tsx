import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SearchBar } from "@/components/SearchBar";

beforeEach(() => {
  vi.resetAllMocks();
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("SearchBar", () => {
  it("renders search input", () => {
    globalThis.fetch = vi.fn();
    render(<SearchBar boardId={1} />);
    expect(screen.getByPlaceholderText("Search cards...")).toBeInTheDocument();
  });

  it("shows results after typing", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          results: [
            { id: "card-1", title: "Found card", details: "detail", due_date: null, column_id: "col-1", column_title: "Backlog" },
          ],
        }),
    });

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<SearchBar boardId={1} />);

    await user.type(screen.getByPlaceholderText("Search cards..."), "Found");
    vi.advanceTimersByTime(350);

    await waitFor(() => {
      expect(screen.getByText("Found card")).toBeInTheDocument();
      expect(screen.getByText("Backlog")).toBeInTheDocument();
    });
  });

  it("shows no results message", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ results: [] }),
    });

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<SearchBar boardId={1} />);

    await user.type(screen.getByPlaceholderText("Search cards..."), "zzzzz");
    vi.advanceTimersByTime(350);

    await waitFor(() => {
      expect(screen.getByText("No cards found")).toBeInTheDocument();
    });
  });

  it("does not fetch on empty input", async () => {
    globalThis.fetch = vi.fn();
    render(<SearchBar boardId={1} />);
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });
});

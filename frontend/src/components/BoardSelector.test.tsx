import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BoardSelector } from "@/components/BoardSelector";

const mockBoards = [
  { id: 1, title: "Sprint 1", created_at: "2026-01-01T00:00:00" },
  { id: 2, title: "Backlog", created_at: "2026-02-01T00:00:00" },
];

const onSelectBoard = vi.fn();
const onLogout = vi.fn();
const onAuthError = vi.fn();

beforeEach(() => {
  vi.resetAllMocks();
  globalThis.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
    if (url === "/api/boards" && (!options || options.method === undefined || options.method === "GET")) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ boards: mockBoards }),
      });
    }
    if (url === "/api/boards" && options?.method === "POST") {
      const body = JSON.parse(options.body as string);
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: 99, title: body.title }),
      });
    }
    if (typeof url === "string" && url.match(/\/api\/boards\/\d+$/) && options?.method === "DELETE") {
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ ok: true }) });
    }
    if (typeof url === "string" && url.match(/\/api\/boards\/\d+$/) && options?.method === "PUT") {
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ ok: true }) });
    }
    if (typeof url === "string" && url.match(/\/api\/boards\/\d+\/stats$/)) {
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ total_cards: 3, member_count: 1, columns: [] }) });
    }
    if (url === "/api/auth/me") {
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ username: "user", display_name: "User" }) });
    }
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
  });
});

describe("BoardSelector", () => {
  it("renders board list from API", async () => {
    render(<BoardSelector onSelectBoard={onSelectBoard} onLogout={onLogout} onAuthError={onAuthError} />);
    await waitFor(() => {
      expect(screen.getByText("Sprint 1")).toBeInTheDocument();
      expect(screen.getByText("Backlog")).toBeInTheDocument();
    });
  });

  it("opens a board when Open button is clicked", async () => {
    render(<BoardSelector onSelectBoard={onSelectBoard} onLogout={onLogout} onAuthError={onAuthError} />);
    await waitFor(() => expect(screen.getByText("Sprint 1")).toBeInTheDocument());

    const openButtons = screen.getAllByRole("button", { name: /open/i });
    await userEvent.click(openButtons[0]);
    expect(onSelectBoard).toHaveBeenCalledWith(1);
  });

  it("opens a board when board title is clicked", async () => {
    render(<BoardSelector onSelectBoard={onSelectBoard} onLogout={onLogout} onAuthError={onAuthError} />);
    await waitFor(() => expect(screen.getByText("Sprint 1")).toBeInTheDocument());

    await userEvent.click(screen.getByText("Sprint 1"));
    expect(onSelectBoard).toHaveBeenCalledWith(1);
  });

  it("creates a new board", async () => {
    render(<BoardSelector onSelectBoard={onSelectBoard} onLogout={onLogout} onAuthError={onAuthError} />);
    await waitFor(() => expect(screen.getByText("Sprint 1")).toBeInTheDocument());

    const input = screen.getByPlaceholderText(/new board name/i);
    await userEvent.type(input, "New Project");
    await userEvent.click(screen.getByRole("button", { name: /create board/i }));

    await waitFor(() => {
      expect(screen.getByText("New Project")).toBeInTheDocument();
    });
  });

  it("deletes a board", async () => {
    render(<BoardSelector onSelectBoard={onSelectBoard} onLogout={onLogout} onAuthError={onAuthError} />);
    await waitFor(() => expect(screen.getByText("Sprint 1")).toBeInTheDocument());

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    await userEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.queryByText("Sprint 1")).not.toBeInTheDocument();
    });
  });

  it("calls onLogout when sign out is clicked", async () => {
    render(<BoardSelector onSelectBoard={onSelectBoard} onLogout={onLogout} onAuthError={onAuthError} />);
    await waitFor(() => expect(screen.getByText("Sprint 1")).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /sign out/i }));
    expect(onLogout).toHaveBeenCalled();
  });
});

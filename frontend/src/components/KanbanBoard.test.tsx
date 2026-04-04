import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";

const mockBoardResponse = {
  columns: [
    { id: "col-1", title: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "col-2", title: "Discovery", cardIds: ["card-3"] },
    { id: "col-3", title: "In Progress", cardIds: ["card-4", "card-5"] },
    { id: "col-4", title: "Review", cardIds: ["card-6"] },
    { id: "col-5", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": { id: "card-1", title: "Align roadmap themes", details: "Draft quarterly themes.", due_date: null, priority: "none", labels: [], comment_count: 0, checklist_total: 0, checklist_done: 0, assignees: [] },
    "card-2": { id: "card-2", title: "Gather customer signals", details: "Review support tags.", due_date: null, priority: "none", labels: [], comment_count: 0, checklist_total: 0, checklist_done: 0, assignees: [] },
    "card-3": { id: "card-3", title: "Prototype analytics view", details: "Sketch initial dashboard.", due_date: null, priority: "none", labels: [], comment_count: 0, checklist_total: 0, checklist_done: 0, assignees: [] },
    "card-4": { id: "card-4", title: "Refine status language", details: "Standardize labels.", due_date: null, priority: "none", labels: [], comment_count: 0, checklist_total: 0, checklist_done: 0, assignees: [] },
    "card-5": { id: "card-5", title: "Design card layout", details: "Add hierarchy.", due_date: null, priority: "none", labels: [], comment_count: 0, checklist_total: 0, checklist_done: 0, assignees: [] },
    "card-6": { id: "card-6", title: "QA micro-interactions", details: "Verify states.", due_date: null, priority: "none", labels: [], comment_count: 0, checklist_total: 0, checklist_done: 0, assignees: [] },
    "card-7": { id: "card-7", title: "Ship marketing page", details: "Final copy.", due_date: null, priority: "none", labels: [], comment_count: 0, checklist_total: 0, checklist_done: 0, assignees: [] },
    "card-8": { id: "card-8", title: "Close onboarding sprint", details: "Document notes.", due_date: null, priority: "none", labels: [], comment_count: 0, checklist_total: 0, checklist_done: 0, assignees: [] },
  },
  labels: [],
};

let cardIdCounter = 100;

beforeEach(() => {
  cardIdCounter = 100;
  globalThis.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
    if (url === "/api/board") {
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(mockBoardResponse) });
    }
    if (url === "/api/cards" && options?.method === "POST") {
      const body = JSON.parse(options.body as string);
      const id = String(++cardIdCounter);
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id, title: body.title, details: body.details || "", due_date: null }),
      });
    }
    // Default: success for PUT/DELETE
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ ok: true }) });
  });
});

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

describe("KanbanBoard", () => {
  it("renders five columns from API", async () => {
    render(<KanbanBoard />);
    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    await waitFor(() => expect(screen.getAllByTestId(/column-/i)).toHaveLength(5));
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    await waitFor(() => expect(screen.getAllByTestId(/column-/i)).toHaveLength(5));
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", { name: /add a card/i });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    await waitFor(() => {
      expect(within(column).getByText("New card")).toBeInTheDocument();
    });

    const deleteButton = within(column).getByRole("button", { name: /delete new card/i });
    await userEvent.click(deleteButton);

    await waitFor(() => {
      expect(within(column).queryByText("New card")).not.toBeInTheDocument();
    });
  });
});

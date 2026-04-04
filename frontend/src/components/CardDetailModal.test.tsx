import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CardDetailModal } from "@/components/CardDetailModal";
import type { Card, Label } from "@/lib/kanban";

// Mock HTMLDialogElement since jsdom doesn't support it
beforeAll(() => {
  HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) {
    this.setAttribute("open", "");
  });
  HTMLDialogElement.prototype.close = vi.fn(function (this: HTMLDialogElement) {
    this.removeAttribute("open");
  });
});

const mockCard: Card = {
  id: "card-1",
  title: "Test Card",
  details: "Some details",
  due_date: null,
  priority: "none",
  labels: [],
  comment_count: 0,
  checklist_total: 0,
  checklist_done: 0,
  assignees: [],
};

const mockLabels: Label[] = [
  { id: 1, name: "Bug", color: "#ef4444" },
  { id: 2, name: "Feature", color: "#3b82f6" },
];

const onClose = vi.fn();
const onUpdate = vi.fn();

beforeEach(() => {
  vi.resetAllMocks();
  HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) {
    this.setAttribute("open", "");
  });
  globalThis.fetch = vi.fn().mockImplementation((url: string) => {
    if (typeof url === "string" && url.includes("/checklist")) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ items: [] }),
      });
    }
    if (typeof url === "string" && url.includes("/comments")) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ comments: [] }),
      });
    }
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ ok: true }),
    });
  });
});

describe("CardDetailModal", () => {
  it("renders card data in form fields", () => {
    render(
      <CardDetailModal card={mockCard} boardLabels={mockLabels} boardMembers={[]} onClose={onClose} onUpdate={onUpdate} />
    );
    expect(screen.getByDisplayValue("Test Card")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Some details")).toBeInTheDocument();
  });

  it("calls onClose when Cancel is clicked", async () => {
    render(
      <CardDetailModal card={mockCard} boardLabels={mockLabels} boardMembers={[]} onClose={onClose} onUpdate={onUpdate} />
    );
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("saves updated card data", async () => {
    render(
      <CardDetailModal card={mockCard} boardLabels={[]} boardMembers={[]} onClose={onClose} onUpdate={onUpdate} />
    );

    const titleInput = screen.getByDisplayValue("Test Card");
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, "Updated Title");
    await userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalledWith(
        expect.objectContaining({ title: "Updated Title" })
      );
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("renders label toggle buttons", () => {
    render(
      <CardDetailModal card={mockCard} boardLabels={mockLabels} boardMembers={[]} onClose={onClose} onUpdate={onUpdate} />
    );
    expect(screen.getByRole("button", { name: "Bug" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Feature" })).toBeInTheDocument();
  });

  it("toggles a label on a card", async () => {
    render(
      <CardDetailModal card={mockCard} boardLabels={mockLabels} boardMembers={[]} onClose={onClose} onUpdate={onUpdate} />
    );

    await userEvent.click(screen.getByRole("button", { name: "Bug" }));

    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalledWith(
        expect.objectContaining({
          labels: [{ id: 1, name: "Bug", color: "#ef4444" }],
        })
      );
    });
  });
});

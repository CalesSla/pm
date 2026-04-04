import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LabelManager } from "@/components/LabelManager";
import type { Label } from "@/lib/kanban";

const mockLabels: Label[] = [
  { id: 1, name: "Bug", color: "#ef4444" },
  { id: 2, name: "Feature", color: "#3b82f6" },
];

const onLabelsChange = vi.fn();
const onClose = vi.fn();

beforeEach(() => {
  vi.resetAllMocks();
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve({ id: 3, name: "New Label", color: "#3b82f6" }),
  });
});

describe("LabelManager", () => {
  it("renders existing labels", () => {
    render(
      <LabelManager boardId={1} labels={mockLabels} onLabelsChange={onLabelsChange} onClose={onClose} />
    );
    expect(screen.getByText("Bug")).toBeInTheDocument();
    expect(screen.getByText("Feature")).toBeInTheDocument();
  });

  it("creates a new label", async () => {
    render(
      <LabelManager boardId={1} labels={mockLabels} onLabelsChange={onLabelsChange} onClose={onClose} />
    );

    await userEvent.type(screen.getByPlaceholderText("Label name..."), "New Label");
    await userEvent.click(screen.getByRole("button", { name: /add/i }));

    await waitFor(() => {
      expect(onLabelsChange).toHaveBeenCalledWith([
        ...mockLabels,
        { id: 3, name: "New Label", color: "#3b82f6" },
      ]);
    });
  });

  it("deletes a label", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ ok: true }),
    });

    render(
      <LabelManager boardId={1} labels={mockLabels} onLabelsChange={onLabelsChange} onClose={onClose} />
    );

    const deleteButtons = screen.getAllByText("Delete");
    await userEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(onLabelsChange).toHaveBeenCalledWith([mockLabels[1]]);
    });
  });

  it("calls onClose when Done is clicked", async () => {
    render(
      <LabelManager boardId={1} labels={mockLabels} onLabelsChange={onLabelsChange} onClose={onClose} />
    );
    await userEvent.click(screen.getByRole("button", { name: /done/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("shows edit mode when Edit is clicked", async () => {
    render(
      <LabelManager boardId={1} labels={mockLabels} onLabelsChange={onLabelsChange} onClose={onClose} />
    );
    const editButtons = screen.getAllByText("Edit");
    await userEvent.click(editButtons[0]);
    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
  });
});

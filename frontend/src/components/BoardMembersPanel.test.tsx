import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BoardMembersPanel } from "@/components/BoardMembersPanel";
import type { BoardMember } from "@/lib/kanban";

const mockMembers: BoardMember[] = [
  { id: 1, username: "owner", display_name: "Owner User", role: "owner" },
  { id: 2, username: "alice", display_name: "Alice", role: "member" },
];

const onMembersChange = vi.fn();
const onClose = vi.fn();

beforeEach(() => {
  vi.resetAllMocks();
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve({ id: 3, username: "bob", display_name: "Bob", role: "member" }),
  });
});

describe("BoardMembersPanel", () => {
  it("renders existing members", () => {
    render(
      <BoardMembersPanel boardId={1} members={mockMembers} onMembersChange={onMembersChange} onClose={onClose} />
    );
    expect(screen.getByText("Owner User")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
  });

  it("owner does not have remove button", () => {
    render(
      <BoardMembersPanel boardId={1} members={mockMembers} onMembersChange={onMembersChange} onClose={onClose} />
    );
    const removeButtons = screen.getAllByText("Remove");
    expect(removeButtons).toHaveLength(1); // Only alice has remove
  });

  it("invites a new member", async () => {
    render(
      <BoardMembersPanel boardId={1} members={mockMembers} onMembersChange={onMembersChange} onClose={onClose} />
    );

    await userEvent.type(screen.getByPlaceholderText("Username..."), "bob");
    await userEvent.click(screen.getByRole("button", { name: /invite/i }));

    await waitFor(() => {
      expect(onMembersChange).toHaveBeenCalledWith([
        ...mockMembers,
        { id: 3, username: "bob", display_name: "Bob", role: "member" },
      ]);
    });
  });

  it("removes a member", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ ok: true }),
    });

    render(
      <BoardMembersPanel boardId={1} members={mockMembers} onMembersChange={onMembersChange} onClose={onClose} />
    );

    await userEvent.click(screen.getByText("Remove"));

    await waitFor(() => {
      expect(onMembersChange).toHaveBeenCalledWith([mockMembers[0]]); // Only owner remains
    });
  });

  it("calls onClose when Done is clicked", async () => {
    render(
      <BoardMembersPanel boardId={1} members={mockMembers} onMembersChange={onMembersChange} onClose={onClose} />
    );
    await userEvent.click(screen.getByRole("button", { name: /done/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("shows error on failed invite", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      text: () => Promise.resolve('{"error":"User not found"}'),
    });

    render(
      <BoardMembersPanel boardId={1} members={mockMembers} onMembersChange={onMembersChange} onClose={onClose} />
    );

    await userEvent.type(screen.getByPlaceholderText("Username..."), "ghost");
    await userEvent.click(screen.getByRole("button", { name: /invite/i }));

    await waitFor(() => {
      expect(screen.getByText("User not found")).toBeInTheDocument();
    });
  });
});

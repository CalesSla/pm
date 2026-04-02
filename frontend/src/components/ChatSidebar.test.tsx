import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatSidebar } from "@/components/ChatSidebar";
import * as api from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual("@/lib/api");
  return { ...actual, sendChatMessage: vi.fn() };
});

const mockSend = vi.mocked(api.sendChatMessage);

const mockBoard = {
  columns: [{ id: "col-1", title: "Backlog", cardIds: [] }],
  cards: {},
};

describe("ChatSidebar", () => {
  const onBoardUpdate = vi.fn();
  const onAuthError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows toggle button when closed", () => {
    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);
    expect(screen.getByLabelText("Open AI chat")).toBeInTheDocument();
  });

  it("opens sidebar on toggle click", async () => {
    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);
    await userEvent.click(screen.getByLabelText("Open AI chat"));
    expect(screen.getByText("AI Assistant")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Ask the AI...")).toBeInTheDocument();
  });

  it("closes sidebar on close click", async () => {
    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);
    await userEvent.click(screen.getByLabelText("Open AI chat"));
    expect(screen.getByText("AI Assistant")).toBeInTheDocument();
    await userEvent.click(screen.getByLabelText("Close chat"));
    expect(screen.queryByText("AI Assistant")).not.toBeInTheDocument();
  });

  it("sends a message and displays response", async () => {
    mockSend.mockResolvedValueOnce({
      message: "Done! Created the card.",
      actions: [],
      action_results: [],
      board: mockBoard,
    });

    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);
    await userEvent.click(screen.getByLabelText("Open AI chat"));

    const input = screen.getByPlaceholderText("Ask the AI...");
    await userEvent.type(input, "hello");
    await userEvent.click(screen.getByLabelText("Send message"));

    expect(screen.getByText("hello")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Done! Created the card.")).toBeInTheDocument();
    });
  });

  it("calls onBoardUpdate when actions are returned", async () => {
    mockSend.mockResolvedValueOnce({
      message: "Created a card.",
      actions: [{ type: "create_card" }],
      action_results: [{ ok: true }],
      board: mockBoard,
    });

    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);
    await userEvent.click(screen.getByLabelText("Open AI chat"));

    await userEvent.type(screen.getByPlaceholderText("Ask the AI..."), "create a card");
    await userEvent.click(screen.getByLabelText("Send message"));

    await waitFor(() => {
      expect(onBoardUpdate).toHaveBeenCalledWith(mockBoard);
    });
  });

  it("does not call onBoardUpdate when no actions", async () => {
    mockSend.mockResolvedValueOnce({
      message: "Just chatting.",
      actions: [],
      action_results: [],
      board: mockBoard,
    });

    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);
    await userEvent.click(screen.getByLabelText("Open AI chat"));

    await userEvent.type(screen.getByPlaceholderText("Ask the AI..."), "hi");
    await userEvent.click(screen.getByLabelText("Send message"));

    await waitFor(() => {
      expect(screen.getByText("Just chatting.")).toBeInTheDocument();
    });
    expect(onBoardUpdate).not.toHaveBeenCalled();
  });

  it("shows error message on failure", async () => {
    mockSend.mockRejectedValueOnce(new Error("Network error"));

    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);
    await userEvent.click(screen.getByLabelText("Open AI chat"));

    await userEvent.type(screen.getByPlaceholderText("Ask the AI..."), "test");
    await userEvent.click(screen.getByLabelText("Send message"));

    await waitFor(() => {
      expect(screen.getByText("Something went wrong. Please try again.")).toBeInTheDocument();
    });
  });

  it("calls onAuthError on 401", async () => {
    mockSend.mockRejectedValueOnce(new api.AuthError());

    render(<ChatSidebar onBoardUpdate={onBoardUpdate} onAuthError={onAuthError} />);
    await userEvent.click(screen.getByLabelText("Open AI chat"));

    await userEvent.type(screen.getByPlaceholderText("Ask the AI..."), "test");
    await userEvent.click(screen.getByLabelText("Send message"));

    await waitFor(() => {
      expect(onAuthError).toHaveBeenCalled();
    });
  });

  it("sends via Enter key", async () => {
    mockSend.mockResolvedValueOnce({
      message: "Got it.",
      actions: [],
      action_results: [],
      board: mockBoard,
    });

    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);
    await userEvent.click(screen.getByLabelText("Open AI chat"));

    await userEvent.type(screen.getByPlaceholderText("Ask the AI..."), "hi{Enter}");

    await waitFor(() => {
      expect(screen.getByText("Got it.")).toBeInTheDocument();
    });
  });

  it("disables send button when input is empty", async () => {
    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);
    await userEvent.click(screen.getByLabelText("Open AI chat"));

    expect(screen.getByLabelText("Send message")).toBeDisabled();
  });
});

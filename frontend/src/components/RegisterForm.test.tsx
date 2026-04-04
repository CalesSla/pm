import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RegisterForm } from "@/components/RegisterForm";

const onRegister = vi.fn();
const onSwitchToLogin = vi.fn();

beforeEach(() => {
  vi.resetAllMocks();
});

describe("RegisterForm", () => {
  it("renders the registration form", () => {
    render(<RegisterForm onRegister={onRegister} onSwitchToLogin={onSwitchToLogin} />);
    expect(screen.getByRole("heading", { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
  });

  it("calls onRegister on successful registration", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ username: "newuser", display_name: "newuser" }),
    });

    render(<RegisterForm onRegister={onRegister} onSwitchToLogin={onSwitchToLogin} />);

    await userEvent.type(screen.getByLabelText(/username/i), "newuser");
    await userEvent.type(screen.getByLabelText(/password/i), "secret");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(onRegister).toHaveBeenCalled();
    });
  });

  it("shows error on failed registration", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      text: () => Promise.resolve('{"error":"Username already taken"}'),
    });

    render(<RegisterForm onRegister={onRegister} onSwitchToLogin={onSwitchToLogin} />);

    await userEvent.type(screen.getByLabelText(/username/i), "taken");
    await userEvent.type(screen.getByLabelText(/password/i), "secret");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Username already taken");
    });
  });

  it("switches to login form", async () => {
    render(<RegisterForm onRegister={onRegister} onSwitchToLogin={onSwitchToLogin} />);
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(onSwitchToLogin).toHaveBeenCalled();
  });
});

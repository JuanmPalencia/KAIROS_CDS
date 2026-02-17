import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Login from "../pages/Login";
import { AuthProvider } from "../context/AuthContext";

// Mock fetch globally
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

function renderLogin() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <Login />
      </AuthProvider>
    </MemoryRouter>
  );
}

describe("Login Page", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    localStorage.clear();
  });

  it("renders username and password fields", () => {
    renderLogin();
    expect(screen.getByLabelText(/usuario/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument();
  });

  it("renders the login button", () => {
    renderLogin();
    const btn = screen.getByRole("button", { name: /ingresar/i });
    expect(btn).toBeInTheDocument();
  });

  it("toggles password visibility", () => {
    renderLogin();
    const passwordInput = screen.getByLabelText(/contraseña/i);
    expect(passwordInput.type).toBe("password");

    const toggleBtn = document.querySelector(".password-toggle");
    expect(toggleBtn).toBeTruthy();
    fireEvent.click(toggleBtn);
    expect(passwordInput.type).toBe("text");
  });

  it("shows error on failed login", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Incorrect username or password" }),
    });

    renderLogin();
    const usernameInput = screen.getByLabelText(/usuario/i);
    const passwordInput = screen.getByLabelText(/contraseña/i);
    const submitBtn = screen.getByRole("button", { name: /ingresar/i });

    fireEvent.change(usernameInput, { target: { value: "wrong" } });
    fireEvent.change(passwordInput, { target: { value: "wrong" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    expect(screen.getByText(/usuario o contraseña incorrectos/i)).toBeInTheDocument();
  });
});

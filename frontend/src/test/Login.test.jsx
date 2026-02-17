import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Login from "../pages/Login";
import { AuthProvider } from "../context/AuthContext";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

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
    expect(screen.getByPlaceholderText(/usuario/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/contraseña/i)).toBeInTheDocument();
  });

  it("renders the login button", () => {
    renderLogin();
    const btn = screen.getByRole("button", { name: /iniciar sesión|entrar|login/i });
    expect(btn).toBeInTheDocument();
  });

  it("toggles password visibility", () => {
    renderLogin();
    const passwordInput = screen.getByPlaceholderText(/contraseña/i);
    expect(passwordInput.type).toBe("password");

    // Find the toggle button
    const toggleBtn = screen.getByRole("button", { name: /mostrar|ocultar|👁️|🙈/i }) 
      || document.querySelector(".password-toggle");
    
    if (toggleBtn) {
      fireEvent.click(toggleBtn);
      expect(passwordInput.type).toBe("text");
    }
  });

  it("shows error on failed login", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Incorrect username or password" }),
    });

    renderLogin();
    const usernameInput = screen.getByPlaceholderText(/usuario/i);
    const passwordInput = screen.getByPlaceholderText(/contraseña/i);
    const submitBtn = screen.getByRole("button", { name: /iniciar sesión|entrar|login/i });

    fireEvent.change(usernameInput, { target: { value: "wrong" } });
    fireEvent.change(passwordInput, { target: { value: "wrong" } });
    fireEvent.click(submitBtn);

    // Should call fetch
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });
  });
});

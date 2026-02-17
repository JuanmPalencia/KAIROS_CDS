import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../App";

// Mock leaflet to avoid canvas errors in jsdom
vi.mock("leaflet", () => {
  const L = {
    map: () => ({
      setView: () => L.map(),
      invalidateSize: () => {},
      remove: () => {},
      removeLayer: () => {},
    }),
    tileLayer: () => ({ addTo: () => {} }),
    layerGroup: () => ({
      addTo: () => {},
      removeLayer: () => {},
    }),
    marker: () => ({
      addTo: () => L.marker(),
      bindPopup: () => L.marker(),
      setLatLng: () => {},
      setPopupContent: () => {},
    }),
    circleMarker: () => ({
      addTo: () => L.circleMarker(),
      bindPopup: () => L.circleMarker(),
      setLatLng: () => {},
      setStyle: () => {},
      setPopupContent: () => {},
    }),
    polyline: () => ({
      addTo: () => L.polyline(),
      setStyle: () => {},
    }),
    heatLayer: () => ({
      addTo: () => {},
    }),
    divIcon: () => ({}),
    Icon: {
      Default: {
        prototype: { _getIconUrl: "" },
        mergeOptions: () => {},
      },
    },
  };
  return { default: L, ...L };
});

vi.mock("leaflet.heat", () => ({}));

describe("App", () => {
  it("renders login page when not authenticated", () => {
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <App />
      </MemoryRouter>
    );
    // The login page should show a form
    expect(document.querySelector("form") || document.querySelector("input")).toBeTruthy();
  });

  it("redirects to login when accessing protected route", () => {
    // Clear any stored tokens
    localStorage.removeItem("token");
    
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );
    
    // Should not show dashboard content without auth
    expect(screen.queryByText("Control Central")).toBeNull();
  });
});

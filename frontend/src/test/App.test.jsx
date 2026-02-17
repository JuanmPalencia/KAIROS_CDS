import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
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
  it("renders login page when not authenticated", async () => {
    localStorage.removeItem("token");
    window.history.pushState({}, "", "/login");

    render(
      <App />
    );

    expect(await screen.findByRole("button", { name: /ingresar/i })).toBeInTheDocument();
  });

  it("redirects to login when accessing protected route", async () => {
    localStorage.removeItem("token");
    window.history.pushState({}, "", "/");

    render(
      <App />
    );

    expect(await screen.findByRole("button", { name: /ingresar/i })).toBeInTheDocument();
  });
});

import { cleanup, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { Route, useParams } from "react-router-dom";

import {
  TabRoutes,
  pathJoinWithTrailingSlash,
} from "experimenter-rapid/components/forms/TabRoutes";

import { renderWithRouter } from "./utils";

const TestTabFoo = () => <div>Test Tab Foo</div>;
const TestTabBar = () => <div>Test Tab Bar</div>;
const TEST_CONFIG = [
  {
    path: "",
    label: "Foo Label",
    component: TestTabFoo,
  },
  {
    path: "bar",
    label: "Bar Label",
    component: TestTabBar,
  },
];

afterEach(cleanup);

describe("<TabRoutes />", () => {
  it("should render tab labels", () => {
    const { getByText } = renderWithRouter(<TabRoutes tabs={TEST_CONFIG} />);
    expect(getByText("Foo Label")).toBeInTheDocument();
    expect(getByText("Bar Label")).toBeInTheDocument();
  });
  it("should render default matching route", () => {
    const { getByText } = renderWithRouter(<TabRoutes tabs={TEST_CONFIG} />);
    expect(getByText("Test Tab Foo")).toBeInTheDocument();
  });
  it("should add .active class to the active link", () => {
    const { getByText } = renderWithRouter(<TabRoutes tabs={TEST_CONFIG} />);
    const container = getByText("Foo Label");
    expect(container.classList.contains("active")).toBe(true);
  });
  it("should change the route when a tab is clicked", () => {
    const { getByText, history } = renderWithRouter(
      <TabRoutes tabs={TEST_CONFIG} />,
    );
    fireEvent.click(getByText("Bar Label"));
    expect(history.location.pathname).toBe("/bar/");
  });
  it("should change the content when a tab is clicked", () => {
    const { getByText } = renderWithRouter(<TabRoutes tabs={TEST_CONFIG} />);
    fireEvent.click(getByText("Bar Label"));
    waitFor(() => {
      return expect(getByText("Test Tab Bar")).toBeInTheDocument();
    });
  });
  it("should add an .active class to the active label", () => {
    const { getByText } = renderWithRouter(<TabRoutes tabs={TEST_CONFIG} />);
    expect(getByText("Foo Label").classList.contains("active")).toBe(true);

    fireEvent.click(getByText("Bar Label"));

    waitFor(() => {
      const hasClass = getByText("Bar Label").classList.contains("active");
      return expect(hasClass).toBe(true);
    });
  });
  it("should have access to URL params from parent route", () => {
    const CheckIdComponent = () => {
      const { id } = useParams();
      return <div>The id is {id}</div>;
    };

    const { getByText } = renderWithRouter(
      <Route exact={true} path="/experiments/:id">
        <TabRoutes
          tabs={[
            {
              path: "",
              label: "Hello world",
              component: CheckIdComponent,
            },
          ]}
        />
      </Route>,
      { route: "/experiments/fooBarBaz" },
    );
    expect(getByText("The id is fooBarBaz")).toBeInTheDocument();
  });
});

describe("pathJoinWithTrailingSlash", () => {
  it("should add a trailing slash", () => {
    expect(pathJoinWithTrailingSlash("foo")).toBe("foo/");
  });
  it("should join paths without slashes", () => {
    expect(pathJoinWithTrailingSlash("foo", "bar")).toBe("foo/bar/");
  });
  it("should remove extra slashes", () => {
    expect(pathJoinWithTrailingSlash("/foo/", "/bar/", "baz//")).toBe(
      "/foo/bar/baz/",
    );
  });
});

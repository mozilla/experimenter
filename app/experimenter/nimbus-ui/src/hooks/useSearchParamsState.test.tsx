/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useNavigate } from "@reach/router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { RouterSlugProvider } from "../lib/test-utils";
import useSearchParamsState, { genStorageKey } from "./useSearchParamsState";

// TODO: Work out how to test this stuff with @testing-library/react-hooks?
// Depends on being wrapped by @reach/router, so that seems to make it difficult

describe("hooks/useSearchParamsState", () => {
  let originalSessionStorage: typeof window.sessionStorage;

  beforeAll(() => {
    originalSessionStorage = window.sessionStorage;
    // @ts-ignore excuse this hackery for mocking sessionStorage
    delete window.sessionStorage;
    Object.defineProperty(window, "sessionStorage", {
      writable: true,
      value: {
        getItem: jest.fn().mockName("getItem"),
        setItem: jest.fn().mockName("setItem"),
      },
    });
  });

  beforeEach(() => {
    // @ts-ignore excuse this hackery for mocking sessionStorage
    sessionStorage.getItem.mockClear();
    // @ts-ignore excuse this hackery for mocking sessionStorage
    sessionStorage.setItem.mockClear();
  });

  afterAll(() => {
    Object.defineProperty(window, "sessionStorage", {
      writable: true,
      value: originalSessionStorage,
    });
  });

  it("returns the current search parameters", async () => {
    const expected = { foo: "bar", baz: "quux" };
    const params = new URLSearchParams(expected);
    const path = `/xyzzy/edit?${params.toString()}`;
    render(<Subject path={path} />);
    expect(screen.getByTestId("params")).toHaveTextContent(params.toString());
  });

  it("updates the search parameters", async () => {
    render(
      <Subject
        path="/xyzzy/edit?deleteme=now&wibble=wobble&deletemetoo=also&beep=beep"
        paramsToDelete={["deleteme", "deletemetoo"]}
        paramsToSet={[
          ["three", "four"],
          ["one", "two"],
        ]}
      />,
    );
    fireEvent.click(screen.getByTestId("setParams"));
    await waitFor(() => {
      expect(screen.getByTestId("params")).toHaveTextContent(
        "wibble=wobble&beep=beep&three=four&one=two",
      );
    });
  });

  it("preserves search parameters on navigation", async () => {
    const storageSubKey = "PageFoo";
    const expectedSearch = "wibble=wobble&beep=beep";
    const path = `/xyzzy/edit?${expectedSearch}`;

    render(<Subject {...{ path, storageSubKey, navigateTo: "/quux/edit" }} />);
    fireEvent.click(screen.getByTestId("navigate"));

    await waitFor(() => {
      expect(window.sessionStorage.setItem).toHaveBeenCalledWith(
        genStorageKey(storageSubKey),
        expectedSearch,
      );
    });
  });

  it("restores search parameters on navigation with empty params", async () => {
    const storageSubKey = "PageFoo";
    const expectedSearch = "wibble=wobble&beep=beep";

    // @ts-ignore excuse this hackery for mocking sessionStorage
    window!.sessionStorage!.getItem.mockImplementation(() => expectedSearch);

    render(
      <Subject
        {...{
          storageSubKey,
          path: "/xyzzy/edit?donot=restorethis",
          navigateTo: "/quux/edit",
        }}
      />,
    );
    fireEvent.click(screen.getByTestId("navigate"));

    await waitFor(() => {
      expect(window.sessionStorage.getItem).toHaveBeenCalledWith(
        genStorageKey(storageSubKey),
      );
      expect(screen.getByTestId("params").textContent).toEqual(expectedSearch);
    });
  });

  it("does not restore empty search parameters", async () => {
    const storageSubKey = "PageFoo";

    // @ts-ignore excuse this hackery for mocking sessionStorage
    window!.sessionStorage!.getItem.mockImplementation(() => null);

    render(
      <Subject
        {...{
          storageSubKey,
          path: "/xyzzy/edit?donot=restorethis",
          navigateTo: "/quux/edit",
        }}
      />,
    );
    fireEvent.click(screen.getByTestId("navigate"));

    await waitFor(() => {
      expect(window.sessionStorage.getItem).toHaveBeenCalledWith(
        genStorageKey(storageSubKey),
      );
      expect(screen.getByTestId("params").textContent).toEqual("");
    });
  });

  interface SubjectProps {
    path: string;
    paramsToDelete?: Array<string>;
    // TODO: This should be Array<[string, string]> but current eslint version trips on it
    paramsToSet?: Array<string[]>;
    storageSubKey?: string;
    navigateTo?: string;
  }
  const Subject = (props: SubjectProps) => (
    <RouterSlugProvider path={props.path}>
      <SubjectInner {...props} />
    </RouterSlugProvider>
  );
  const SubjectInner = (props: SubjectProps) => {
    const { storageSubKey, navigateTo } = props;
    const navigate = useNavigate();
    const [params, setParams] = useSearchParamsState(storageSubKey);

    const onSetParamsClick = () => {
      const { paramsToDelete = [], paramsToSet = [] } = props;
      setParams((params) => {
        for (const name of paramsToDelete) {
          params.delete(name);
        }
        for (const [name, value] of paramsToSet) {
          params.set(name, value);
        }
      });
    };

    const onNavigateClick = () => navigateTo && navigate(navigateTo);

    return (
      <div>
        <code data-testid="params">{params.toString()}</code>
        <button data-testid="setParams" onClick={onSetParamsClick}>
          Set params
        </button>
        <button data-testid="navigate" onClick={onNavigateClick}>
          Navigate
        </button>
      </div>
    );
  };
});

/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  createHistory,
  createMemorySource,
  History,
  HistorySource,
  useNavigate,
} from "@reach/router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React, { useContext } from "react";
import { RouterSlugProvider } from "../lib/test-utils";
import useSearchParamsState, {
  SearchParamsContext,
} from "./useSearchParamsState";

// TODO: Work out how to test this stuff with @testing-library/react-hooks?
// Depends on being wrapped by @reach/router, so that seems to make it difficult

describe("hooks/useSearchParamsState", () => {
  // HACK: the types don't cover these properties exposed by the mock
  // memory history source, but they're useful for tests
  type MemoryHistorySource = HistorySource & {
    history: HistorySource["history"] & {
      entries: { pathname: string; search: string }[];
      index: number;
    };
  };

  let mockHistory: History;
  let mockHistorySource: MemoryHistorySource;
  let navigateSpy: jest.SpyInstance<Promise<void>, any>;

  beforeEach(() => {
    mockHistorySource = createMemorySource(
      "/xyzzy/edit",
    ) as MemoryHistorySource;
    mockHistory = createHistory(mockHistorySource);
    navigateSpy = jest.spyOn(mockHistory, "navigate");
  });

  const clickNavigate = () => {
    navigateSpy.mockClear();
    fireEvent.click(screen.getByTestId("navigate"));
  };

  it("returns the current search parameters", async () => {
    const expected = { foo: "bar", baz: "quux" };
    const params = new URLSearchParams(expected);
    const path = `/xyzzy/edit?${params.toString()}`;
    render(<Subject path={path} />);
    expect(screen.getByTestId("params")).toHaveTextContent(params.toString());
  });

  it("updates the search parameters", async () => {
    const path = "/xyzzy/edit";
    const expectedSearch = "wibble=wobble&beep=beep&three=four&one=two";
    render(
      <Subject
        path={`${path}?deleteme=now&wibble=wobble&deletemetoo=also&beep=beep`}
        paramsToDelete={["deleteme", "deletemetoo"]}
        paramsToSet={[
          ["three", "four"],
          ["one", "two"],
        ]}
      />,
    );
    fireEvent.click(screen.getByTestId("setParams"));
    await waitFor(() => {
      expect(screen.getByTestId("params")).toHaveTextContent(expectedSearch);
      expect(navigateSpy).toHaveBeenCalledWith(`${path}?${expectedSearch}`);
    });
  });

  it("preserves search parameters on navigation", async () => {
    const storageKey = "PageFoo";
    const expectedSearch = "wibble=wobble&beep=beep";
    const path = `/xyzzy/edit?${expectedSearch}`;

    render(<Subject {...{ path, storageKey, navigateTo: "/quux/edit" }} />);

    clickNavigate();

    await waitFor(() => {
      expect(screen.getByTestId("storage")).toHaveTextContent(
        JSON.stringify({
          current: {
            [storageKey]: expectedSearch,
          },
        }),
      );
    });
  });

  it("stores search parameters on navigation", async () => {
    const storageKey = "PageFoo";
    const expectedSearch = "wibble=wobble&beep=beep";
    const path = "/quux/edit";
    const initialStorage = {};

    render(
      <Subject
        {...{
          storageKey,
          path,
          navigateTo: `${path}?${expectedSearch}`,
          initialStorage,
        }}
      />,
    );

    clickNavigate();

    await waitFor(() => {
      expect(initialStorage).toEqual({
        [storageKey]: expectedSearch,
      });
    });
  });

  it("restores search parameters on fresh render if params empty", async () => {
    const storageKey = "PageFoo";
    const expectedSearch = "wibble=wobble&beep=beep";
    const path = "/quux/edit";

    render(
      <Subject
        {...{
          storageKey,
          path,
          initialStorage: {
            [storageKey]: expectedSearch,
          },
        }}
      />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("params").textContent).toEqual(expectedSearch);
      expect(navigateSpy).toHaveBeenCalledWith(`${path}?${expectedSearch}`, {
        replace: true,
      });
    });
  });

  it("does not restore empty search parameters", async () => {
    const storageKey = "PageFoo";
    const navigateTo = "/xyzzy/edit";

    render(
      <Subject
        {...{
          storageKey,
          path: "/quux/edit",
          navigateTo,
          initialStorage: { PageFoo: "" },
        }}
      />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("params").textContent).toEqual("");
      expect(navigateSpy).not.toHaveBeenCalledWith(`${navigateTo}?`, {
        replace: true,
      });
    });
  });

  it("does not restore previous search parameters after parameters are cleared (issue #6314)", async () => {
    const storageKey = "PageFoo";
    const expectedSearch = "wibble=wobble&beep=beep";
    const navigateTo = "/quux/edit";
    const initialStorage = {
      [storageKey]: expectedSearch,
    };

    render(
      <Subject
        {...{
          storageKey,
          path: `${navigateTo}?${expectedSearch}`,
          navigateTo,
          initialStorage,
        }}
      />,
    );

    clickNavigate();

    await waitFor(() => {
      expect(screen.getByTestId("params").textContent).toEqual("");
      expect(initialStorage).toEqual({
        [storageKey]: "",
      });
      expect(navigateSpy).not.toHaveBeenCalledWith(
        `${navigateTo}?${expectedSearch}`,
        { replace: true },
      );
    });
  });

  interface SubjectProps {
    path: string;
    paramsToDelete?: Array<string>;
    // TODO: This should be Array<[string, string]> but current eslint version trips on it
    paramsToSet?: Array<string[]>;
    initialStorage?: Record<string, string>;
    storageKey?: string;
    navigateTo?: string;
  }
  const Subject = (props: SubjectProps) => {
    mockHistory.navigate(props.path, { replace: true });
    return (
      <RouterSlugProvider
        {...{ path: props.path, mockHistorySource, mockHistory }}
      >
        <SubjectInner {...props} />
      </RouterSlugProvider>
    );
  };

  const SubjectInner = (props: SubjectProps) => {
    const { storageKey, navigateTo, initialStorage } = props;
    const navigate = useNavigate();
    const [params, setParams] = useSearchParamsState(storageKey);
    const storage = useContext(SearchParamsContext);

    if (initialStorage) {
      storage!.current = initialStorage;
    }

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
        <code data-testid="storage">{JSON.stringify(storage)}</code>
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

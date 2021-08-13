/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useNavigate } from "@reach/router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React, { useContext } from "react";
import { RouterSlugProvider } from "../lib/test-utils";
import useSearchParamsState, {
  SearchParamsContext,
} from "./useSearchParamsState";

// TODO: Work out how to test this stuff with @testing-library/react-hooks?
// Depends on being wrapped by @reach/router, so that seems to make it difficult

describe("hooks/useSearchParamsState", () => {
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
    const storageKey = "PageFoo";
    const expectedSearch = "wibble=wobble&beep=beep";
    const path = `/xyzzy/edit?${expectedSearch}`;

    render(<Subject {...{ path, storageKey, navigateTo: "/quux/edit" }} />);
    fireEvent.click(screen.getByTestId("navigate"));

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

  it("restores search parameters on navigation with empty params", async () => {
    const storageKey = "PageFoo";
    const expectedSearch = "wibble=wobble&beep=beep";

    render(
      <Subject
        {...{
          storageKey,
          path: "/xyzzy/edit?donot=restorethis",
          navigateTo: "/quux/edit",
          initialStorage: {
            [storageKey]: expectedSearch,
          },
        }}
      />,
    );

    fireEvent.click(screen.getByTestId("navigate"));

    await waitFor(() => {
      expect(screen.getByTestId("params").textContent).toEqual(expectedSearch);
    });
  });

  it("does not restore empty search parameters", async () => {
    const storageKey = "PageFoo";
    render(
      <Subject
        {...{
          storageKey,
          path: "/xyzzy/edit?donot=restorethis",
          navigateTo: "/xyzzy/edit",
          initialStorage: {},
        }}
      />,
    );

    fireEvent.click(screen.getByTestId("navigate"));

    await waitFor(() => {
      expect(screen.getByTestId("params").textContent).toEqual("");
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
  const Subject = (props: SubjectProps) => (
    <RouterSlugProvider path={props.path}>
      <SubjectInner {...props} />
    </RouterSlugProvider>
  );
  const SubjectInner = (props: SubjectProps) => {
    const { storageKey, navigateTo, initialStorage } = props;
    const navigate = useNavigate();
    const [params, setParams] = useSearchParamsState(storageKey);
    const storage = useContext(SearchParamsContext);

    if (initialStorage) {
      Object.assign(storage!.current, initialStorage);
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

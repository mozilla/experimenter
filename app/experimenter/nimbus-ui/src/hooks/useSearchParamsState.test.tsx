/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { RouterSlugProvider } from "../lib/test-utils";
import useSearchParamsState from "./useSearchParamsState";

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

  interface SubjectProps {
    path: string;
    paramsToDelete?: Array<string>;
    // TODO: This should be Array<[string, string]> but current eslint version trips on it
    paramsToSet?: Array<string[]>;
  }
  const Subject = (props: SubjectProps) => (
    <RouterSlugProvider path={props.path}>
      <SubjectInner {...props} />
    </RouterSlugProvider>
  );
  const SubjectInner = (props: SubjectProps) => {
    const [params, setParams] = useSearchParamsState();
    const onClick = () => {
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
    return (
      <div>
        <code data-testid="params">{params.toString()}</code>
        <button data-testid="setParams" onClick={onClick}>
          Set params
        </button>
      </div>
    );
  };
});

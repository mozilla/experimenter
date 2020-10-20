/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { InMemoryCache, ApolloClient, ApolloProvider } from "@apollo/client";
import { MockLink, MockedResponse } from "@apollo/client/testing";

export interface MockedProps {
  childProps?: object;
  children?: React.ReactElement;
  mocks?: MockedResponse<Record<string, any>>[];
}

export interface MockedState {
  client: ApolloClient<any>;
}

// Disabling this rule for now because we'll eventually
// be using props from MockedProps.
// eslint-disable-next-line no-empty-pattern
export function createCache({}: MockedProps = {}) {
  const cache = new InMemoryCache();

  // As we set up new cached queries we can use
  // `cache.writeQuery` to set up default data
  // in tests with values set in MockedProps
  //
  // cache.writeQuery({
  //   query: MY_QUERY,
  //   data: {
  //     queryDataDefault,
  //   },
  // });

  return cache;
}

export class MockedCache extends React.Component<MockedProps, MockedState> {
  constructor(props: MockedProps) {
    super(props);
    this.state = {
      client: new ApolloClient({
        cache: createCache(props),
        link: new MockLink(props.mocks || [], true),
      }),
    };
  }

  render() {
    const { children, childProps } = this.props;
    return children ? (
      <ApolloProvider client={this.state.client}>
        {React.cloneElement(React.Children.only(children), { ...childProps })}
      </ApolloProvider>
    ) : null;
  }

  componentWillUnmount() {
    this.state.client.stop();
  }
}

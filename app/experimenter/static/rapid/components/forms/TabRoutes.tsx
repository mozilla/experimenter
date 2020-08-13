import React from "react";
import {
  NavLink,
  Route,
  RouteProps,
  Switch,
  useRouteMatch,
} from "react-router-dom";

/**
 * Helper function to join paths without duplicating slashes.
 * Adds a trailing slash to be inline with Experimenter's style of URL
 */
export function pathJoinWithTrailingSlash(...paths: Array<string>): string {
  return `${paths.join("/")}/`.replace(/\/{1,}/g, "/");
}

interface TabProps {
  tabs: Array<{
    className?: string;
    label: string;
    path: string;
    render?: RouteProps["render"];
    component?: RouteProps["component"];
  }>;
}

/**
 * Creates horizontal tabs that will also trigger a route change.
 * Paths are relative to the page on which TabRoutes is rendered, so
 * the default route should be path=""
 */
export const TabRoutes: React.FC<TabProps> = ({ tabs }) => {
  const { url, path } = useRouteMatch();
  return (
    <div>
      <ul className="nav nav-tabs mb-4">
        {tabs.map((tab) => (
          <li key={tab.path} className="nav-item">
            <NavLink
              activeClassName="active"
              className="nav-link"
              exact={true}
              to={pathJoinWithTrailingSlash(url, tab.path)}
            >
              {tab.label}
            </NavLink>
          </li>
        ))}
      </ul>
      <Switch>
        {tabs.map((tab) => (
          <Route
            key={tab.path}
            component={tab.component}
            exact={true}
            path={pathJoinWithTrailingSlash(path, tab.path)}
            render={tab.render}
          />
        ))}
      </Switch>
    </div>
  );
};

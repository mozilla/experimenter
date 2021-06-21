/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect, useState } from "react";
import { ReactComponent as Airplane } from "../../images/airplane.svg";
import { StatusCheck } from "../../lib/experiment";
import { LinkNav } from "../LinkNav";
import getSummaryAction from "../PageSummary/getSummaryAction";

type LinkNavSummaryProps = {
  slug: string;
  status: StatusCheck;
  canReview: boolean | null;
  showSummaryAction?: boolean;
};

const LinkNavSummary = ({
  slug,
  status,
  canReview,
  showSummaryAction = true,
}: LinkNavSummaryProps) => {
  const [summaryAction, setSummaryAction] = useState("");
  useEffect(() => {
    setSummaryAction(getSummaryAction(status, canReview));
  }, [status, canReview]);

  return (
    <LinkNav route={slug} storiesOf={"pages/Summary"} testid={"nav-summary"}>
      <Airplane className="sidebar-icon align-self-start mt-1" />
      {summaryAction && showSummaryAction ? (
        <span>
          <span>Summary</span>
          <span className="d-block small">{summaryAction}</span>
        </span>
      ) : (
        "Summary"
      )}
    </LinkNav>
  );
};

export default LinkNavSummary;

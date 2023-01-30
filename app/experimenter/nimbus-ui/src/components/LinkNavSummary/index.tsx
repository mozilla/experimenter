/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect, useState } from "react";
import { LinkNav } from "src/components/LinkNav";
import { ReactComponent as Airplane } from "src/images/airplane.svg";
import { getSummaryAction, StatusCheck } from "src/lib/experiment";

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
    <LinkNav route={slug} testid={"nav-summary"}>
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

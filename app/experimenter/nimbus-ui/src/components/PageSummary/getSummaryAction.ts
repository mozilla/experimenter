/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { StatusCheck } from "../../lib/experiment";

const getSummaryAction = (status: StatusCheck, canReview: boolean | null) => {
  // has pending review approval
  if (status.review || status.approved || status.waiting) {
    if (!canReview) {
      if (status.endRequested) {
        return "Requested End";
      } else {
        return "Requested Launch";
      }
    } else {
      if (status.endRequested) {
        return "Review End Request";
      } else {
        return "Review Launch Request";
      }
    }
  }

  if (!status.launched) {
    return "Request Launch";
  }
  return "";
};

export default getSummaryAction;

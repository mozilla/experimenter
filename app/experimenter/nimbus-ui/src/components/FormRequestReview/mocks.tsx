/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import FormRequestReview from ".";
import { MockedCache, mockExperimentQuery } from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";

export const Subject = ({
  isLoading = false,
  submitError = null,
  onSubmit = () => {},
  status = NimbusExperimentStatus.DRAFT,
}: Partial<React.ComponentProps<typeof FormRequestReview>> & {
  status?: NimbusExperimentStatus;
}) => {
  const { mock } = mockExperimentQuery("demo-slug", {
    status,
  });

  return (
    <div className="p-5">
      <MockedCache mocks={[mock]}>
        <FormRequestReview
          {...{
            isLoading,
            submitError,
            onSubmit,
          }}
        />
      </MockedCache>
    </div>
  );
};

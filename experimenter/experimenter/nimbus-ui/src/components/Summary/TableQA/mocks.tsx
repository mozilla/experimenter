/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
import React, { useState } from "react";
import TableQA from "src/components/Summary/TableQA";
import { RouterSlugProvider } from "src/lib/test-utils";
import { NimbusExperimentQAStatusEnum } from "src/types/globalTypes";

export const Subject = ({
  id = 123,
  publishStatus = null,
  qaStatus = NimbusExperimentQAStatusEnum.NOT_SET,
  qaComment = null,
  isLoading = false,
  onSubmit = async (data) => {},
  ...props
}: Partial<React.ComponentProps<typeof TableQA>>) => {
  const [showEditor, setShowEditor] = useState(
    typeof props.showEditor !== "undefined" ? props.showEditor : false,
  );
  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>(
    props.submitErrors || {},
  );
  const isServerValid =
    typeof props.isServerValid !== "undefined" ? props.isServerValid : false;

  return (
    <RouterSlugProvider>
      <div className="p-4">
        <TableQA
          {...{
            id,
            publishStatus,
            qaStatus,
            qaComment,
            isLoading,
            onSubmit,
            showEditor,
            setShowEditor,
            submitErrors,
            setSubmitErrors,
            isServerValid,
            ...props,
          }}
        />
      </div>
    </RouterSlugProvider>
  );
};

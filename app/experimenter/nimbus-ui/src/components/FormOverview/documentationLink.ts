/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useEffect, useMemo } from "react";
import { ArrayField, useFieldArray, UseFormMethods } from "react-hook-form";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusDocumentationLinkTitle } from "../../types/globalTypes";

type DefaultDocumentationLink = {
  title: NimbusDocumentationLinkTitle | "";
  link: string;
};

export type AnnotatedDocumentationLink = DefaultDocumentationLink & {
  isValid: boolean;
  isDirty: boolean;
  errors: Record<string, string[]>;
};

export function useDocumentationLinks(
  experiment: getExperiment_experimentBySlug | null | undefined,
  control: UseFormMethods["control"],
  setValue: UseFormMethods["setValue"],
) {
  const {
    fields: documentationLinks,
    append,
    remove,
  } = useFieldArray<AnnotatedDocumentationLink>({
    control,
    name: "documentationLinks",
  });

  const stateAPI = useMemo(
    () => ({
      addDocumentationLink: () => {
        append(emptyDocumentationLink());
      },
      removeDocumentationLink: (
        documentationLink: Partial<
          ArrayField<AnnotatedDocumentationLink, "id">
        >,
      ) => {
        const index = documentationLinks.findIndex(
          (d) => d.id === documentationLink.id,
        );
        remove(index);
      },
    }),
    [documentationLinks, append, remove],
  );

  useEffect(() => {
    const documentationLinks = setupDocumentationLinks(
      experiment?.documentationLinks,
    );
    setValue("documentationLinks", documentationLinks);
  }, [experiment, setValue]);

  return { documentationLinks, ...stateAPI };
}

export const setupDocumentationLinks = (
  existing?: getExperiment_experimentBySlug["documentationLinks"],
) => {
  const hasExisting = existing && existing.length > 0;
  const initialDocumentationLinks = hasExisting
    ? (existing! as DefaultDocumentationLink[]).map(annotateDocumentationLink)
    : [emptyDocumentationLink()];

  return initialDocumentationLinks;
};

export const emptyDocumentationLink = () => {
  return annotateDocumentationLink({ title: "", link: "" });
};

export function annotateDocumentationLink(
  documentationLink: DefaultDocumentationLink,
): AnnotatedDocumentationLink {
  return {
    ...documentationLink,
    isValid: true,
    isDirty: false,
    errors: {},
  };
}

export function stripInvalidDocumentationLinks(data: Record<string, any>) {
  let documentationLinks: DefaultDocumentationLink[] = data.documentationLinks;

  if (!documentationLinks || !documentationLinks.length) {
    return data;
  }

  documentationLinks = documentationLinks.filter(
    (documentationLink) =>
      documentationLink.title.length && documentationLink.link.length,
  );

  return {
    ...data,
    documentationLinks,
  };
}

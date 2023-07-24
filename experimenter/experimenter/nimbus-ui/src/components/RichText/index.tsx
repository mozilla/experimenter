/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import LinkExternal from "src/components/LinkExternal";

// Match http://, https://, www., a combo, but not neither
const LINK_MATCHER =
  /((?<!\+)(?:https?:\/\/(?:www\.)?|www\.)(?:[a-zA-Z\d-_.]+(?:(?:\.|@)[a-zA-Z\d]{2,}))(?:(?:[-a-zA-Z\d:%_+.~#*$!?&//=@]*)(?:[,](?![\s]))*)*)/gi;
const NEWLINE_MATCHER = /(\r\n|\r|\n)/gi;

const RichText = ({ text }: { text: string }) => (
  <>
    {text
      .split(
        new RegExp(`${LINK_MATCHER.source}|${NEWLINE_MATCHER.source}`, "gi"),
      )
      .map((word, idx) => {
        const linkMatch = word?.match(LINK_MATCHER);
        const newlineMatch = word?.match(NEWLINE_MATCHER);

        if (linkMatch) {
          let href = (text = linkMatch[0]);
          if (!href.startsWith("http")) {
            href = `https://${href}`;
          }
          return (
            <LinkExternal key={idx} {...{ href }}>
              {text}
            </LinkExternal>
          );
        }

        if (newlineMatch) {
          return (
            <React.Fragment key={idx}>
              {word}
              <br />
            </React.Fragment>
          );
        }

        return word;
      })}
  </>
);

export default RichText;

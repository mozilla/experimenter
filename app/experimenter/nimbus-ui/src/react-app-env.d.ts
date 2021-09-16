/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/// <reference types="react-scripts" />

type DateTime = string;
type ObjectField = Record<string, any> | string;

type SerializerMessage = string[];
type SerializerSet = Record<string, SerializerMessage>;
type SerializerMessages<
  T = SerializerMessage | SerializerSet | SerializerSet[],
> = Record<string, T>;

// TODO: implement the correct type here for EXP-1766
type Upload = any;

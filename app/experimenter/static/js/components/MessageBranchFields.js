import PropTypes from "prop-types";
import React from "react";
import { Map } from "immutable";
import { boundClass } from "autobind-decorator";

import {
  BRANCH_RATIO_HELP,
  BRANCH_NAME_HELP,
  BRANCH_DESCRIPTION_HELP,
  MESSAGE_CONTENT_HELP,
  MESSAGE_TARGETING_HELP,
  MESSAGE_THRESHOLD_HELP,
  MESSAGE_TRIGGERS_HELP,
} from "experimenter/components/constants";

@boundClass
class MessageBranchFields extends React.PureComponent {
  static propTypes = {
    branch: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    renderField: PropTypes.func,
    options: PropTypes.object,
  };

  render() {
    return (
      <React.Fragment>
        {this.props.renderField(
          "ratio",
          "Branch Size",
          this.props.branch.get("ratio"),
          this.props.errors.get("ratio"),
          BRANCH_RATIO_HELP,
        )}
        {this.props.renderField(
          "name",
          "Name",
          this.props.branch.get("name"),
          this.props.errors.get("name"),
          BRANCH_NAME_HELP,
        )}
        {this.props.renderField(
          "description",
          "Description",
          this.props.branch.get("description"),
          this.props.errors.get("description"),
          BRANCH_DESCRIPTION_HELP,
        )}

        {this.props.options.isCfr ? (
          <React.Fragment>
            {this.props.renderField(
              "message_targeting",
              "Message Targeting",
              this.props.branch.get("message_targeting"),
              this.props.errors.get("message_targeting"),
              MESSAGE_TARGETING_HELP,
            )}
            {this.props.renderField(
              "message_threshold",
              "Message Threshold",
              this.props.branch.get("message_threshold"),
              this.props.errors.get("message_thresold"),
              MESSAGE_THRESHOLD_HELP,
            )}
            {this.props.renderField(
              "message_triggers",
              "Message Triggers",
              this.props.branch.get("message_triggers"),
              this.props.errors.get("message_triggers"),
              MESSAGE_TRIGGERS_HELP,
            )}
          </React.Fragment>
        ) : null}

        {this.props.renderField(
          "value",
          "Message Content",
          this.props.branch.get("value"),
          this.props.errors.get("value"),
          MESSAGE_CONTENT_HELP,
          "textarea",
          10,
        )}
      </React.Fragment>
    );
  }
}

export default MessageBranchFields;

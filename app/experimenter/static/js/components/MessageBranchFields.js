import PropTypes from "prop-types";
import React from "react";
import { Map } from "immutable";
import { boundClass } from "autobind-decorator";

import {
  BRANCH_RATIO_HELP,
  BRANCH_NAME_HELP,
  BRANCH_DESCRIPTION_HELP,
  MESSAGE_ID_HELP,
  MESSAGE_CONTENT_HELP,
} from "experimenter/components/constants";

@boundClass
class MessageBranchFields extends React.PureComponent {
  static propTypes = {
    branch: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    renderField: PropTypes.func,
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
        {this.props.renderField(
          "message_id",
          "Message ID",
          this.props.branch.get("message_id"),
          this.props.errors.get("message_id"),
          MESSAGE_ID_HELP,
        )}
        {this.props.renderField(
          "value",
          "Content",
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

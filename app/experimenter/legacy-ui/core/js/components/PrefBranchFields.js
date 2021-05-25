import { boundClass } from "autobind-decorator";
import {
  BRANCH_DESCRIPTION_HELP,
  BRANCH_NAME_HELP,
  BRANCH_RATIO_HELP,
  PREF_VALUE_HELP,
} from "experimenter/components/constants";
import { Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";

@boundClass
class PrefBranchFields extends React.PureComponent {
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
          "value",
          "Value",
          this.props.branch.get("value"),
          this.props.errors.get("value"),
          PREF_VALUE_HELP,
        )}
      </React.Fragment>
    );
  }
}

export default PrefBranchFields;

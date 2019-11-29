import PropTypes from "prop-types";
import React from "react";
import { Map, List } from "immutable";
import PrefManager from "experimenter/components/PrefManager";
import { boundClass } from "autobind-decorator";

import {
  BRANCH_RATIO_HELP,
  BRANCH_NAME_HELP,
  BRANCH_DESCRIPTION_HELP,
} from "experimenter/components/constants";

@boundClass
class MultiPrefBranchFields extends React.PureComponent {
  static propTypes = {
    branch: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleErrorsChange: PropTypes.instanceOf(Map),
    index: PropTypes.number,
    onChange: PropTypes.func,
    renderField: PropTypes.func,
  };
  handlePrefChange(value) {
    this.props.onChange("preferences", value);
  }

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
        <PrefManager
          preferences={this.props.branch.get("preferences", new List())}
          errors={this.props.errors.get("preferences", new List())}
          variant_index={this.props.index}
          onChange={value => {
            this.handlePrefChange(value);
          }}
          handleErrorsChange={this.props.handleErrorsChange}
        />
      </React.Fragment>
    );
  }
}

export default MultiPrefBranchFields;

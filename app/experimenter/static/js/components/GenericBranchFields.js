import PropTypes from "prop-types";
import React from "react";
import { Map } from "immutable";
import { boundClass } from "autobind-decorator";

import DesignInput from "experimenter/components/DesignInput";
import {
  BRANCH_RATIO_HELP,
  BRANCH_NAME_HELP,
  BRANCH_DESCRIPTION_HELP,
} from "experimenter/components/constants";

@boundClass
class GenericBranchFields extends React.PureComponent {
  static propTypes = {
    branch: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleChange: PropTypes.func,
    index: PropTypes.number,
  };

  renderField(name, label, help) {
    return (
      <DesignInput
        label={label}
        name={`variants[${this.props.index}][${name}]`}
        id={`variants-${this.props.index}-${name}`}
        value={this.props.branch.get(name)}
        onChange={value => {
          this.props.handleChange(name, value);
        }}
        error={this.props.errors.get(name)}
        helpContent={help}
      />
    );
  }

  render() {
    return (
      <React.Fragment>
        {this.renderField("ratio", "Branch Size", BRANCH_RATIO_HELP)}
        {this.renderField("name", "Name", BRANCH_NAME_HELP)}
        {this.renderField(
          "description",
          "Description",
          BRANCH_DESCRIPTION_HELP,
        )}
      </React.Fragment>
    );
  }
}

export default GenericBranchFields;

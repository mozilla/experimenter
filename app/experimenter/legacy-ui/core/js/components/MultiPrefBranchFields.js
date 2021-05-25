import { boundClass } from "autobind-decorator";
import {
  BRANCH_DESCRIPTION_HELP,
  BRANCH_NAME_HELP,
  BRANCH_RATIO_HELP,
} from "experimenter/components/constants";
import PrefManager from "experimenter/components/PrefManager";
import { List, Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";

@boundClass
class MultiPrefBranchFields extends React.PureComponent {
  static propTypes = {
    branch: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleErrorsChange: PropTypes.instanceOf(Map),
    index: PropTypes.number,
    onChange: PropTypes.func,
    onErrorChange: PropTypes.func,
    renderField: PropTypes.func,
  };

  static defaultProps = {
    errors: new Map(),
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
        <PrefManager
          preferences={this.props.branch.get("preferences", new List())}
          errors={this.props.errors.get("preferences", new List())}
          onDataChange={(value) => {
            this.props.onChange("preferences", value);
          }}
          onErrorChange={(errors) => {
            this.props.onErrorChange("preferences", errors);
          }}
          variantIndex={this.props.index}
        />
      </React.Fragment>
    );
  }
}

export default MultiPrefBranchFields;

import { Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";

import BranchManager from "experimenter/components/BranchManager";
import DesignInput from "experimenter/components/DesignInput";
import GenericBranchFields from "experimenter/components/GenericBranchFields";

export default class GenericForm extends React.PureComponent {
  static propTypes = {
    data: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleDataChange: PropTypes.func,
    onAddBranch: PropTypes.func,
    onRemoveBranch: PropTypes.func,
  };

  render() {
    return (
      <div>
        <DesignInput
          label="Design"
          name="design"
          onChange={value => {
            this.props.handleDataChange("design", value);
          }}
          value={this.props.data.get("design")}
          error={this.props.errors.get("design", "")}
          as="textarea"
          rows="10"
          helpContent={
            <div>
              <p>Specify the design of the experiment.</p>
            </div>
          }
        />

        <hr className="heavy-line my-5" />

        <BranchManager
          branches={this.props.data.get("variants")}
          onAddBranch={this.props.onAddBranch}
          onRemoveBranch={this.props.onRemoveBranch}
          onChange={value => {
            this.props.handleDataChange("variants", value);
          }}
          branchFieldsComponent={GenericBranchFields}
          errors={this.props.errors}
        />
      </div>
    );
  }
}

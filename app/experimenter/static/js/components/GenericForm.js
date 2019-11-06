import React from "react";

import DesignInput from "experimenter/components/DesignInput";
import BranchManager from "experimenter/components/BranchManager";
import GenericBranchFields from "experimenter/components/GenericBranchFields";

export default class GenericForm extends React.PureComponent {
  render() {
    return (
      <div>
        <DesignInput
          label="Design"
          name="design"
          onChange={value => {
            this.props.handleDataChange("design", value);
          }}
          value={this.props.data.design}
          error={this.props.errors ? this.props.errors.design : ""}
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
          branches={this.props.data.variants}
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

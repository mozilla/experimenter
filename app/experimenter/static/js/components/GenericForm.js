import { List, Map } from "immutable";
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
    handleErrorsChange: PropTypes.func,
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
          branchFieldsComponent={GenericBranchFields}
          branches={this.props.data.get("variants", new List())}
          errors={this.props.errors.get("variants", new List())}
          handleDataChange={this.props.handleDataChange}
          handleErrorsChange={this.props.handleErrorsChange}
        />
      </div>
    );
  }
}

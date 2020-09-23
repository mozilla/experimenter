import PropTypes from "prop-types";
import React from "react";
import { List, Map } from "immutable";

import BranchManager from "experimenter/components/BranchManager";
import DesignInput from "experimenter/components/DesignInput";
import GenericBranchFields from "experimenter/components/GenericBranchFields";
import { DESIGN_HELP } from "experimenter/components/constants";

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
          id="id_design"
          dataTestId="design"
          onChange={(value) => {
            this.props.handleDataChange("design", value);
          }}
          value={this.props.data.get("design")}
          error={this.props.errors.get("design", "")}
          as="textarea"
          rows="10"
          helpContent={DESIGN_HELP}
          labelColumnWidth={2}
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

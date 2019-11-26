import PropTypes from "prop-types";
import React from "react";
import { List, Map } from "immutable";
import { Row, Col } from "react-bootstrap";

import BranchManager from "experimenter/components/BranchManager";
import DesignInput from "experimenter/components/DesignInput";
import GenericBranchFields from "experimenter/components/GenericBranchFields";
import {
  ADDON_EXPERIMENT_ID_HELP,
  ADDON_RELEASE_URL_HELP,
} from "experimenter/components/constants";

export default class AddonForm extends React.PureComponent {
  static propTypes = {
    data: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleDataChange: PropTypes.func,
    handleErrorsChange: PropTypes.func,
  };

  render() {
    return (
      <div>
        <Row className="mb-3">
          <Col md={{ span: 4, offset: 3 }}>
            <h4 className="mb-3">Firefox Add-On</h4>
          </Col>
        </Row>

        <DesignInput
          label="Addon Experiment Name"
          name="addon_experiment_id"
          onChange={value => {
            this.props.handleDataChange("addon_experiment_id", value);
          }}
          value={this.props.data.get("addon_experiment_id")}
          error={this.props.errors.get("addon_experiment_id", "")}
          helpContent={ADDON_EXPERIMENT_ID_HELP}
        />

        <DesignInput
          label="Signed Release URL"
          name="addon_release_url"
          onChange={value => {
            this.props.handleDataChange("addon_release_url", value);
          }}
          value={this.props.data.get("addon_release_url")}
          error={this.props.errors.get("addon_release_url", "")}
          helpContent={ADDON_RELEASE_URL_HELP}
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

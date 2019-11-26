import PropTypes from "prop-types";
import React from "react";
import { List, Map } from "immutable";
import { Row, Col } from "react-bootstrap";

import BranchManager from "experimenter/components/BranchManager";
import DesignInput from "experimenter/components/DesignInput";
import PrefBranchFields from "experimenter/components/PrefBranchFields";
import {
  PREF_KEY_HELP,
  PREF_TYPE_HELP,
  PREF_BRANCH_HELP,
} from "experimenter/components/constants";

export default class PrefForm extends React.PureComponent {
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
            <h4>Firefox Pref</h4>
          </Col>
        </Row>

        <DesignInput
          label="Pref Name"
          name="pref_key"
          id="id_pref_key"
          onChange={value => {
            this.props.handleDataChange("pref_key", value);
          }}
          value={this.props.data.get("pref_key")}
          error={this.props.errors.get("pref_key", "")}
          helpContent={PREF_KEY_HELP}
        />

        <DesignInput
          label="Pref Type"
          name="pref_type"
          id="id_pref_type"
          onChange={value => {
            this.props.handleDataChange("pref_type", value);
          }}
          value={this.props.data.get("pref_type")}
          error={this.props.errors.get("pref_type", "")}
          as="select"
          helpContent={PREF_TYPE_HELP}
        >
          <option>Firefox Pref Type</option>
          <option>boolean</option>
          <option>integer</option>
          <option>string</option>
          <option>json string</option>
        </DesignInput>

        <DesignInput
          label="Pref Branch"
          name="pref_branch"
          id="id_pref_branch"
          onChange={value => {
            this.props.handleDataChange("pref_branch", value);
          }}
          value={this.props.data.get("pref_branch")}
          error={this.props.errors.get("pref_branch", "")}
          as="select"
          helpContent={PREF_BRANCH_HELP}
        >
          <option>Firefox Pref Branch</option>
          <option>default</option>
          <option>user</option>
        </DesignInput>

        <hr className="heavy-line my-5" />

        <BranchManager
          branchFieldsComponent={PrefBranchFields}
          branches={this.props.data.get("variants", new List())}
          errors={this.props.errors.get("variants", new List())}
          handleDataChange={this.props.handleDataChange}
          handleErrorsChange={this.props.handleErrorsChange}
        />
      </div>
    );
  }
}

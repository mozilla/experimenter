import BranchManager from "experimenter/components/BranchManager";
import {
  PREF_BRANCH_HELP,
  PREF_NAME_HELP,
  PREF_TYPE_HELP,
} from "experimenter/components/constants";
import DesignInput from "experimenter/components/DesignInput";
import MultiPrefBranchFields from "experimenter/components/MultiPrefBranchFields";
import PrefBranchFields from "experimenter/components/PrefBranchFields";
import RadioButton from "experimenter/components/RadioButton";
import { List, Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Col, Row } from "react-bootstrap";

export default class PrefForm extends React.PureComponent {
  static propTypes = {
    data: PropTypes.instanceOf(Map),
    type: PropTypes.string,
    errors: PropTypes.instanceOf(Map),
    handleDataChange: PropTypes.func,
    handleErrorsChange: PropTypes.func,
    handleReloadAPIState: PropTypes.func,
  };

  renderSingularPrefInfo() {
    if (!this.props.data.get("is_multi_pref")) {
      return (
        <div>
          <DesignInput
            label="Pref Name"
            name="pref_name"
            id="id_pref_name"
            onChange={(value) => {
              this.props.handleDataChange("pref_name", value);
            }}
            value={this.props.data.get("pref_name")}
            error={this.props.errors.get("pref_name", "")}
            helpContent={PREF_NAME_HELP}
            labelColumnWidth={2}
          />

          <DesignInput
            label="Pref Type"
            name="pref_type"
            id="id_pref_type"
            onChange={(value) => {
              this.props.handleDataChange("pref_type", value);
            }}
            value={this.props.data.get("pref_type")}
            error={this.props.errors.get("pref_type", "")}
            as="select"
            helpContent={PREF_TYPE_HELP}
            labelColumnWidth={2}
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
            onChange={(value) => {
              this.props.handleDataChange("pref_branch", value);
            }}
            value={this.props.data.get("pref_branch")}
            error={this.props.errors.get("pref_branch", "")}
            as="select"
            helpContent={PREF_BRANCH_HELP}
            labelColumnWidth={2}
          >
            <option>Firefox Pref Branch</option>
            <option>default</option>
            <option>user</option>
          </DesignInput>

          <hr className="heavy-line my-5" />
        </div>
      );
    }
  }

  render() {
    return (
      <div>
        <Row>
          <Col md={{ span: 10, offset: 2 }}>
            <RadioButton
              elementLabel="How Many Prefs does this ship?"
              fieldName="is_multi_pref"
              choices={[
                { value: false, label: "One Pref for all branches" },
                { value: true, label: "Different Prefs per branch" },
              ]}
              onChange={(event) => {
                this.props.handleReloadAPIState(
                  "is_multi_pref",
                  event.target.value === "true",
                );
              }}
              value={this.props.data.get("is_multi_pref")}
            />
            <hr className="heavy-line my-5" />
          </Col>
        </Row>
        {this.renderSingularPrefInfo()}
        <BranchManager
          branchFieldsComponent={
            this.props.data.get("is_multi_pref")
              ? MultiPrefBranchFields
              : PrefBranchFields
          }
          branches={this.props.data.get("variants", new List())}
          errors={this.props.errors.get("variants", new List())}
          handleDataChange={this.props.handleDataChange}
          handleErrorsChange={this.props.handleErrorsChange}
        />
      </div>
    );
  }
}

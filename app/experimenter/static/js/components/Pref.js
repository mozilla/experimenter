import { boundClass } from "autobind-decorator";
import { Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Button, Row, Col } from "react-bootstrap";
import DesignInput from "experimenter/components/DesignInput";

import {
  PREF_KEY_HELP,
  PREF_TYPE_HELP,
  PREF_BRANCH_HELP,
} from "experimenter/components/constants";
import { PREF_VALUE_HELP } from "./constants";

@boundClass
class Pref extends React.PureComponent {
  static propTypes = {
    preference: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    index: PropTypes.number,
    onChange: PropTypes.func,
    remove: PropTypes.func,
  };

  handlePrefValueChange(key, value) {
    const { onChange, preference } = this.props;
    onChange(preference.set(key, value));
  }

  renderTitle() {
    return <h4>Pref {this.props.index + 1}</h4>;
  }

  renderRemoveButton() {
    const { index } = this.props;
    if (index != 0) {
      return (
        <Button
          variant="outline-danger"
          onClick={() => {
            this.props.remove(index);
          }}
          id="remove-branch-button"
        >
          <span className="fas fa-times" /> Remove Pref
        </Button>
      );
    }
  }

  renderPrefBranch() {
    return (
      <div>
        <DesignInput
          label="Pref Name"
          name="pref_key"
          id="id_pref_key"
          onChange={value => {
            this.handlePrefValueChange("pref_name", value);
          }}
          value={
            this.props.preference
              ? this.props.preference.get("pref_name")
              : null
          }
          error={this.props.errors.get("pref_name", null)}
          helpContent={PREF_KEY_HELP}
        />

        <DesignInput
          label="Pref Type"
          name="pref_type"
          id="id_pref_type"
          onChange={value => {
            this.handlePrefValueChange("pref_type", value);
          }}
          value={
            this.props.preference
              ? this.props.preference.get("pref_type")
              : null
          }
          error={this.props.errors.get("pref_type", null)}
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
            this.handlePrefValueChange("pref_branch", value);
          }}
          value={
            this.props.preference
              ? this.props.preference.get("pref_branch")
              : null
          }
          error={this.props.errors.get("pref_branch", null)}
          as="select"
          helpContent={PREF_BRANCH_HELP}
        >
          <option>Firefox Pref Branch</option>
          <option>default</option>
          <option>user</option>
        </DesignInput>
        <DesignInput
          label="Pref Value"
          name="pref_value"
          id="id_pref_value"
          onChange={value => {
            this.handlePrefValueChange("pref_value", value);
          }}
          value={
            this.props.preference
              ? this.props.preference.get("pref_value")
              : null
          }
          error={this.props.errors.get("pref_value", null)}
          helpContent={PREF_VALUE_HELP}
        />
      </div>
    );
  }
  render() {
    return (
      <div key={this.props.index} id="control-branch-group">
        <Row className="mb-3">
          <Col md={{ span: 4, offset: 3 }}>{this.renderTitle()}</Col>
          <Col md={5} className="text-right">
            {this.renderRemoveButton()}
          </Col>
        </Row>
        {this.renderPrefBranch()}
      </div>
    );
  }
}
export default Pref;

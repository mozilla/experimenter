import { boundClass } from "autobind-decorator";
import {
  PREF_BRANCH_HELP,
  PREF_NAME_HELP,
  PREF_TYPE_HELP,
} from "experimenter/components/constants";
import DesignInput from "experimenter/components/DesignInput";
import { Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Button, Col, Container, Row } from "react-bootstrap";
import { PREF_VALUE_HELP, ROLLOUT_PREF_BRANCH_HELP } from "./constants";

@boundClass
class Pref extends React.PureComponent {
  static propTypes = {
    preference: PropTypes.instanceOf(Map),
    numOfPreferences: PropTypes.number,
    errors: PropTypes.instanceOf(Map),
    index: PropTypes.number,
    onChange: PropTypes.func,
    remove: PropTypes.func,
    variantIndex: PropTypes.number,
    rolloutType: PropTypes.string,
  };

  handlePrefValueChange(key, value) {
    const { onChange, preference } = this.props;
    onChange(preference.set(key, value));
  }

  renderTitle() {
    return <h4>Pref {this.props.index + 1}</h4>;
  }

  renderRemoveButton() {
    const { index, numOfPreferences } = this.props;
    if (!(numOfPreferences == 1 && index == 0)) {
      return (
        <Button
          variant="outline-danger"
          onClick={() => {
            this.props.remove(index);
          }}
          data-testid={`remove-pref-${this.props.variantIndex}-${this.props.index}`}
        >
          <span className="fas fa-times" /> Remove Pref
        </Button>
      );
    }
  }
  renderPrefBranchInput() {
    if (this.props.rolloutType) {
      return (
        <DesignInput
          label="Pref Branch"
          name="pref_branch"
          id={`pref-branch-${this.props.variantIndex}-${this.props.index}`}
          helpContent={ROLLOUT_PREF_BRANCH_HELP}
          note="*Note: Pref Rollouts always use the Default Pref Branch"
          labelColumnWidth={5}
          as="select"
          value={"default"}
        >
          <option>default</option>
          <option disabled>user</option>
        </DesignInput>
      );
    }
    return (
      <DesignInput
        label="Pref Branch"
        name="pref_branch"
        id={`pref-branch-${this.props.variantIndex}-${this.props.index}`}
        onChange={(value) => {
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
        labelColumnWidth={5}
      >
        <option>Firefox Pref Branch</option>
        <option>default</option>
        <option>user</option>
      </DesignInput>
    );
  }

  renderPrefBranch() {
    return (
      <Container>
        <Row>
          <Col lg={4}>{this.renderPrefBranchInput()}</Col>
          <Col lg={8}>
            <DesignInput
              label="Pref Name"
              name="pref_name"
              id={`pref-key-${this.props.variantIndex}-${this.props.index}`}
              onChange={(value) => {
                this.handlePrefValueChange("pref_name", value);
              }}
              value={
                this.props.preference
                  ? this.props.preference.get("pref_name")
                  : null
              }
              error={this.props.errors.get("pref_name", null)}
              helpContent={PREF_NAME_HELP}
              labelColumnWidth={2}
            />
          </Col>
        </Row>
        <Row>
          <Col lg={4}>
            <DesignInput
              label="Pref Type"
              name="pref_type"
              id={`pref-type-${this.props.variantIndex}-${this.props.index}`}
              onChange={(value) => {
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
              labelColumnWidth={5}
            >
              <option>Firefox Pref Type</option>
              <option>boolean</option>
              <option>integer</option>
              <option>string</option>
              <option>json string</option>
            </DesignInput>
          </Col>
          <Col lg={8}>
            <DesignInput
              label="Pref Value"
              name="pref_value"
              id={`pref-value-${this.props.variantIndex}-${this.props.index}`}
              onChange={(value) => {
                this.handlePrefValueChange("pref_value", value);
              }}
              value={
                this.props.preference
                  ? this.props.preference.get("pref_value")
                  : null
              }
              error={this.props.errors.get("pref_value", null)}
              helpContent={PREF_VALUE_HELP}
              labelColumnWidth={2}
            />
          </Col>
        </Row>
      </Container>
    );
  }
  render() {
    return (
      <div key={this.props.index} id="control-branch-group-pref">
        <Row className="mb-3">
          <Col md={{ span: 5, offset: 1 }}>{this.renderTitle()}</Col>
          <Col md={6} className="text-right">
            {this.renderRemoveButton()}
          </Col>
        </Row>
        {this.renderPrefBranch()}
        <hr />
      </div>
    );
  }
}
export default Pref;

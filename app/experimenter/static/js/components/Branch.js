import PropTypes from "prop-types";
import React from "react";
import { Button, Row, Col } from "react-bootstrap";
import { Map } from "immutable";
import { boundClass } from "autobind-decorator";

import DesignInput from "experimenter/components/DesignInput";

@boundClass
class Branch extends React.PureComponent {
  static propTypes = {
    branch: PropTypes.instanceOf(Map),
    branchFieldsComponent: PropTypes.func,
    errors: PropTypes.instanceOf(Map),
    index: PropTypes.number,
    onChange: PropTypes.func,
    onErrorChange: PropTypes.func,
    remove: PropTypes.func,
    options: PropTypes.object,
  };

  handleBranchFieldChange(key, value) {
    const { onChange, branch } = this.props;
    onChange(branch.set(key, value));
  }
  handleErrorBranchFieldChange(key, value) {
    const { onErrorChange, errors } = this.props;
    onErrorChange(errors.set(key, value));
  }

  renderTitle() {
    const { branch, index } = this.props;
    if (branch.get("is_control")) {
      return <h4>Control Branch</h4>;
    }
    return <h4>Branch {index}</h4>;
  }

  renderField(name, label, value, error, help, as, rows) {
    return (
      <DesignInput
        as={as || "input"}
        rows={rows}
        label={label}
        dataTestId={label}
        name={`variants[${this.props.index}][${name}]`}
        id={`variants-${this.props.index}-${name}`}
        value={value}
        onChange={(value) => {
          this.handleBranchFieldChange(name, value);
        }}
        error={error}
        helpContent={help}
        labelColumnWidth={2}
      />
    );
  }

  renderRemoveButton() {
    const { branch, index } = this.props;
    if (branch.get("is_control")) {
      return null;
    }
    return (
      <Button
        variant="danger"
        onClick={() => {
          this.props.remove(index);
        }}
        id="remove-branch-button"
      >
        <span className="fas fa-times" /> Remove Branch
      </Button>
    );
  }

  render() {
    const BranchFields = this.props.branchFieldsComponent;

    return (
      <div
        key={this.props.index}
        id="control-branch-group"
        data-testid={"branch" + this.props.index}
      >
        <Row className="mb-3">
          <Col md={{ span: 4, offset: 2 }}>{this.renderTitle()}</Col>
          <Col md={6} className="text-right">
            {this.renderRemoveButton()}
          </Col>
        </Row>

        <BranchFields
          branch={this.props.branch}
          errors={this.props.errors}
          onChange={this.handleBranchFieldChange}
          onErrorChange={this.handleErrorBranchFieldChange}
          index={this.props.index}
          renderField={this.renderField}
          options={this.props.options}
        />

        <hr className="heavy-line my-5" />
      </div>
    );
  }
}

export default Branch;

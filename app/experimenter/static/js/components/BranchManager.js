import { boundClass } from "autobind-decorator";
import { fromJS, List, Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Row, Col, Button } from "react-bootstrap";

import Branch from "experimenter/components/Branch";

@boundClass
class BranchManager extends React.PureComponent {
  static propTypes = {
    branchFieldsComponent: PropTypes.func,
    branches: PropTypes.instanceOf(List),
    errors: PropTypes.instanceOf(List),
    handleDataChange: PropTypes.func,
    handleErrorsChange: PropTypes.func,
  };

  handleChange(index, value) {
    const { branches, handleDataChange } = this.props;
    handleDataChange("variants", branches.set(index, value));
  }

  addBranch() {
    const {
      branches,
      errors,
      handleDataChange,
      handleErrorsChange,
    } = this.props;
    handleDataChange("variants", branches.push(fromJS({is_control: false})));
    handleErrorsChange("variants", errors.push(fromJS({})));
  }

  removeBranch(index) {
    const {
      branches,
      errors,
      handleDataChange,
      handleErrorsChange,
    } = this.props;
    handleDataChange("variants", branches.delete(index));
    handleErrorsChange("variants", errors.delete(index));
  }

  renderBranch(branch, index) {
    const { branchFieldsComponent, errors } = this.props;

    return (
      <Branch
        key={index}
        index={index}
        branch={branch}
        branchFieldsComponent={branchFieldsComponent}
        remove={index => {
          this.removeBranch(index);
        }}
        errors={errors.get(index, new Map())}
        onChange={value => {
          this.handleChange(index, value);
        }}
      />
    );
  }

  render() {
    const { branches } = this.props;
    return (
      <React.Fragment>
        {branches.map((b, i) => this.renderBranch(b, i))}
        <Row>
          <Col className="text-right">
            <Button
              id="add-branch-button"
              variant="success"
              className="mb-4"
              onClick={this.addBranch}
            >
              <span className="fas fa-plus" /> Add Branch
            </Button>
          </Col>
        </Row>
      </React.Fragment>
    );
  }
}
export default BranchManager;

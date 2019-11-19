import { boundClass } from "autobind-decorator";
import { List, Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Row, Col, Button } from "react-bootstrap";

import Branch from "experimenter/components/Branch";

@boundClass
class BranchManager extends React.PureComponent {
  static propTypes = {
    branches: PropTypes.instanceOf(List),
    branchFieldsComponent: PropTypes.func,
    errors: PropTypes.instanceOf(Map),
    onAddBranch: PropTypes.func,
    onChange: PropTypes.func,
    onRemoveBranch: PropTypes.func,
  };

  handleChange(index, value) {
    const { branches, onChange } = this.props;
    onChange(branches.set(index, value));
  }

  renderBranch(branch, index) {
    const { branchFieldsComponent, errors, onRemoveBranch } = this.props;

    return (
      <Branch
        key={index}
        index={index}
        branch={branch}
        branchFieldsComponent={branchFieldsComponent}
        remove={onRemoveBranch}
        errors={errors}
        onChange={value => {
          this.handleChange(index, value);
        }}
      />
    );
  }

  render() {
    const { onAddBranch, branches } = this.props;
    const controlBranch = branches.filter(b => b.get("is_control")).get(0);
    const treatmentBranches = branches.filter(b => !b.get("is_control"));

    return (
      <React.Fragment>
        {this.renderBranch(controlBranch, 0)}
        {treatmentBranches.map((b, i) => this.renderBranch(b, i + 1))}
        <Row>
          <Col className="text-right">
            <Button
              id="add-branch-button"
              variant="success"
              className="mb-4"
              onClick={onAddBranch}
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

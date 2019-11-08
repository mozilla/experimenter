import React from "react";
import { Row, Col, Button } from "react-bootstrap";
import { boundClass } from "autobind-decorator";
import PropTypes from "prop-types";

import Branch from "experimenter/components/Branch";

@boundClass
class BranchManager extends React.PureComponent {
  handleChange(index, value) {
    const branches = [...this.props.branches];
    branches.splice(index, 1, value);
    this.props.onChange(branches);
  }

  render() {
    const { branches, onAddBranch, onRemoveBranch } = this.props;

    // Make sure the control branch is the first branch
    const sortedBranches = [
      ...branches.filter(b => b.is_control),
      ...branches.filter(b => !b.is_control)
    ];

    return (
      <React.Fragment>
        {sortedBranches.map((variant, index) => (
          <React.Fragment key={index}>
            <Branch
              index={index}
              branch={variant}
              branchFieldsComponent={this.props.branchFieldsComponent}
              remove={onRemoveBranch}
              errors={this.props.errors}
              onChange={value => {
                this.handleChange(index, value);
              }}
            />
          </React.Fragment>
        ))}
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

BranchManager.propTypes = {
  data: PropTypes.object,
  errors: PropTypes.object,
  onAddBranch: PropTypes.func,
  onRemoveBranch: PropTypes.func,
  onChange: PropTypes.func,
  branchFieldsComponent: PropTypes.func,
  branches: PropTypes.array
};

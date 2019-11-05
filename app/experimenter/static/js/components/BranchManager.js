import React from "react";
import { Row, Col, Button } from "react-bootstrap";

export default class BranchManager extends React.Component {

  render() {
    const {onAddBranch, onRemoveBranch} = this.props;
    const BranchComponent = this.props.branchComponent;
    return (
      <div>
        {this.props.variants.map((variant, index) => (
          <div>
            <BranchComponent
              values={variant}
              id={index}
              type={this.props.type}
              index={index}
              remove={onRemoveBranch}
              errors={this.props.errors}
            />
          </div>
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
      </div>
    );
  }
}

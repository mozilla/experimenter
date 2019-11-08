import { boundClass } from "autobind-decorator";
import React from "react";
import { Button, Row, Col } from "react-bootstrap";
import PropTypes from "prop-types";

@boundClass
class Branch extends React.PureComponent {
  handleChange(key, value) {
    const { onChange, branch } = this.props;
    onChange({
      ...branch,
      is_control: this.props.index === 0,
      [key]: value,
    });
  }

  renderTitle() {
    if (this.props.index === 0) {
      return <h4>Control Branch</h4>;
    }
    return <h4>Branch {this.props.index}</h4>;
  }

  renderRemoveButton() {
    if (this.props.index === 0) {
      return null;
    }
    return (
      <Button
        variant="danger"
        onClick={() => {
          this.props.remove(this.props.index);
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
      <div key={this.props.index} id="control-branch-group">
        <Row className="mb-3">
          <Col md={{ span: 4, offset: 3 }}>{this.renderTitle()}</Col>
          <Col md={5} className="text-right">
            {this.renderRemoveButton()}
          </Col>
        </Row>

        <BranchFields
          handleChange={this.handleChange}
          index={this.props.index}
          branch={this.props.branch}
          errors={this.props.errors}
        />

        <hr className="heavy-line my-5" />
      </div>
    );
  }
}

Branch.propTypes = {
  errors: PropTypes.object,
  index: PropTypes.number,
  onChange: PropTypes.func,
  remove: PropTypes.func,
  branchFieldsComponent: PropTypes.func,
  branch: PropTypes.object,
};

export default Branch;
